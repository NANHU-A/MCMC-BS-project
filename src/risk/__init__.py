"""Risk management module for quantitative finance.

Provides:
- Value at Risk (VaR) and Conditional VaR (CVaR) calculations
- Portfolio risk metrics and analytics
- Risk-adjusted performance measures
- Stress testing and scenario analysis
"""

from .risk_metrics import (
    calculate_var_historical,
    calculate_var_parametric,
    calculate_var_monte_carlo,
    calculate_cvar,
    calculate_portfolio_var,
    calculate_beta,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_max_drawdown,
    calculate_value_at_risk,
    calculate_expected_shortfall,
    calculate_greeks,
    calculate_risk_metrics,
)

__all__ = [
    "calculate_var_historical",
    "calculate_var_parametric",
    "calculate_var_monte_carlo",
    "calculate_cvar",
    "calculate_portfolio_var",
    "calculate_beta",
    "calculate_sharpe_ratio",
    "calculate_sortino_ratio",
    "calculate_max_drawdown",
    "calculate_value_at_risk",
    "calculate_shortfall",
    "calculate_greeks",
    "calculate_risk_metrics",
]
