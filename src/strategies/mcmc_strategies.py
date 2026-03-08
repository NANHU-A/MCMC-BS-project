"""MCMC-based trading strategies for quantitative finance.

This module implements strategies that leverage Markov Chain Monte Carlo methods
for parameter estimation, volatility forecasting, and statistical arbitrage.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import warnings

# Import existing MCMC modules
from ..mcmc_option_pricing import (
    RandomWalkMetropolis,
    MultipleTryMetropolis,
    BlackScholesModel,
)
from ..mcmc_optimized import AdaptiveMetropolis
from ..quant_models.heston import HestonModel

# Import backtest base class
from ..backtest.backtest_engine import VolatilityTradingStrategy

warnings.filterwarnings("ignore")


class MCMCVolatilityForecastingStrategy(VolatilityTradingStrategy):
    """Volatility forecasting strategy using MCMC for parameter estimation.

    This strategy uses MCMC to estimate volatility parameters from historical data,
    then trades based on volatility forecasts and mean reversion.
    """

    def __init__(
        self,
        lookback_window: int = 20,
        forecast_horizon: int = 5,
        confidence_level: float = 0.95,
        n_mcmc_samples: int = 5000,
        burn_in: int = 1000,
    ):
        """
        Initialize MCMC volatility forecasting strategy.

        Args:
            lookback_window: Number of days for historical estimation
            forecast_horizon: Forecast horizon in days
            confidence_level: Confidence level for prediction intervals
            n_mcmc_samples: Number of MCMC samples for parameter estimation
            burn_in: Burn-in period for MCMC
        """
        super().__init__()
        self.lookback_window = lookback_window
        self.forecast_horizon = forecast_horizon
        self.confidence_level = confidence_level
        self.n_mcmc_samples = n_mcmc_samples
        self.burn_in = burn_in

        # State variables
        self.returns_history = []
        self.volatility_estimates = []
        self.volatility_forecasts = []
        self.mcmc_samples = None

    def initialize(self):
        """Initialize strategy state."""
        super().initialize()
        self.returns_history = []
        self.volatility_estimates = []
        self.volatility_forecasts = []
        self.mcmc_samples = None

    def update(self, backtest_engine, market_data, idx):
        """
        Update strategy state with new market data.

        Args:
            backtest_engine: Backtest engine instance
            market_data: Current market data
            idx: Current index
        """
        # Calculate return
        if len(self.returns_history) > 0:
            prev_price = (
                self.returns_history[-1][1]
                if isinstance(self.returns_history[-1], tuple)
                else self.returns_history[-1]
            )
            current_price = market_data["Close"]
            returns = (current_price - prev_price) / prev_price
        else:
            returns = 0.0

        # Store price and return
        self.returns_history.append((market_data["Close"], returns))

        # Keep only lookback_window
        if len(self.returns_history) > self.lookback_window:
            self.returns_history = self.returns_history[-self.lookback_window :]

    def generate_signals(self, market_data, idx):
        """
        Generate trading signals based on MCMC volatility forecasts.

        Args:
            market_data: Current market data
            idx: Current index

        Returns:
            Dictionary of trading signals
        """
        signals = {}

        # Need enough data for estimation
        if len(self.returns_history) < self.lookback_window // 2:
            return signals

        # Extract returns for estimation
        returns = [r for _, r in self.returns_history]
        prices = [p for p, _ in self.returns_history]

        # Estimate volatility using MCMC
        current_vol = self.estimate_volatility_mcmc(returns)
        self.volatility_estimates.append(current_vol)

        # Generate volatility forecast
        vol_forecast = self.forecast_volatility(returns, current_vol)
        self.volatility_forecasts.append(vol_forecast)

        # Get current price
        current_price = market_data["Close"]

        # Calculate volatility z-score (current vs historical)
        if len(self.volatility_estimates) > 10:
            vol_mean = np.mean(self.volatility_estimates[-10:])
            vol_std = np.std(self.volatility_estimates[-10:])

            if vol_std > 0:
                vol_zscore = (current_vol - vol_mean) / vol_std

                # Trading logic based on volatility regimes
                if vol_zscore > 1.5 and self.position <= 0:
                    # High volatility regime - consider short or hedge
                    signals["SPY"] = "SELL" if self.position == 0 else "HOLD"
                elif vol_zscore < -1.5 and self.position >= 0:
                    # Low volatility regime - consider long
                    signals["SPY"] = "BUY" if self.position == 0 else "HOLD"

        # Mean reversion on price if we have enough price history
        if len(prices) >= self.lookback_window:
            recent_prices = prices[-self.lookback_window :]
            price_mean = np.mean(recent_prices)
            price_std = np.std(recent_prices)

            if price_std > 0:
                price_zscore = (current_price - price_mean) / price_std

                # Combine volatility and price signals
                if abs(price_zscore) > 2.0:
                    if price_zscore > 2.0 and "SPY" not in signals:
                        signals["SPY"] = "SELL"
                    elif price_zscore < -2.0 and "SPY" not in signals:
                        signals["SPY"] = "BUY"

        return signals

    def estimate_volatility_mcmc(self, returns: List[float]) -> float:
        """
        Estimate volatility using MCMC.

        Args:
            returns: List of returns

        Returns:
            Estimated volatility (annualized)
        """
        # Convert to numpy array
        returns_array = np.array(returns)

        # Simple Bayesian model: returns ~ N(0, sigma^2)
        # Prior: sigma ~ InverseGamma(alpha, beta)

        # Use Random Walk Metropolis to sample sigma
        def log_posterior(log_sigma):
            sigma = np.exp(log_sigma)
            # Log likelihood
            log_lik = (
                -0.5 * len(returns_array) * np.log(2 * np.pi * sigma**2)
                - 0.5 * np.sum(returns_array**2) / sigma**2
            )
            # Log prior (Jeffreys prior: 1/sigma)
            log_prior = -np.log(sigma)
            return log_lik + log_prior

        # Initialize MCMC
        if len(returns_array) < 10:
            # Fallback to simple estimator
            return np.std(returns_array) * np.sqrt(252)

        # Use Adaptive Metropolis if available
        try:
            mcmc = AdaptiveMetropolis(log_posterior)
            samples = mcmc.sample(self.n_mcmc_samples, burn_in=self.burn_in)
        except:
            # Fallback to Random Walk Metropolis
            mcmc = RandomWalkMetropolis(log_posterior, proposal_std=0.5)
            samples = mcmc.sample(self.n_mcmc_samples, burn_in=self.burn_in)

        # Convert from log-space to sigma
        sigma_samples = np.exp(samples)

        # Store samples for analysis
        self.mcmc_samples = sigma_samples

        # Use median as point estimate
        sigma_estimate = np.median(sigma_samples)

        # Annualize
        sigma_annualized = sigma_estimate * np.sqrt(252)

        return sigma_annualized

    def forecast_volatility(
        self, returns: List[float], current_vol: float
    ) -> Dict[str, float]:
        """
        Forecast volatility using GARCH-like model with MCMC.

        Args:
            returns: Historical returns
            current_vol: Current volatility estimate

        Returns:
            Dictionary with forecast statistics
        """
        # Simple forecasting: mean reversion in volatility
        returns_array = np.array(returns)

        if len(returns_array) < 20:
            return {
                "point_forecast": current_vol,
                "lower_bound": current_vol * 0.8,
                "upper_bound": current_vol * 1.2,
            }

        # Fit simple GARCH(1,1) parameters using MCMC
        def garch_log_likelihood(params):
            omega, alpha, beta = params
            n = len(returns_array)
            sigma2 = np.zeros(n)

            # Initialize with unconditional variance
            unconditional_var = (
                omega / (1 - alpha - beta)
                if (alpha + beta) < 1
                else np.var(returns_array)
            )
            sigma2[0] = unconditional_var

            for t in range(1, n):
                sigma2[t] = (
                    omega + alpha * returns_array[t - 1] ** 2 + beta * sigma2[t - 1]
                )

            # Log likelihood
            log_lik = -0.5 * np.sum(
                np.log(2 * np.pi * sigma2) + returns_array**2 / sigma2
            )

            # Priors
            log_prior = -np.log(omega) - np.log(alpha) - np.log(beta)  # Improper priors

            return log_lik + log_prior

        # Simple point estimates (could be extended to full MCMC)
        omega = 0.01
        alpha = 0.1
        beta = 0.85

        # Forecast volatility
        forecast = omega + (alpha + beta) * current_vol**2

        return {
            "point_forecast": np.sqrt(forecast),
            "lower_bound": np.sqrt(forecast) * 0.9,
            "upper_bound": np.sqrt(forecast) * 1.1,
        }


class HestonCalibrationStrategy(VolatilityTradingStrategy):
    """Trading strategy based on Heston model calibration using MCMC.

    This strategy calibrates Heston model parameters to market data using MCMC,
    then trades based on model-implied volatility versus realized volatility.
    """

    def __init__(
        self,
        calibration_window: int = 60,
        n_mcmc_samples: int = 3000,
        burn_in: int = 1000,
    ):
        """
        Initialize Heston calibration strategy.

        Args:
            calibration_window: Window for model calibration
            n_mcmc_samples: Number of MCMC samples
            burn_in: Burn-in period
        """
        super().__init__()
        self.calibration_window = calibration_window
        self.n_mcmc_samples = n_mcmc_samples
        self.burn_in = burn_in

        # Model state
        self.heston_model = None
        self.calibrated_params = None
        self.calibration_history = []
        self.volatility_spread_history = []

    def initialize(self):
        """Initialize strategy state."""
        super().initialize()
        self.heston_model = None
        self.calibrated_params = None
        self.calibration_history = []
        self.volatility_spread_history = []

    def update(self, backtest_engine, market_data, idx):
        """
        Update strategy with new market data.

        Args:
            backtest_engine: Backtest engine
            market_data: Current market data
            idx: Current index
        """
        # Calibrate Heston model periodically
        if idx % self.calibration_window == 0 and idx > 0:
            self.calibrate_heston(backtest_engine, market_data, idx)

    def generate_signals(self, market_data, idx):
        """
        Generate signals based on Heston model calibration.

        Args:
            market_data: Current market data
            idx: Current index

        Returns:
            Dictionary of trading signals
        """
        signals = {}

        # Need calibrated model
        if self.heston_model is None or self.calibrated_params is None:
            return signals

        # Extract current market data
        current_price = market_data["Close"]
        realized_vol = market_data.get("realized_volatility", 0.2)

        # Calculate Heston implied volatility
        try:
            # Use current parameters to price at-the-money option
            heston_vol = self.heston_model.calculate_volatility_smile(
                current_price, current_price, 0.08, self.calibrated_params
            )[0]  # ATM volatility

            # Volatility spread (model vs realized)
            vol_spread = heston_vol - realized_vol
            self.volatility_spread_history.append(vol_spread)

            # Trading logic: if model predicts higher vol than realized, buy volatility
            if len(self.volatility_spread_history) > 5:
                spread_mean = np.mean(self.volatility_spread_history[-5:])
                spread_std = np.std(self.volatility_spread_history[-5:])

                if spread_std > 0:
                    spread_zscore = vol_spread / spread_std

                    # Trade VIX or options based on spread
                    if spread_zscore > 1.5:
                        # Model predicts higher vol than realized - buy volatility
                        signals["VIX"] = "BUY"
                    elif spread_zscore < -1.5:
                        # Model predicts lower vol than realized - sell volatility
                        signals["VIX"] = "SELL"

        except Exception as e:
            print(f"Error in Heston signal generation: {e}")

        return signals

    def calibrate_heston(self, backtest_engine, market_data, idx):
        """
        Calibrate Heston model to historical data using MCMC.

        Args:
            backtest_engine: Backtest engine
            market_data: Current market data
            idx: Current index
        """
        # This is a placeholder - actual calibration would use option prices
        # For simplicity, we'll use synthetic parameters

        # Initialize Heston model with reasonable parameters
        self.heston_model = HestonModel(
            s0=market_data["Close"],
            v0=0.04,  # initial variance
            kappa=1.5,  # mean reversion speed
            theta=0.04,  # long-term variance
            sigma=0.3,  # vol of vol
            rho=-0.7,  # correlation
            risk_free_rate=0.02,
        )

        # Store "calibrated" parameters
        self.calibrated_params = {
            "v0": 0.04,
            "kappa": 1.5,
            "theta": 0.04,
            "sigma": 0.3,
            "rho": -0.7,
        }

        self.calibration_history.append((idx, self.calibrated_params))

        print(f"Heston model calibrated at index {idx}")


class StatisticalArbitrageStrategy(VolatilityTradingStrategy):
    """Statistical arbitrage strategy using MCMC for pair trading.

    This strategy identifies pairs of assets with cointegrated prices,
    estimates the relationship using MCMC, and trades mean reversion.
    """

    def __init__(
        self,
        lookback_window: int = 60,
        zscore_threshold: float = 2.0,
        n_mcmc_samples: int = 2000,
    ):
        """
        Initialize statistical arbitrage strategy.

        Args:
            lookback_window: Window for cointegration testing
            zscore_threshold: Z-score threshold for trading
            n_mcmc_samples: Number of MCMC samples for parameter estimation
        """
        super().__init__()
        self.lookback_window = lookback_window
        self.zscore_threshold = zscore_threshold
        self.n_mcmc_samples = n_mcmc_samples

        # Pairs trading state
        self.pair_history = []
        self.spread_history = []
        self.coint_params = None
        self.coint_score_history = []

    def initialize(self):
        """Initialize strategy state."""
        super().initialize()
        self.pair_history = []
        self.spread_history = []
        self.coint_params = None
        self.coint_score_history = []

    def generate_signals(self, market_data, idx):
        """
        Generate pairs trading signals.

        Args:
            market_data: Current market data
            idx: Current index

        Returns:
            Dictionary of trading signals
        """
        signals = {}

        # This is a simplified implementation
        # In practice, we would track multiple pairs and select the best

        # Example pair: SPY and IVV (both track S&P 500)
        spy_price = market_data.get("SPY_Close", market_data["Close"])
        ivv_price = market_data.get("IVV_Close", spy_price * 1.001)  # synthetic

        # Store pair prices
        self.pair_history.append((spy_price, ivv_price))

        if len(self.pair_history) > self.lookback_window:
            self.pair_history = self.pair_history[-self.lookback_window :]

            # Estimate cointegration relationship using MCMC
            if self.coint_params is None or idx % 20 == 0:
                self.estimate_cointegration()

            # Calculate spread
            if self.coint_params is not None:
                alpha, beta = self.coint_params
                spread = spy_price - beta * ivv_price - alpha
                self.spread_history.append(spread)

                # Calculate z-score of spread
                if len(self.spread_history) > 10:
                    spread_mean = np.mean(self.spread_history[-10:])
                    spread_std = np.std(self.spread_history[-10:])

                    if spread_std > 0:
                        zscore = (spread - spread_mean) / spread_std

                        # Trading logic
                        if zscore > self.zscore_threshold:
                            # Spread too wide - short SPY, long IVV
                            signals["SPY"] = "SELL"
                            signals["IVV"] = "BUY"
                        elif zscore < -self.zscore_threshold:
                            # Spread too narrow - long SPY, short IVV
                            signals["SPY"] = "BUY"
                            signals["IVV"] = "SELL"

        return signals

    def estimate_cointegration(self):
        """Estimate cointegration relationship using MCMC."""
        if len(self.pair_history) < 20:
            return

        # Extract prices
        spy_prices = [p[0] for p in self.pair_history]
        ivv_prices = [p[1] for p in self.pair_history]

        # Bayesian linear regression: spy = alpha + beta * ivv + epsilon
        def log_posterior(params):
            alpha, beta, log_sigma = params
            sigma = np.exp(log_sigma)

            # Predicted values
            predicted = alpha + beta * np.array(ivv_prices)

            # Log likelihood
            residuals = np.array(spy_prices) - predicted
            log_lik = (
                -0.5 * len(residuals) * np.log(2 * np.pi * sigma**2)
                - 0.5 * np.sum(residuals**2) / sigma**2
            )

            # Priors
            log_prior = -np.log(sigma)  # Jeffreys prior for sigma

            return log_lik + log_prior

        # Use MCMC to sample parameters
        try:
            mcmc = AdaptiveMetropolis(log_posterior)
            samples = mcmc.sample(self.n_mcmc_samples, burn_in=500)

            # Use posterior means
            alpha_samples = samples[:, 0]
            beta_samples = samples[:, 1]

            self.coint_params = (np.mean(alpha_samples), np.mean(beta_samples))

            # Calculate cointegration score (R-squared)
            predicted = self.coint_params[0] + self.coint_params[1] * np.array(
                ivv_prices
            )
            ss_res = np.sum((np.array(spy_prices) - predicted) ** 2)
            ss_tot = np.sum((np.array(spy_prices) - np.mean(spy_prices)) ** 2)
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

            self.coint_score_history.append(r2)

        except Exception as e:
            print(f"Error in cointegration estimation: {e}")


class OptionMarketMakingStrategy(VolatilityTradingStrategy):
    """Option market making strategy using MCMC for volatility surface modeling.

    This strategy uses MCMC to model the volatility surface and makes markets
    in options by quoting bid-ask spreads based on model uncertainty.
    """

    def __init__(self, volatility_surface_window: int = 30, n_mcmc_samples: int = 1000):
        """
        Initialize option market making strategy.

        Args:
            volatility_surface_window: Window for volatility surface estimation
            n_mcmc_samples: Number of MCMC samples
        """
        super().__init__()
        self.volatility_surface_window = volatility_surface_window
        self.n_mcmc_samples = n_mcmc_samples

        # Market making state
        self.vol_surface_history = []
        self.option_inventory = {}
        self.quotes_history = []

    def generate_signals(self, market_data, idx):
        """
        Generate option market making signals.

        Args:
            market_data: Current market data
            idx: Current index

        Returns:
            Dictionary of trading signals (option quotes)
        """
        signals = {}

        # This is a simplified implementation
        # In practice, we would manage a full option portfolio

        # Example: quote ATM options
        current_price = market_data["Close"]
        realized_vol = market_data.get("realized_volatility", 0.2)

        # Use MCMC to estimate volatility surface parameters
        vol_estimate = self.estimate_volatility_surface(current_price, realized_vol)

        # Generate quotes for call and put options
        strike_atm = current_price
        strike_otm_call = current_price * 1.05
        strike_otm_put = current_price * 0.95

        # Calculate bid-ask spreads based on MCMC uncertainty
        call_bid = self.calculate_option_price(
            current_price, strike_atm, 0.08, vol_estimate * 0.95, "call"
        )
        call_ask = self.calculate_option_price(
            current_price, strike_atm, 0.08, vol_estimate * 1.05, "call"
        )

        put_bid = self.calculate_option_price(
            current_price, strike_atm, 0.08, vol_estimate * 0.95, "put"
        )
        put_ask = self.calculate_option_price(
            current_price, strike_atm, 0.08, vol_estimate * 1.05, "put"
        )

        # Store quotes
        self.quotes_history.append(
            {
                "call_bid": call_bid,
                "call_ask": call_ask,
                "put_bid": put_bid,
                "put_ask": put_ask,
            }
        )

        # Generate signals based on inventory management
        # (simplified - in practice, would delta-hedge)

        return signals

    def estimate_volatility_surface(
        self, current_price: float, realized_vol: float
    ) -> float:
        """
        Estimate volatility surface using MCMC.

        Args:
            current_price: Current underlying price
            realized_vol: Realized volatility

        Returns:
            Estimated ATM volatility
        """

        # Simplified: just use realized vol with Bayesian updating
        def log_posterior(log_vol):
            vol = np.exp(log_vol)

            # Prior: vol ~ N(realized_vol, 0.1)
            log_prior = -0.5 * (vol - realized_vol) ** 2 / 0.01

            # Likelihood: option prices observed with noise
            # (simplified - would use actual option prices)
            log_lik = 0.0

            return log_prior + log_lik

        # Sample from posterior
        try:
            mcmc = RandomWalkMetropolis(log_posterior, proposal_std=0.1)
            samples = mcmc.sample(self.n_mcmc_samples, burn_in=200)
            vol_samples = np.exp(samples)

            return np.mean(vol_samples)
        except:
            return realized_vol

    def calculate_option_price(
        self, s: float, k: float, t: float, sigma: float, option_type: str
    ) -> float:
        """
        Calculate option price using Black-Scholes.

        Args:
            s: Underlying price
            k: Strike price
            t: Time to expiration
            sigma: Volatility
            option_type: 'call' or 'put'

        Returns:
            Option price
        """
        from scipy.stats import norm

        d1 = (np.log(s / k) + (0.02 + 0.5 * sigma**2) * t) / (sigma * np.sqrt(t))
        d2 = d1 - sigma * np.sqrt(t)

        if option_type == "call":
            price = s * norm.cdf(d1) - k * np.exp(-0.02 * t) * norm.cdf(d2)
        else:
            price = k * np.exp(-0.02 * t) * norm.cdf(-d2) - s * norm.cdf(-d1)

        return max(price, 0.01)  # Minimum price
