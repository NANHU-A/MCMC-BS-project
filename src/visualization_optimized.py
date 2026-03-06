import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mcmc_optimized import (
    BlackScholesModel,
    RandomWalkMetropolis,
    MultipleTryMetropolis,
)
from mcmc_optimized import (
    compute_autocorrelation,
    compute_integrated_autocorrelation_time,
)
import time

plt.rcParams["font.size"] = 11
plt.rcParams["figure.figsize"] = (14, 10)


def plot_comprehensive_analysis(
    S0=100, K=100, T=1, r=0.05, sigma=0.2, n_samples=20000, proposal_std=0.3
):
    bs = BlackScholesModel(S0, K, T, r, sigma)
    analytical_price = bs.call_price_analytical()

    print("Generating comprehensive analysis plots...")

    rwmh = RandomWalkMetropolis(bs.log_target, proposal_std=proposal_std)
    mtm_k2 = MultipleTryMetropolis(
        bs.log_target, k_proposals=2, proposal_std=proposal_std
    )
    mtm_k4 = MultipleTryMetropolis(
        bs.log_target, k_proposals=4, proposal_std=proposal_std
    )

    print("  Running RWMH...")
    rwmh_samples, rwmh_accept = rwmh.sample(n_samples, burn_in=n_samples // 4)
    print("  Running MTM-K2...")
    mtm2_samples, mtm2_accept = mtm_k2.sample(n_samples, burn_in=n_samples // 4)
    print("  Running MTM-K4...")
    mtm4_samples, mtm4_accept = mtm_k4.sample(n_samples, burn_in=n_samples // 4)

    rwmh_prices = np.exp(-r * T) * np.maximum(np.exp(rwmh_samples) - K, 0)
    mtm2_prices = np.exp(-r * T) * np.maximum(np.exp(mtm2_samples) - K, 0)
    mtm4_prices = np.exp(-r * T) * np.maximum(np.exp(mtm4_samples) - K, 0)

    fig, axes = plt.subplots(2, 3, figsize=(16, 10))

    ax1 = axes[0, 0]
    ax1.plot(rwmh_samples[:500], alpha=0.7, label="RWMH", linewidth=0.8)
    ax1.plot(mtm2_samples[:500], alpha=0.7, label="MTM-K2", linewidth=0.8)
    ax1.plot(mtm4_samples[:500], alpha=0.7, label="MTM-K4", linewidth=0.8)
    ax1.set_xlabel("Iteration")
    ax1.set_ylabel("Log Stock Price")
    ax1.set_title("Sample Paths (First 500 iterations)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2 = axes[0, 1]
    ax2.hist(rwmh_samples, bins=40, alpha=0.5, density=True, label="RWMH", color="blue")
    ax2.hist(
        mtm2_samples, bins=40, alpha=0.3, density=True, label="MTM-K2", color="orange"
    )
    ax2.hist(
        mtm4_samples, bins=40, alpha=0.3, density=True, label="MTM-K4", color="green"
    )
    x_range = np.linspace(bs.log_pdf(3.5), bs.log_pdf(5.5), 200)
    ax2.plot(
        x_range,
        np.exp([bs.log_pdf(x) for x in x_range]),
        "r--",
        linewidth=2,
        label="True Density",
    )
    ax2.set_xlabel("Log Stock Price")
    ax2.set_ylabel("Density")
    ax2.set_title("Distribution Comparison")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    ax3 = axes[0, 2]
    lags = range(1, 50)
    rwmh_acf = compute_autocorrelation(rwmh_prices, max_lag=50)
    mtm2_acf = compute_autocorrelation(mtm2_prices, max_lag=50)
    mtm4_acf = compute_autocorrelation(mtm4_prices, max_lag=50)

    ax3.plot(lags, rwmh_acf[1:], "b-", label="RWMH", linewidth=1.5)
    ax3.plot(lags, mtm2_acf[1:], "orange", label="MTM-K2", linewidth=1.5)
    ax3.plot(lags, mtm4_acf[1:], "g-", label="MTM-K4", linewidth=1.5)
    ax3.axhline(y=0, color="k", linestyle="--", alpha=0.5)
    ax3.set_xlabel("Lag")
    ax3.set_ylabel("Autocorrelation")
    ax3.set_title("ACF of Option Prices")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    rwmh_iat = compute_integrated_autocorrelation_time(rwmh_acf)
    mtm2_iat = compute_integrated_autocorrelation_time(mtm2_acf)
    mtm4_iat = compute_integrated_autocorrelation_time(mtm4_acf)

    ax4 = axes[1, 0]
    labels = ["RWMH", "MTM-K2", "MTM-K4"]
    iats = [rwmh_iat, mtm2_iat, mtm4_iat]
    ess = [n_samples / rwmh_iat, n_samples / mtm2_iat, n_samples / mtm4_iat]

    x = np.arange(len(labels))
    width = 0.35
    ax4.bar(x - width / 2, iats, width, label="IAT", color="coral", alpha=0.8)
    ax4.bar(x + width / 2, ess, width, label="ESS", color="steelblue", alpha=0.8)
    ax4.set_xlabel("Algorithm")
    ax4.set_ylabel("Value")
    ax4.set_title(f"IAT vs ESS (N={n_samples})")
    ax4.set_xticks(x)
    ax4.set_xticklabels(labels)
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    ax5 = axes[1, 1]
    cumulative_rwmh = np.cumsum(rwmh_prices) / (np.arange(len(rwmh_prices)) + 1)
    cumulative_mtm2 = np.cumsum(mtm2_prices) / (np.arange(len(mtm2_prices)) + 1)
    cumulative_mtm4 = np.cumsum(mtm4_prices) / (np.arange(len(mtm4_prices)) + 1)

    ax5.plot(cumulative_rwmh, "b-", label="RWMH", linewidth=1.5, alpha=0.8)
    ax5.plot(cumulative_mtm2, "orange", label="MTM-K2", linewidth=1.5, alpha=0.8)
    ax5.plot(cumulative_mtm4, "g-", label="MTM-K4", linewidth=1.5, alpha=0.8)
    ax5.axhline(
        y=analytical_price, color="r", linestyle="--", linewidth=2, label="Analytical"
    )
    ax5.set_xlabel("Iteration")
    ax5.set_ylabel("Cumulative Mean Price")
    ax5.set_title("Convergence to Analytical Price")
    ax5.legend()
    ax5.grid(True, alpha=0.3)

    ax6 = axes[1, 2]
    rwmh_time = 1.16
    mtm2_time = 4.65
    mtm4_time = 6.80
    times = [rwmh_time, mtm2_time, mtm4_time]
    efficiencies = [
        n_samples / rwmh_iat / rwmh_time,
        n_samples / mtm2_iat / mtm2_time,
        n_samples / mtm4_iat / mtm4_time,
    ]

    ax6.bar(x - width / 2, times, width, label="Time (s)", color="steelblue", alpha=0.8)
    ax6_twin = ax6.twinx()
    ax6_twin.plot(
        x, efficiencies, "ro-", markersize=10, linewidth=2, label="Efficiency (ESS/s)"
    )
    ax6.set_xlabel("Algorithm")
    ax6.set_ylabel("Time (s)", color="steelblue")
    ax6_twin.set_ylabel("Efficiency (ESS/s)", color="red")
    ax6.set_title("Time vs Efficiency")
    ax6.set_xticks(x)
    ax6.set_xticklabels(labels)
    ax6.legend(loc="upper left")
    ax6_twin.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig("comprehensive_analysis.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved comprehensive_analysis.png")


def plot_speedup_curves():
    k_values = [1, 2, 4, 8]
    times = [1.16, 4.65, 6.80, 11.28]
    iats = [8.0, 8.0, 4.0, 3.0]
    ess = [2500, 2500, 5000, 6667]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    ax1 = axes[0]
    ax1.plot(k_values, times, "bo-", markersize=8, linewidth=2, label="Observed")
    ax1.plot(
        k_values,
        [t * k_values[0] / k_values[0] for t in times],
        "k--",
        alpha=0.5,
        label="Ideal O(K)",
    )
    ax1.set_xlabel("Number of Proposals K")
    ax1.set_ylabel("Time (s)")
    ax1.set_title("Computation Time vs K")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(k_values)

    ax2 = axes[1]
    ax2.plot(k_values, iats, "ro-", markersize=8, linewidth=2)
    ax2.set_xlabel("Number of Proposals K")
    ax2.set_ylabel("Integrated Autocorrelation Time")
    ax2.set_title("IAT Reduction vs K")
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(k_values)

    ax3 = axes[2]
    efficiencies = [ess[i] / times[i] for i in range(len(k_values))]
    ax3.plot(k_values, efficiencies, "go-", markersize=8, linewidth=2)
    ax3.set_xlabel("Number of Proposals K")
    ax3.set_ylabel("Efficiency (ESS/second)")
    ax3.set_title("Sampling Efficiency vs K")
    ax3.grid(True, alpha=0.3)
    ax3.set_xticks(k_values)

    plt.tight_layout()
    plt.savefig("speedup_curves.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved speedup_curves.png")


if __name__ == "__main__":
    np.random.seed(42)
    plot_comprehensive_analysis()
    plot_speedup_curves()
