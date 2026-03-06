import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mcmc_option_pricing import (
    BlackScholesModel,
    RandomWalkMetropolis,
    MultipleTryMetropolis,
    compute_autocorrelation,
    compute_integrated_autocorrelation_time,
)
import time

plt.rcParams["font.size"] = 10
plt.rcParams["figure.figsize"] = (12, 8)


def plot_comparison(
    S0=100, K=100, T=1, r=0.05, sigma=0.2, n_samples=30000, proposal_std=0.3
):
    bs = BlackScholesModel(S0, K, T, r, sigma)
    analytical_price = bs.call_price_analytical()

    rwmh = RandomWalkMetropolis(bs.log_target, proposal_std=proposal_std)
    rwmh_samples, rwmh_accept = rwmh.sample(n_samples, burn_in=3000)

    k_values = [4, 8]
    mtm_samples_dict = {}
    mtm_accept_dict = {}

    for k in k_values:
        mtm = MultipleTryMetropolis(
            bs.log_target, k_proposals=k, proposal_std=proposal_std
        )
        samples, accept = mtm.sample(n_samples, burn_in=3000)
        mtm_samples_dict[k] = samples
        mtm_accept_dict[k] = accept

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    ax1 = axes[0, 0]
    ax1.plot(rwmh_samples[:500], alpha=0.7, label="RWMH", linewidth=0.8)
    for k in k_values:
        ax1.plot(
            mtm_samples_dict[k][:500], alpha=0.7, label=f"MTM K={k}", linewidth=0.8
        )
    ax1.set_xlabel("Iteration")
    ax1.set_ylabel("Log Stock Price")
    ax1.set_title("Sample Paths (First 500 iterations)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2 = axes[0, 1]
    ax2.hist(rwmh_samples, bins=50, alpha=0.5, density=True, label="RWMH", color="blue")
    for k in k_values:
        ax2.hist(
            mtm_samples_dict[k], bins=50, alpha=0.3, density=True, label=f"MTM K={k}"
        )
    x_range = np.linspace(bs.log_pdf(3), bs.log_pdf(6), 200)
    ax2.plot(
        x_range,
        np.exp([bs.log_pdf(x) for x in x_range]),
        "k--",
        linewidth=2,
        label="True Density",
    )
    ax2.set_xlabel("Log Stock Price")
    ax2.set_ylabel("Density")
    ax2.set_title("Distribution of Log Stock Prices at Maturity")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    ax3 = axes[1, 0]
    rwmh_prices = np.exp(-r * T) * np.maximum(np.exp(rwmh_samples) - K, 0)
    ax3.acorr(
        rwmh_prices - np.mean(rwmh_prices), maxlags=50, label="RWMH", linewidth=1.5
    )
    for k in k_values:
        mtm_prices = np.exp(-r * T) * np.maximum(np.exp(mtm_samples_dict[k]) - K, 0)
        ax3.acorr(
            mtm_prices - np.mean(mtm_prices),
            maxlags=50,
            label=f"MTM K={k}",
            linewidth=1.5,
            alpha=0.7,
        )
    ax3.set_xlabel("Lag")
    ax3.set_ylabel("Autocorrelation")
    ax3.set_title("Autocorrelation Function of Option Prices")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    ax4 = axes[1, 1]
    labels = ["RWMH"] + [f"MTM K={k}" for k in k_values]
    times = []
    iats = []

    start = time.time()
    rwmh_samples, _ = rwmh.sample(n_samples, burn_in=3000)
    times.append(time.time() - start)

    rwmh_prices = np.exp(-r * T) * np.maximum(np.exp(rwmh_samples) - K, 0)
    rwmh_acf = compute_autocorrelation(rwmh_prices)
    iats.append(compute_integrated_autocorrelation_time(rwmh_acf))

    for k in k_values:
        mtm = MultipleTryMetropolis(
            bs.log_target, k_proposals=k, proposal_std=proposal_std
        )
        start = time.time()
        samples, _ = mtm.sample(n_samples, burn_in=3000)
        times.append(time.time() - start)

        mtm_prices = np.exp(-r * T) * np.maximum(np.exp(samples) - K, 0)
        mtm_acf = compute_autocorrelation(mtm_prices)
        iats.append(compute_integrated_autocorrelation_time(mtm_acf))

    x = np.arange(len(labels))
    width = 0.35

    ax4_twin = ax4.twinx()
    bars1 = ax4.bar(
        x - width / 2, times, width, label="Time (s)", color="steelblue", alpha=0.8
    )
    bars2 = ax4_twin.bar(
        x + width / 2, iats, width, label="IAT", color="coral", alpha=0.8
    )

    ax4.set_xlabel("Algorithm")
    ax4.set_ylabel("Time (s)", color="steelblue")
    ax4_twin.set_ylabel("Integrated Autocorrelation Time", color="coral")
    ax4.set_title(f"Performance Comparison (Analytical: {analytical_price:.4f})")
    ax4.set_xticks(x)
    ax4.set_xticklabels(labels)
    ax4.legend(loc="upper left")
    ax4_twin.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig("mcmc_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved mcmc_comparison.png")


def plot_speedup_curve(
    S0=100, K=100, T=1, r=0.05, sigma=0.2, n_samples=30000, proposal_std=0.3
):
    bs = BlackScholesModel(S0, K, T, r, sigma)

    rwmh = RandomWalkMetropolis(bs.log_target, proposal_std=proposal_std)
    start = time.time()
    rwmh_samples, _ = rwmh.sample(n_samples, burn_in=3000)
    rwmh_time = time.time() - start

    rwmh_prices = np.exp(-r * T) * np.maximum(np.exp(rwmh_samples) - K, 0)
    rwmh_acf = compute_autocorrelation(rwmh_prices)
    rwmh_iat = compute_integrated_autocorrelation_time(rwmh_acf)

    k_values = [1, 2, 4, 8, 16, 32]
    speedups = []
    iat_reductions = []

    for k in k_values:
        if k == 1:
            speedups.append(1.0)
            iat_reductions.append(1.0)
            continue

        mtm = MultipleTryMetropolis(
            bs.log_target, k_proposals=k, proposal_std=proposal_std
        )
        start = time.time()
        mtm_samples, _ = mtm.sample(n_samples, burn_in=3000)
        mtm_time = time.time() - start

        mtm_prices = np.exp(-r * T) * np.maximum(np.exp(mtm_samples) - K, 0)
        mtm_acf = compute_autocorrelation(mtm_prices)
        mtm_iat = compute_integrated_autocorrelation_time(mtm_acf)

        speedups.append(rwmh_time / mtm_time)
        iat_reductions.append(rwmh_iat / mtm_iat if mtm_iat > 0 else 0)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    k_plot = k_values[1:]
    speedup_plot = speedups[1:]
    ax1.plot(
        k_plot, speedup_plot, "o-", linewidth=2, markersize=8, label="Observed Speedup"
    )
    ax1.plot(k_plot, k_plot, "k--", linewidth=1, alpha=0.7, label="O(K) Linear")
    ax1.plot(k_plot, np.log(k_plot), "g--", linewidth=1, alpha=0.7, label="O(log K)")
    ax1.set_xlabel("Number of Proposals K")
    ax1.set_ylabel("Speedup (Time Ratio)")
    ax1.set_title("Speedup vs Number of Proposals")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale("log")

    ax2.plot(
        k_plot,
        iat_reductions[1:],
        "s-",
        linewidth=2,
        markersize=8,
        color="coral",
        label="IAT Reduction",
    )
    ax2.axhline(y=1, color="k", linestyle="--", alpha=0.5)
    ax2.set_xlabel("Number of Proposals K")
    ax2.set_ylabel("IAT Reduction Factor")
    ax2.set_title("Integrated Autocorrelation Time Reduction")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale("log")

    plt.tight_layout()
    plt.savefig("speedup_analysis.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved speedup_analysis.png")


if __name__ == "__main__":
    np.random.seed(42)
    plot_comparison()
    plot_speedup_curve()
