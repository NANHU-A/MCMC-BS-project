"""Quantitative finance utilities.

This module provides utility functions for statistical analysis,
time series processing, MCMC diagnostics, and financial calculations.
"""

import numpy as np
import pandas as pd
from typing import Union, List, Tuple, Dict, Optional
from scipy import stats, signal
import warnings

warnings.filterwarnings("ignore")


def calculate_autocorrelation(
    series: Union[np.ndarray, pd.Series], max_lag: int = 50
) -> np.ndarray:
    """
    Calculate autocorrelation function for a time series.

    Args:
        series: Time series data
        max_lag: Maximum lag to compute

    Returns:
        Array of autocorrelations for lags 0 to max_lag
    """
    if isinstance(series, pd.Series):
        series = series.values

    n = len(series)
    mean = np.mean(series)
    var = np.var(series)

    if var == 0:
        return np.zeros(max_lag + 1)

    acf = np.zeros(max_lag + 1)
    acf[0] = 1.0

    for k in range(1, max_lag + 1):
        if k >= n:
            break
        acf[k] = np.sum((series[: n - k] - mean) * (series[k:] - mean)) / (n * var)

    return acf


def calculate_effective_sample_size(samples: np.ndarray, max_lag: int = 1000) -> float:
    """
    Calculate effective sample size (ESS) for MCMC samples.

    ESS = N / (1 + 2 * Σ_{k=1}^∞ ρ(k))
    where ρ(k) is the autocorrelation at lag k.

    Args:
        samples: MCMC samples (1D array)
        max_lag: Maximum lag for autocorrelation calculation

    Returns:
        Effective sample size
    """
    n = len(samples)

    if n < 10:
        return n

    # Calculate autocorrelation
    acf = calculate_autocorrelation(samples, max_lag)

    # Sum autocorrelations (skip lag 0)
    acf_sum = 0.0
    for k in range(1, min(max_lag, len(acf))):
        if acf[k] > 0:
            acf_sum += acf[k]
        else:
            # Stop when autocorrelation becomes negative
            break

    ess = n / (1 + 2 * acf_sum)
    return max(ess, 1.0)


def calculate_integrated_autocorrelation_time(
    samples: np.ndarray, max_lag: int = 1000
) -> float:
    """
    Calculate integrated autocorrelation time (IAT) for MCMC samples.

    IAT = 1 + 2 * Σ_{k=1}^∞ ρ(k)

    Args:
        samples: MCMC samples
        max_lag: Maximum lag for autocorrelation calculation

    Returns:
        Integrated autocorrelation time
    """
    ess = calculate_effective_sample_size(samples, max_lag)
    n = len(samples)

    if ess > 0:
        iat = n / ess
    else:
        iat = n

    return iat


def calculate_gelman_rubin_statistic(chains: List[np.ndarray]) -> float:
    """
    Calculate Gelman-Rubin R-hat statistic for MCMC convergence.

    R-hat compares between-chain and within-chain variance.
    Values close to 1 indicate convergence.

    Args:
        chains: List of chains from multiple MCMC runs

    Returns:
        R-hat statistic
    """
    m = len(chains)  # number of chains
    if m < 2:
        return 1.0

    # Chain lengths (assuming same length)
    n = len(chains[0])

    # Calculate within-chain variance
    chain_means = [np.mean(chain) for chain in chains]
    chain_vars = [np.var(chain, ddof=1) for chain in chains]

    W = np.mean(chain_vars)  # within-chain variance

    # Calculate between-chain variance
    overall_mean = np.mean(chain_means)
    B = n * np.var(chain_means, ddof=1)  # between-chain variance

    # Estimate marginal posterior variance
    var_plus = (n - 1) / n * W + B / n

    # Compute R-hat
    rhat = np.sqrt(var_plus / W)

    return rhat


def calculate_ess_per_second(
    samples: np.ndarray, elapsed_time: float, max_lag: int = 1000
) -> float:
    """
    Calculate effective samples per second (ESS/s).

    Args:
        samples: MCMC samples
        elapsed_time: Total sampling time in seconds
        max_lag: Maximum lag for autocorrelation

    Returns:
        Effective samples per second
    """
    if elapsed_time <= 0:
        return 0.0

    ess = calculate_effective_sample_size(samples, max_lag)
    return ess / elapsed_time


