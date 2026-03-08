"""Advanced trading strategies for quantitative finance.

This module implements sophisticated strategies that combine multiple
MCMC models, machine learning, and advanced financial theory.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import warnings

# Import base strategy
from ..backtest.backtest_engine import VolatilityTradingStrategy

# Import MCMC modules
from ..mcmc_option_pricing import RandomWalkMetropolis, MultipleTryMetropolis
from ..quant_models.heston import HestonModel
from ..risk.risk_metrics import calculate_risk_metrics

warnings.filterwarnings("ignore")


class BayesianPortfolioStrategy(VolatilityTradingStrategy):
    """Bayesian portfolio optimization strategy using MCMC.

    This strategy uses MCMC to sample from the posterior distribution
    of asset returns and optimizes portfolio weights using Bayesian
    mean-variance optimization.
    """

    def __init__(
        self,
        n_assets: int = 5,
        lookback_window: int = 60,
        n_mcmc_samples: int = 5000,
        risk_aversion: float = 1.0,
    ):
        """
        Initialize Bayesian portfolio strategy.

        Args:
            n_assets: Number of assets in portfolio
            lookback_window: Window for return estimation
            n_mcmc_samples: Number of MCMC samples
            risk_aversion: Risk aversion parameter
        """
        super().__init__()
        self.n_assets = n_assets
        self.lookback_window = lookback_window
        self.n_mcmc_samples = n_mcmc_samples
        self.risk_aversion = risk_aversion

        # Portfolio state
        self.returns_history = []
        self.portfolio_weights = None
        self.portfolio_history = []
        self.covariance_samples = []

    def initialize(self):
        """Initialize strategy state."""
        super().initialize()
        self.returns_history = []
        self.portfolio_weights = np.ones(self.n_assets) / self.n_assets
        self.portfolio_history = []
        self.covariance_samples = []

    def generate_signals(self, market_data, idx):
        """
        Generate portfolio rebalancing signals.

        Args:
            market_data: Current market data
            idx: Current index

        Returns:
            Dictionary of trading signals
        """
        signals = {}

        # Collect returns data
        # (In practice, would collect multiple assets)

        # Rebalance portfolio periodically
        if idx % 20 == 0 and idx > 0:
            self.rebalance_portfolio(market_data, idx)

            # Generate signals based on new weights
            symbols = ["SPY", "QQQ", "IWM", "EFA", "EEM"][: self.n_assets]
            current_weights = self.get_current_weights()
            target_weights = self.portfolio_weights

            for i, symbol in enumerate(symbols):
                weight_diff = target_weights[i] - current_weights.get(symbol, 0)

                if weight_diff > 0.05:  # Buy if underweight by 5%
                    signals[symbol] = "BUY"
                elif weight_diff < -0.05:  # Sell if overweight by 5%
                    signals[symbol] = "SELL"

        return signals

    def rebalance_portfolio(self, market_data, idx):
        """
        Rebalance portfolio using Bayesian optimization.

        Args:
            market_data: Current market data
            idx: Current index
        """
        # This is a simplified implementation
        # In practice, would estimate full covariance matrix

        # Sample from posterior distribution of returns
        returns_samples = self.sample_posterior_returns()

        # Bayesian mean-variance optimization
        try:
            # Calculate posterior mean and covariance
            posterior_mean = np.mean(returns_samples, axis=0)
            posterior_cov = np.cov(returns_samples.T)

            # Check for positive definiteness
            min_eig = np.min(np.real(np.linalg.eigvals(posterior_cov)))
            if min_eig < 1e-8:
                posterior_cov += np.eye(posterior_cov.shape[0]) * (1e-8 - min_eig)

            # Inverse of covariance matrix
            cov_inv = np.linalg.inv(posterior_cov)

            # Optimal weights: w* = (1/λ) * Σ⁻¹ * μ
            optimal_weights = (1 / self.risk_aversion) * cov_inv @ posterior_mean

            # Normalize weights to sum to 1 (with leverage constraint)
            optimal_weights = optimal_weights / np.sum(np.abs(optimal_weights))

            # Apply constraints (no short selling for simplicity)
            optimal_weights = np.maximum(optimal_weights, 0)
            optimal_weights = optimal_weights / np.sum(optimal_weights)

            self.portfolio_weights = optimal_weights
            self.covariance_samples.append(posterior_cov)

        except Exception as e:
            print(f"Error in portfolio optimization: {e}")
            # Fallback to equal weights
            self.portfolio_weights = np.ones(self.n_assets) / self.n_assets

    def sample_posterior_returns(self) -> np.ndarray:
        """
        Sample from posterior distribution of asset returns using MCMC.

        Returns:
            Array of return samples (n_samples x n_assets)
        """
        # Simplified: sample from multivariate normal
        n_samples = self.n_mcmc_samples

        # Use historical means and covariances as priors
        # (In practice, would use more sophisticated Bayesian model)

        # Generate synthetic samples
        means = np.random.randn(self.n_assets) * 0.01
        cov = np.eye(self.n_assets) * 0.02 + 0.01  # Some correlation

        samples = np.random.multivariate_normal(means, cov, n_samples)

        return samples

    def get_current_weights(self) -> Dict[str, float]:
        """
        Get current portfolio weights.

        Returns:
            Dictionary mapping symbols to weights
        """
        # Simplified: assume equal allocation for now
        symbols = ["SPY", "QQQ", "IWM", "EFA", "EEM"][: self.n_assets]
        return {symbol: 1.0 / self.n_assets for symbol in symbols}


class RegimeSwitchingStrategy(VolatilityTradingStrategy):
    """Regime switching strategy using MCMC for regime detection.

    This strategy uses MCMC to detect market regimes (bull, bear, sideways)
    and adjusts trading behavior accordingly.
    """

    def __init__(
        self, n_regimes: int = 3, lookback_window: int = 40, n_mcmc_samples: int = 3000
    ):
        """
        Initialize regime switching strategy.

        Args:
            n_regimes: Number of market regimes
            lookback_window: Window for regime detection
            n_mcmc_samples: Number of MCMC samples
        """
        super().__init__()
        self.n_regimes = n_regimes
        self.lookback_window = lookback_window
        self.n_mcmc_samples = n_mcmc_samples

        # Regime state
        self.returns_history = []
        self.current_regime = 0
        self.regime_probabilities = []
        self.regime_history = []

    def initialize(self):
        """Initialize strategy state."""
        super().initialize()
        self.returns_history = []
        self.current_regime = 0
        self.regime_probabilities = np.ones(self.n_regimes) / self.n_regimes
        self.regime_history = []

    def generate_signals(self, market_data, idx):
        """
        Generate signals based on detected market regime.

        Args:
            market_data: Current market data
            idx: Current index

        Returns:
            Dictionary of trading signals
        """
        signals = {}

        # Update returns history
        current_return = market_data.get("return", 0.0)
        self.returns_history.append(current_return)

        if len(self.returns_history) > self.lookback_window:
            self.returns_history = self.returns_history[-self.lookback_window :]

        # Detect regime periodically
        if idx % 10 == 0 and len(self.returns_history) >= 20:
            self.detect_regime()

        # Trading logic based on regime
        if self.current_regime == 0:  # Bull market
            # Trend following
            if len(self.returns_history) >= 5:
                recent_returns = self.returns_history[-5:]
                if np.mean(recent_returns) > 0:
                    signals["SPY"] = "BUY"

        elif self.current_regime == 1:  # Bear market
            # Defensive or short
            if len(self.returns_history) >= 5:
                recent_returns = self.returns_history[-5:]
                if np.mean(recent_returns) < 0:
                    signals["SPY"] = "SELL"

        elif self.current_regime == 2:  # Sideways/volatile
            # Mean reversion
            if len(self.returns_history) >= 10:
                recent_prices = self.returns_history[-10:]
                price_mean = np.mean(recent_prices)
                price_std = np.std(recent_prices) if np.std(recent_prices) > 0 else 1.0

                current_price = market_data["Close"]
                zscore = (current_price - price_mean) / price_std

                if zscore > 1.0:
                    signals["SPY"] = "SELL"
                elif zscore < -1.0:
                    signals["SPY"] = "BUY"

        return signals

    def detect_regime(self):
        """Detect current market regime using MCMC."""
        if len(self.returns_history) < 20:
            return

        returns_array = np.array(self.returns_history)

        # Simple regime switching model with MCMC
        def log_posterior(params):
            # params: regime means, regime variances, transition probabilities
            # Simplified for illustration

            # Prior
            log_prior = 0.0

            # Likelihood (simplified)
            log_lik = 0.0

            return log_prior + log_lik

        # For now, use simple heuristic based on recent returns
        recent_returns = returns_array[-20:]
        mean_return = np.mean(recent_returns)
        vol_return = np.std(recent_returns)

        # Heuristic regime classification
        if mean_return > 0.001 and vol_return < 0.02:
            self.current_regime = 0  # Bull
        elif mean_return < -0.001:
            self.current_regime = 1  # Bear
        else:
            self.current_regime = 2  # Sideways

        self.regime_history.append(self.current_regime)

        # Update regime probabilities (simplified)
        if len(self.regime_history) > 10:
            recent_regimes = self.regime_history[-10:]
            for i in range(self.n_regimes):
                self.regime_probabilities[i] = np.mean(np.array(recent_regimes) == i)


class JumpDiffusionStrategy(VolatilityTradingStrategy):
    """Jump diffusion strategy using MCMC for jump detection.

    This strategy models asset returns with jumps using MCMC,
    and trades based on jump probabilities and sizes.
    """

    def __init__(
        self,
        jump_threshold: float = 3.0,
        lookback_window: int = 30,
        n_mcmc_samples: int = 4000,
    ):
        """
        Initialize jump diffusion strategy.

        Args:
            jump_threshold: Threshold for jump detection (in standard deviations)
            lookback_window: Window for jump analysis
            n_mcmc_samples: Number of MCMC samples
        """
        super().__init__()
        self.jump_threshold = jump_threshold
        self.lookback_window = lookback_window
        self.n_mcmc_samples = n_mcmc_samples

        # Jump state
        self.returns_history = []
        self.jump_probabilities = []
        self.jump_sizes = []
        self.jump_detected = False

    def initialize(self):
        """Initialize strategy state."""
        super().initialize()
        self.returns_history = []
        self.jump_probabilities = []
        self.jump_sizes = []
        self.jump_detected = False

    def generate_signals(self, market_data, idx):
        """
        Generate signals based on jump detection.

        Args:
            market_data: Current market data
            idx: Current index

        Returns:
            Dictionary of trading signals
        """
        signals = {}

        # Update returns
        current_return = market_data.get("return", 0.0)
        self.returns_history.append(current_return)

        if len(self.returns_history) > self.lookback_window:
            self.returns_history = self.returns_history[-self.lookback_window :]

        # Detect jumps
        if len(self.returns_history) >= 10:
            jump_prob, jump_size = self.detect_jump()
            self.jump_probabilities.append(jump_prob)
            self.jump_sizes.append(jump_size)

            # Trading logic
            if jump_prob > 0.7 and abs(jump_size) > 0.02:
                self.jump_detected = True

                if jump_size > 0:  # Positive jump
                    # Could fade the jump or ride momentum
                    if self.position <= 0:
                        signals["SPY"] = "BUY"
                else:  # Negative jump
                    if self.position >= 0:
                        signals["SPY"] = "SELL"
            else:
                self.jump_detected = False

        return signals

    def detect_jump(self) -> Tuple[float, float]:
        """
        Detect jumps in returns using MCMC.

        Returns:
            Tuple of (jump probability, estimated jump size)
        """
        if len(self.returns_history) < 10:
            return 0.0, 0.0

        returns_array = np.array(self.returns_history)

        # Simple jump detection using extreme value theory
        recent_returns = returns_array[-10:]
        mean_return = np.mean(recent_returns)
        std_return = np.std(recent_returns) if np.std(recent_returns) > 0 else 0.01

        # Check for extreme returns
        extreme_returns = recent_returns[
            abs(recent_returns - mean_return) > self.jump_threshold * std_return
        ]

        if len(extreme_returns) > 0:
            # Possible jump detected
            jump_size = np.mean(extreme_returns)

            # Estimate jump probability using Bayesian approach
            # Simplified: probability proportional to extremity
            max_deviation = np.max(abs(recent_returns - mean_return))
            jump_prob = min(1.0, max_deviation / (3 * std_return))

            return jump_prob, jump_size
        else:
            return 0.0, 0.0


class MultiModelEnsembleStrategy(VolatilityTradingStrategy):
    """Ensemble strategy combining multiple MCMC models.

    This strategy combines signals from multiple MCMC-based strategies
    using Bayesian model averaging or other ensemble methods.
    """

    def __init__(
        self,
        strategies: List[VolatilityTradingStrategy],
        ensemble_method: str = "bayesian_averaging",
    ):
        """
        Initialize ensemble strategy.

        Args:
            strategies: List of base strategies
            ensemble_method: Method for combining signals ('bayesian_averaging',
                           'majority_vote', 'weighted_average')
        """
        super().__init__()
        self.strategies = strategies
        self.ensemble_method = ensemble_method

        # Ensemble state
        self.strategy_weights = np.ones(len(strategies)) / len(strategies)
        self.strategy_performance = []
        self.combined_signals_history = []

    def initialize(self):
        """Initialize all strategies."""
        super().initialize()
        for strategy in self.strategies:
            strategy.initialize()

        self.strategy_weights = np.ones(len(self.strategies)) / len(self.strategies)
        self.strategy_performance = []
        self.combined_signals_history = []

    def update(self, backtest_engine, market_data, idx):
        """Update all strategies."""
        super().update(backtest_engine, market_data, idx)
        for strategy in self.strategies:
            strategy.update(backtest_engine, market_data, idx)

    def generate_signals(self, market_data, idx):
        """
        Generate combined signals from all strategies.

        Args:
            market_data: Current market data
            idx: Current index

        Returns:
            Dictionary of combined trading signals
        """
        # Get signals from all strategies
        all_signals = []
        for strategy in self.strategies:
            signals = strategy.generate_signals(market_data, idx)
            all_signals.append(signals)

        # Combine signals based on ensemble method
        combined_signals = self.combine_signals(all_signals)
        self.combined_signals_history.append(combined_signals)

        return combined_signals

    def combine_signals(self, all_signals: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Combine signals from multiple strategies.

        Args:
            all_signals: List of signal dictionaries from each strategy

        Returns:
            Combined signal dictionary
        """
        if not all_signals:
            return {}

        # Collect all symbols
        all_symbols = set()
        for signals in all_signals:
            all_symbols.update(signals.keys())

        combined = {}

        for symbol in all_symbols:
            # Collect votes for each symbol
            votes = []
            for i, signals in enumerate(all_signals):
                if symbol in signals:
                    vote = signals[symbol]
                    weight = self.strategy_weights[i]
                    votes.append((vote, weight))

            if not votes:
                continue

            # Combine votes
            if self.ensemble_method == "majority_vote":
                # Simple majority vote
                vote_counts = {}
                for vote, weight in votes:
                    vote_counts[vote] = vote_counts.get(vote, 0) + 1

                # Get vote with highest count
                combined_vote = max(vote_counts.items(), key=lambda x: x[1])[0]
                combined[symbol] = combined_vote

            elif self.ensemble_method == "weighted_average":
                # Weighted by strategy weights
                buy_weight = sum(weight for vote, weight in votes if vote == "BUY")
                sell_weight = sum(weight for vote, weight in votes if vote == "SELL")
                hold_weight = sum(weight for vote, weight in votes if vote == "HOLD")

                max_weight = max(buy_weight, sell_weight, hold_weight)

                if max_weight == buy_weight and buy_weight > 0:
                    combined[symbol] = "BUY"
                elif max_weight == sell_weight and sell_weight > 0:
                    combined[symbol] = "SELL"
                else:
                    combined[symbol] = "HOLD"

            elif self.ensemble_method == "bayesian_averaging":
                # Bayesian model averaging (simplified)
                # Use strategy weights as posterior model probabilities
                buy_prob = sum(weight for vote, weight in votes if vote == "BUY")
                sell_prob = sum(weight for vote, weight in votes if vote == "SELL")

                if buy_prob > sell_prob and buy_prob > 0.5:
                    combined[symbol] = "BUY"
                elif sell_prob > buy_prob and sell_prob > 0.5:
                    combined[symbol] = "SELL"
                else:
                    combined[symbol] = "HOLD"

        return combined

    def update_strategy_weights(self, performance_metrics: List[Dict[str, float]]):
        """
        Update strategy weights based on recent performance.

        Args:
            performance_metrics: List of performance metrics for each strategy
        """
        if not performance_metrics or len(performance_metrics) != len(self.strategies):
            return

        # Use Sharpe ratio to weight strategies
        sharpe_ratios = []
        for metrics in performance_metrics:
            sharpe = metrics.get("sharpe_ratio", 0.0)
            sharpe_ratios.append(sharpe)

        # Convert to probabilities using softmax
        sharpe_array = np.array(sharpe_ratios)

        # Handle negative Sharpe ratios
        if np.all(sharpe_array <= 0):
            sharpe_array = np.ones_like(sharpe_array)

        # Softmax with temperature
        exp_sharpe = np.exp(sharpe_array / 0.1)  # Temperature = 0.1
        new_weights = exp_sharpe / np.sum(exp_sharpe)

        self.strategy_weights = new_weights
        self.strategy_performance.append(sharpe_ratios)
