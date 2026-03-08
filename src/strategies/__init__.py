"""Trading strategies for quantitative finance.

This module provides strategies that leverage MCMC models for:
- Volatility forecasting and trading
- Statistical arbitrage
- Option pricing and hedging
- Market making
"""

from .mcmc_strategies import (
    MCMCVolatilityForecastingStrategy,
    HestonCalibrationStrategy,
    StatisticalArbitrageStrategy,
    OptionMarketMakingStrategy,
)

from .advanced_strategies import (
    BayesianPortfolioStrategy,
    RegimeSwitchingStrategy,
    JumpDiffusionStrategy,
)

__all__ = [
    "MCMCVolatilityForecastingStrategy",
    "HestonCalibrationStrategy",
    "StatisticalArbitrageStrategy",
    "OptionMarketMakingStrategy",
    "BayesianPortfolioStrategy",
    "RegimeSwitchingStrategy",
    "JumpDiffusionStrategy",
]
