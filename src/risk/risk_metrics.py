"""Risk metrics and calculations for quantitative finance.

This module provides comprehensive risk management tools including:
- Value at Risk (VaR) calculations using historical, parametric, and Monte Carlo methods
- Conditional VaR (CVaR) / Expected Shortfall
- Portfolio risk analytics
- Risk-adjusted performance measures
- Greeks calculation for options
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Union, Tuple, List, Optional, Dict
import warnings


def calculate_var_historical(
    returns: Union[pd.Series, np.ndarray], confidence_level: float = 0.95
) -> float:
    """Calculate Value at Risk using historical simulation.

    Args:
        returns: Series or array of returns
        confidence_level: Confidence level for VaR (e.g., 0.95 for 95%)

    Returns:
        VaR value (negative indicates loss)
    """
    if isinstance(returns, pd.Series):
        returns = returns.values

    if len(returns) == 0:
        raise ValueError("Returns array cannot be empty")

    var = -np.percentile(returns, (1 - confidence_level) * 100)
    return var


def calculate_var_parametric(
    returns: Union[pd.Series, np.ndarray],
    confidence_level: float = 0.95,
    mean: Optional[float] = None,
    std: Optional[float] = None,
) -> float:
    """Calculate Value at Risk using parametric (variance-covariance) method.

    Assumes normal distribution of returns.

    Args:
        returns: Series or array of returns
        confidence_level: Confidence level for VaR
        mean: Optional pre-calculated mean of returns
        std: Optional pre-calculated standard deviation of returns

    Returns:
        VaR value (negative indicates loss)
    """
    if isinstance(returns, pd.Series):
        returns = returns.values

    if len(returns) == 0:
        raise ValueError("Returns array cannot be empty")

    if mean is None:
        mean = np.mean(returns)
    if std is None:
        std = np.std(returns)

    # Z-score for confidence level
    z_score = stats.norm.ppf(1 - confidence_level)

    var = -(mean + z_score * std)
    return var


def calculate_var_monte_carlo(
    returns: Union[pd.Series, np.ndarray],
    confidence_level: float = 0.95,
    n_simulations: int = 10000,
    time_horizon: int = 1,
) -> float:
    """Calculate Value at Risk using Monte Carlo simulation.

    Args:
        returns: Series or array of returns
        confidence_level: Confidence level for VaR
        n_simulations: Number of Monte Carlo simulations
        time_horizon: Time horizon in days

    Returns:
        VaR value (negative indicates loss)
    """
    if isinstance(returns, pd.Series):
        returns = returns.values

    if len(returns) == 0:
        raise ValueError("Returns array cannot be empty")

    mean = np.mean(returns)
    std = np.std(returns)

    # Generate simulated returns
    simulated_returns = np.random.normal(mean, std, (n_simulations, time_horizon))

    # Calculate portfolio values
    portfolio_values = 100 * np.prod(1 + simulated_returns, axis=1)

    # Calculate VaR
    var = 100 - np.percentile(portfolio_values, (1 - confidence_level) * 100)
    return var


def calculate_cvar(
    returns: Union[pd.Series, np.ndarray], confidence_level: float = 0.95
) -> float:
    """Calculate Conditional Value at Risk (Expected Shortfall).

    CVaR is the average loss given that the loss exceeds VaR.

    Args:
        returns: Series or array of returns
        confidence_level: Confidence level for CVaR

    Returns:
        CVaR value (negative indicates loss)
    """
    if isinstance(returns, pd.Series):
        returns = returns.values

    if len(returns) == 0:
        raise ValueError("Returns array cannot be empty")

    var = calculate_var_historical(returns, confidence_level)

    # Calculate average of returns below VaR threshold
    losses = returns[returns < -var]

    if len(losses) == 0:
        # If no losses exceed VaR, return VaR
        return var

    cvar = -np.mean(losses)
    return cvar


def calculate_portfolio_var(
    weights: np.ndarray,
    covariance_matrix: np.ndarray,
    portfolio_value: float,
    confidence_level: float = 0.95,
) -> float:
    """Calculate portfolio VaR using parametric method.

    Args:
        weights: Portfolio weights (should sum to 1)
        covariance_matrix: Covariance matrix of asset returns
        portfolio_value: Total portfolio value
        confidence_level: Confidence level for VaR

    Returns:
        Portfolio VaR in value terms
    """
    # Calculate portfolio variance
    portfolio_variance = weights.T @ covariance_matrix @ weights

    if portfolio_variance < 0:
        raise ValueError("Portfolio variance cannot be negative")

    portfolio_std = np.sqrt(portfolio_variance)

    # Z-score for confidence level
    z_score = stats.norm.ppf(1 - confidence_level)

    # Portfolio VaR
    var = portfolio_value * z_score * portfolio_std
    return var


def calculate_beta(
    asset_returns: Union[pd.Series, np.ndarray],
    market_returns: Union[pd.Series, np.ndarray],
) -> float:
    """Calculate beta of an asset relative to market.

    Args:
        asset_returns: Returns of the asset
        market_returns: Returns of the market index

    Returns:
        Beta coefficient
    """
    if isinstance(asset_returns, pd.Series):
        asset_returns = asset_returns.values
    if isinstance(market_returns, pd.Series):
        market_returns = market_returns.values

    if len(asset_returns) != len(market_returns):
        raise ValueError("Asset and market returns must have same length")

    # Calculate covariance and variance
    covariance = np.cov(asset_returns, market_returns)[0, 1]
    market_variance = np.var(market_returns)

    if market_variance == 0:
        return 0.0

    beta = covariance / market_variance
    return beta


def calculate_sharpe_ratio(
    returns: Union[pd.Series, np.ndarray],
    risk_free_rate: float = 0.02,
    periods_per_year: int = 252,
) -> float:
    """Calculate Sharpe ratio (risk-adjusted return).

    Args:
        returns: Series or array of returns
        risk_free_rate: Annual risk-free rate
        periods_per_year: Number of periods per year (252 for daily)

    Returns:
        Sharpe ratio
    """
    if isinstance(returns, pd.Series):
        returns = returns.values

    if len(returns) == 0:
        return 0.0

    excess_returns = returns - risk_free_rate / periods_per_year
    sharpe = (
        np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(periods_per_year)
    )
    return sharpe


def calculate_sortino_ratio(
    returns: Union[pd.Series, np.ndarray],
    risk_free_rate: float = 0.02,
    periods_per_year: int = 252,
) -> float:
    """Calculate Sortino ratio (downside risk-adjusted return).

    Args:
        returns: Series or array of returns
        risk_free_rate: Annual risk-free rate
        periods_per_year: Number of periods per year

    Returns:
        Sortino ratio
    """
    if isinstance(returns, pd.Series):
        returns = returns.values

    if len(returns) == 0:
        return 0.0

    excess_returns = returns - risk_free_rate / periods_per_year

    # Calculate downside deviation
    downside_returns = excess_returns[excess_returns < 0]
    if len(downside_returns) == 0:
        return np.inf

    downside_std = np.std(downside_returns)

    sortino = np.mean(excess_returns) / downside_std * np.sqrt(periods_per_year)
    return sortino


def calculate_max_drawdown(returns: Union[pd.Series, np.ndarray]) -> float:
    """Calculate maximum drawdown.

    Args:
        returns: Series or array of returns

    Returns:
        Maximum drawdown as positive percentage
    """
    if isinstance(returns, pd.Series):
        cumulative = (1 + returns).cumprod()
    else:
        cumulative = np.cumprod(1 + returns)

    # Calculate running maximum
    running_max = np.maximum.accumulate(cumulative)

    # Calculate drawdown
    drawdown = (cumulative - running_max) / running_max

    max_drawdown = -np.min(drawdown)
    return max_drawdown


def calculate_value_at_risk(
    returns: Union[pd.Series, np.ndarray],
    confidence_level: float = 0.95,
    method: str = "historical",
) -> float:
    """Unified VaR calculation with multiple methods.

    Args:
        returns: Series or array of returns
        confidence_level: Confidence level for VaR
        method: 'historical', 'parametric', or 'monte_carlo'

    Returns:
        VaR value
    """
    if method == "historical":
        return calculate_var_historical(returns, confidence_level)
    elif method == "parametric":
        return calculate_var_parametric(returns, confidence_level)
    elif method == "monte_carlo":
        return calculate_var_monte_carlo(returns, confidence_level)
    else:
        raise ValueError(
            f"Unknown method: {method}. Use 'historical', 'parametric', or 'monte_carlo'."
        )


def calculate_expected_shortfall(
    returns: Union[pd.Series, np.ndarray], confidence_level: float = 0.95
) -> float:
    """Alias for calculate_cvar."""
    return calculate_cvar(returns, confidence_level)


def calculate_greeks(
    s0: float, k: float, t: float, r: float, sigma: float, option_type: str = "call"
) -> Dict[str, float]:
    """Calculate Black-Scholes Greeks for options.

    Args:
        s0: Current stock price
        k: Strike price
        t: Time to expiration (in years)
        r: Risk-free rate
        sigma: Volatility
        option_type: 'call' or 'put'

    Returns:
        Dictionary with delta, gamma, theta, vega, rho
    """
    from scipy.stats import norm

    d1 = (np.log(s0 / k) + (r + 0.5 * sigma**2) * t) / (sigma * np.sqrt(t))
    d2 = d1 - sigma * np.sqrt(t)

    if option_type == "call":
        delta = norm.cdf(d1)
        theta = -(s0 * norm.pdf(d1) * sigma) / (2 * np.sqrt(t)) - r * k * np.exp(
            -r * t
        ) * norm.cdf(d2)
        rho = k * t * np.exp(-r * t) * norm.cdf(d2)
    else:  # put
        delta = norm.cdf(d1) - 1
        theta = -(s0 * norm.pdf(d1) * sigma) / (2 * np.sqrt(t)) + r * k * np.exp(
            -r * t
        ) * norm.cdf(-d2)
        rho = -k * t * np.exp(-r * t) * norm.cdf(-d2)

    # Gamma and vega are same for calls and puts
    gamma = norm.pdf(d1) / (s0 * sigma * np.sqrt(t))
    vega = s0 * norm.pdf(d1) * np.sqrt(t)

    return {"delta": delta, "gamma": gamma, "theta": theta, "vega": vega, "rho": rho}


def calculate_risk_metrics(
    returns: Union[pd.Series, np.ndarray],
    risk_free_rate: float = 0.02,
    confidence_level: float = 0.95,
) -> Dict[str, float]:
    """Calculate comprehensive risk metrics for a returns series.

    Args:
        returns: Series or array of returns
        risk_free_rate: Annual risk-free rate
        confidence_level: Confidence level for VaR/CVaR

    Returns:
        Dictionary of risk metrics
    """
    if isinstance(returns, pd.Series):
        returns_arr = returns.values
    else:
        returns_arr = returns

    metrics = {
        "mean_return": np.mean(returns_arr),
        "volatility": np.std(returns_arr),
        "skewness": stats.skew(returns_arr),
        "kurtosis": stats.kurtosis(returns_arr),
        "sharpe_ratio": calculate_sharpe_ratio(returns_arr, risk_free_rate),
        "sortino_ratio": calculate_sortino_ratio(returns_arr, risk_free_rate),
        "max_drawdown": calculate_max_drawdown(returns_arr),
        "var_historical": calculate_var_historical(returns_arr, confidence_level),
        "cvar": calculate_cvar(returns_arr, confidence_level),
        "var_parametric": calculate_var_parametric(returns_arr, confidence_level),
    }

    return metrics