def standardize_returns(
    returns: Union[np.ndarray, pd.Series], method: str = "zscore"
) -> np.ndarray:
    """
    Standardize returns for analysis.

    Args:
        returns: Returns series
        method: Standardization method ('zscore', 'robust', 'minmax')

    Returns:
        Standardized returns
    """
    if isinstance(returns, pd.Series):
        returns = returns.values

    if method == "zscore":
        mean = np.mean(returns)
        std = np.std(returns)
        if std > 0:
            standardized = (returns - mean) / std
        else:
            standardized = returns - mean

    elif method == "robust":
        median = np.median(returns)
        mad = np.median(np.abs(returns - median))
        if mad > 0:
            standardized = (returns - median) / mad
        else:
            standardized = returns - median

    elif method == "minmax":
        min_val = np.min(returns)
        max_val = np.max(returns)
        range_val = max_val - min_val
        if range_val > 0:
            standardized = (returns - min_val) / range_val
        else:
            standardized = returns - min_val

    else:
        raise ValueError(f"Unknown method: {method}")

    return standardized


def calculate_rolling_statistics(
    series: Union[np.ndarray, pd.Series], window: int = 20
) -> Dict[str, np.ndarray]:
    """
    Calculate rolling statistics for a time series.

    Args:
        series: Time series data
        window: Rolling window size

    Returns:
        Dictionary with rolling statistics
    """
    if isinstance(series, pd.Series):
        series = series.values

    n = len(series)
    if n < window:
        # Return arrays of NaNs
        empty = np.full(n, np.nan)
        return {
            "mean": empty,
            "std": empty,
            "min": empty,
            "max": empty,
            "median": empty,
        }

    # Initialize arrays
    rolling_mean = np.full(n, np.nan)
    rolling_std = np.full(n, np.nan)
    rolling_min = np.full(n, np.nan)
    rolling_max = np.full(n, np.nan)
    rolling_median = np.full(n, np.nan)

    # Calculate rolling statistics
    for i in range(window - 1, n):
        window_data = series[i - window + 1 : i + 1]
        rolling_mean[i] = np.mean(window_data)
        rolling_std[i] = np.std(window_data)
        rolling_min[i] = np.min(window_data)
        rolling_max[i] = np.max(window_data)
        rolling_median[i] = np.median(window_data)

    return {
        "mean": rolling_mean,
        "std": rolling_std,
        "min": rolling_min,
        "max": rolling_max,
        "median": rolling_median,
    }


def detect_outliers(
    series: Union[np.ndarray, pd.Series], method: str = "iqr", threshold: float = 3.0
) -> np.ndarray:
    """
    Detect outliers in a time series.

    Args:
        series: Time series data
        method: Detection method ('iqr', 'zscore', 'modified_zscore')
        threshold: Threshold for outlier detection

    Returns:
        Boolean array indicating outliers
    """
    if isinstance(series, pd.Series):
        series = series.values

    if method == "iqr":
        q1 = np.percentile(series, 25)
        q3 = np.percentile(series, 75)
        iqr = q3 - q1
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        outliers = (series < lower_bound) | (series > upper_bound)

    elif method == "zscore":
        mean = np.mean(series)
        std = np.std(series)
        if std > 0:
            z_scores = np.abs((series - mean) / std)
            outliers = z_scores > threshold
        else:
            outliers = np.zeros_like(series, dtype=bool)

    elif method == "modified_zscore":
        median = np.median(series)
        mad = np.median(np.abs(series - median))
        if mad > 0:
            modified_z_scores = 0.6745 * (series - median) / mad
            outliers = np.abs(modified_z_scores) > threshold
        else:
            outliers = np.zeros_like(series, dtype=bool)

    else:
        raise ValueError(f"Unknown method: {method}")

    return outliers


def calculate_correlation_matrix(
    returns: pd.DataFrame, method: str = "pearson"
) -> pd.DataFrame:
    """
    Calculate correlation matrix for multiple time series.

    Args:
        returns: DataFrame of returns (columns = assets, rows = time)
        method: Correlation method ('pearson', 'spearman', 'kendall')

    Returns:
        Correlation matrix
    """
    return returns.corr(method=method)


def calculate_cointegration_test(
    series1: Union[np.ndarray, pd.Series], series2: Union[np.ndarray, pd.Series]
) -> Dict[str, float]:
    """
    Perform cointegration test between two time series.

    Args:
        series1: First time series
        series2: Second time series

    Returns:
        Dictionary with test statistics
    """
    if isinstance(series1, pd.Series):
        series1 = series1.values
    if isinstance(series2, pd.Series):
        series2 = series2.values

    # Ensure same length
    min_len = min(len(series1), len(series2))
    series1 = series1[:min_len]
    series2 = series2[:min_len]

    # Simple linear regression for cointegration test
    # In practice, use statsmodels or similar for proper test
    beta = np.cov(series1, series2)[0, 1] / np.var(series2)
    alpha = np.mean(series1) - beta * np.mean(series2)

    # Calculate spread
    spread = series1 - (alpha + beta * series2)

    # Augmented Dickey-Fuller test on spread (simplified)
    # Calculate test statistic
    spread_diff = np.diff(spread)
    spread_lag = spread[:-1]

    if len(spread_diff) > 1:
        # Simple ADF test statistic
        numerator = np.sum(spread_lag * spread_diff) / len(spread_diff)
        denominator = np.sum(spread_lag**2) / len(spread_diff)

        if denominator > 0:
            adf_stat = numerator / denominator
        else:
            adf_stat = 0.0
    else:
        adf_stat = 0.0

    # Calculate half-life of mean reversion
    spread_lag = spread[:-1]
    spread_future = spread[1:]

    if len(spread_lag) > 1 and len(spread_future) > 1:
        # Linear regression: spread_future = alpha + beta * spread_lag
        beta_halflife = np.cov(spread_lag, spread_future)[0, 1] / np.var(spread_lag)
        half_life = -np.log(2) / np.log(beta_halflife) if beta_halflife > 0 else 0
    else:
        half_life = 0.0

    return {
        "beta": beta,
        "alpha": alpha,
        "adf_statistic": adf_stat,
        "half_life": half_life,
        "spread_std": np.std(spread),
    }


def calculate_volatility_metrics(
    returns: Union[np.ndarray, pd.Series], window: int = 20
) -> Dict[str, np.ndarray]:
    """
    Calculate various volatility metrics.

    Args:
        returns: Returns series
        window: Rolling window size

    Returns:
        Dictionary with volatility metrics
    """
    if isinstance(returns, pd.Series):
        returns = returns.values

    n = len(returns)

    # Initialize arrays
    realized_vol = np.full(n, np.nan)
    parkinson_vol = np.full(n, np.nan)
    garman_klass_vol = np.full(n, np.nan)
    yang_zhang_vol = np.full(n, np.nan)

    # Note: This function expects OHLC data, but we only have returns
    # For simplicity, we'll calculate realized volatility
    for i in range(window - 1, n):
        window_returns = returns[i - window + 1 : i + 1]
        realized_vol[i] = np.std(window_returns) * np.sqrt(252)

    return {
        "realized_volatility": realized_vol,
        "parkinson_volatility": parkinson_vol,
        "garman_klass_volatility": garman_klass_vol,
        "yang_zhang_volatility": yang_zhang_vol,
    }


def calculate_momentum_indicators(
    prices: Union[np.ndarray, pd.Series], windows: List[int] = [10, 20, 50]
) -> Dict[str, np.ndarray]:
    """
    Calculate momentum indicators.

    Args:
        prices: Price series
        windows: List of window sizes for momentum calculation

    Returns:
        Dictionary with momentum indicators
    """
    if isinstance(prices, pd.Series):
        prices = prices.values

    n = len(prices)
    indicators = {}

    for window in windows:
        # Momentum (price change over window)
        momentum = np.full(n, np.nan)
        for i in range(window, n):
            momentum[i] = prices[i] / prices[i - window] - 1

        indicators[f"momentum_{window}"] = momentum

        # Rate of Change (ROC)
        roc = np.full(n, np.nan)
        for i in range(window, n):
            roc[i] = (prices[i] - prices[i - window]) / prices[i - window]

        indicators[f"roc_{window}"] = roc

    # Moving averages
    for window in windows:
        ma = np.full(n, np.nan)
        for i in range(window - 1, n):
            ma[i] = np.mean(prices[i - window + 1 : i + 1])

        indicators[f"ma_{window}"] = ma

    # Exponential moving average (simplified)
    for window in windows:
        ema = np.full(n, np.nan)
        alpha = 2 / (window + 1)

        if n > 0:
            ema[0] = prices[0]
            for i in range(1, n):
                ema[i] = alpha * prices[i] + (1 - alpha) * ema[i - 1]

        indicators[f"ema_{window}"] = ema

    return indicators


def calculate_technical_indicators(
    prices: Union[np.ndarray, pd.Series],
    high: Optional[np.ndarray] = None,
    low: Optional[np.ndarray] = None,
    volume: Optional[np.ndarray] = None,
) -> Dict[str, np.ndarray]:
    """
    Calculate common technical indicators.

    Args:
        prices: Closing prices
        high: High prices (optional)
        low: Low prices (optional)
        volume: Volume data (optional)

    Returns:
        Dictionary with technical indicators
    """
    if isinstance(prices, pd.Series):
        prices = prices.values

    n = len(prices)

    # Initialize indicators
    indicators = {}

    # Relative Strength Index (RSI)
    window_rsi = 14
    rsi = np.full(n, np.nan)

    if n > window_rsi:
        # Calculate price changes
        deltas = np.diff(prices)

        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        # Calculate average gains and losses
        avg_gains = np.full(n, np.nan)
        avg_losses = np.full(n, np.nan)

        # Initial average
        avg_gains[window_rsi] = np.mean(gains[:window_rsi])
        avg_losses[window_rsi] = np.mean(losses[:window_rsi])

        # Smooth averages
        for i in range(window_rsi + 1, n):
            avg_gains[i] = (
                avg_gains[i - 1] * (window_rsi - 1) + gains[i - 1]
            ) / window_rsi
            avg_losses[i] = (
                avg_losses[i - 1] * (window_rsi - 1) + losses[i - 1]
            ) / window_rsi

        # Calculate RSI
        for i in range(window_rsi, n):
            if avg_losses[i] > 0:
                rs = avg_gains[i] / avg_losses[i]
                rsi[i] = 100 - 100 / (1 + rs)
            else:
                rsi[i] = 100

    indicators["rsi"] = rsi

    # Bollinger Bands
    window_bb = 20
    bb_upper = np.full(n, np.nan)
    bb_middle = np.full(n, np.nan)
    bb_lower = np.full(n, np.nan)

    if n >= window_bb:
        for i in range(window_bb - 1, n):
            window_prices = prices[i - window_bb + 1 : i + 1]
            middle = np.mean(window_prices)
            std = np.std(window_prices)

            bb_middle[i] = middle
            bb_upper[i] = middle + 2 * std
            bb_lower[i] = middle - 2 * std

    indicators["bb_upper"] = bb_upper
    indicators["bb_middle"] = bb_middle
    indicators["bb_lower"] = bb_lower

    # MACD (Moving Average Convergence Divergence)
    macd = np.full(n, np.nan)
    signal_line = np.full(n, np.nan)
    histogram = np.full(n, np.nan)

    if n > 26:  # Need at least 26 periods for MACD
        # Calculate EMAs
        ema12 = np.full(n, np.nan)
        ema26 = np.full(n, np.nan)

        # Initial EMAs
        ema12[0] = prices[0]
        ema26[0] = prices[0]

        alpha12 = 2 / (12 + 1)
        alpha26 = 2 / (26 + 1)

        for i in range(1, n):
            ema12[i] = alpha12 * prices[i] + (1 - alpha12) * ema12[i - 1]
            ema26[i] = alpha26 * prices[i] + (1 - alpha26) * ema26[i - 1]

        # MACD line
        macd = ema12 - ema26

        # Signal line (9-period EMA of MACD)
        signal_line = np.full(n, np.nan)
        signal_line[0] = macd[0]
        alpha_signal = 2 / (9 + 1)

        for i in range(1, n):
            signal_line[i] = (
                alpha_signal * macd[i] + (1 - alpha_signal) * signal_line[i - 1]
            )

        # Histogram
        histogram = macd - signal_line

    indicators["macd"] = macd
    indicators["macd_signal"] = signal_line
    indicators["macd_histogram"] = histogram

    return indicators
