import numpy as np
from scipy.stats import norm
from scipy.special import logsumexp
import time


class BlackScholesModel:
    def __init__(self, S0, K, T, r, sigma):
        self.S0 = S0
        self.K = K
        self.T = T
        self.r = r
        self.sigma = sigma
        self._setup_precomputed()

    def _setup_precomputed(self):
        self.log_S0 = np.log(self.S0)
        self.mean = self.log_S0 + (self.r - 0.5 * self.sigma**2) * self.T
        self.std = self.sigma * np.sqrt(self.T)

    def call_price_analytical(self):
        d1 = (np.log(self.S0 / self.K) + (self.r + 0.5 * self.sigma**2) * self.T) / (
            self.sigma * np.sqrt(self.T)
        )
        d2 = d1 - self.sigma * np.sqrt(self.T)
        return self.S0 * norm.cdf(d1) - self.K * np.exp(-self.r * self.T) * norm.cdf(d2)

    def log_pdf(self, x):
        return norm.logpdf(x, loc=self.mean, scale=self.std)

    def log_target(self, x):
        return self.log_pdf(x)


class RandomWalkMetropolis:
    def __init__(self, log_pdf_func, proposal_std=0.5):
        self.log_pdf_func = log_pdf_func
        self.proposal_std = proposal_std

    def sample(self, n_samples, x0=None, burn_in=1000):
        if x0 is None:
            x0 = np.random.randn()

        samples = np.zeros(n_samples)
        current_x = float(x0)
        current_log_pdf = self.log_pdf_func(current_x)
        accepted = 0
        proposal_std = float(self.proposal_std)

        for i in range(n_samples + burn_in):
            proposal_x = current_x + np.random.randn() * proposal_std
            proposal_log_pdf = self.log_pdf_func(proposal_x)

            log_accept_ratio = proposal_log_pdf - current_log_pdf

            if np.log(np.random.rand()) < log_accept_ratio:
                current_x = proposal_x
                current_log_pdf = proposal_log_pdf
                if i >= burn_in:
                    accepted += 1

            if i >= burn_in:
                samples[i - burn_in] = current_x

        return samples, accepted / n_samples


class MultipleTryMetropolis:
    def __init__(self, log_pdf_func, k_proposals=4, proposal_std=0.5):
        self.log_pdf_func = log_pdf_func
        self.k_proposals = k_proposals
        self.proposal_std = proposal_std

    def sample(self, n_samples, x0=None, burn_in=1000):
        if x0 is None:
            x0 = np.random.randn()

        samples = np.zeros(n_samples)
        current_x = float(x0)
        current_log_pdf = self.log_pdf_func(current_x)
        accepted = 0
        k = int(self.k_proposals)
        proposal_std = float(self.proposal_std)

        for i in range(n_samples + burn_in):
            forward_proposals = current_x + np.random.randn(k) * proposal_std
            forward_log_pdf = np.array(
                [self.log_pdf_func(p) for p in forward_proposals]
            )

            forward_weights = np.exp(forward_log_pdf - np.max(forward_log_pdf))
            forward_probs = forward_weights / np.sum(forward_weights)

            selected_idx = np.random.choice(k, p=forward_probs)
            selected_x = forward_proposals[selected_idx]
            selected_log_pdf = forward_log_pdf[selected_idx]

            backward_proposals = np.zeros(k)
            backward_log_pdf = np.zeros(k)
            backward_proposals[0] = current_x
            backward_log_pdf[0] = current_log_pdf
            if k > 1:
                draws = selected_x + np.random.randn(k - 1) * proposal_std
                backward_proposals[1:] = draws
                backward_log_pdf[1:] = np.array([self.log_pdf_func(p) for p in draws])

            log_accept_ratio = logsumexp(forward_log_pdf) - logsumexp(backward_log_pdf)

            if np.log(np.random.rand()) < log_accept_ratio:
                current_x = selected_x
                current_log_pdf = selected_log_pdf
                if i >= burn_in:
                    accepted += 1

            if i >= burn_in:
                samples[i - burn_in] = current_x

        return samples, accepted / n_samples


def compute_autocorrelation(samples, max_lag=50):
    n = len(samples)
    mean = np.mean(samples)
    var = np.var(samples)
    if var == 0:
        return np.zeros(max_lag)
    acf = np.zeros(max_lag)
    for lag in range(1, max_lag):
        acf[lag] = np.sum((samples[lag:] - mean) * (samples[:-lag] - mean)) / (
            (n - lag) * var
        )
    acf[0] = 1.0
    return acf


def compute_integrated_autocorrelation_time(acf, threshold=0.05):
    n = len(acf)
    for i in range(1, n):
        if acf[i] < threshold:
            return i
    return n


def run_comparison(
    S0=100, K=100, T=1, r=0.05, sigma=0.2, n_samples=20000, proposal_std=0.3
):
    bs = BlackScholesModel(S0, K, T, r, sigma)
    analytical_price = bs.call_price_analytical()

    print("=" * 60)
    print("Black-Scholes Option Pricing - MCMC Comparison")
    print("Analytical Price: %.6f" % analytical_price)
    print("=" * 60)

    algorithms = [
        ("RWMH", RandomWalkMetropolis(bs.log_target, proposal_std=proposal_std)),
        (
            "MTM-K2",
            MultipleTryMetropolis(
                bs.log_target, k_proposals=2, proposal_std=proposal_std
            ),
        ),
        (
            "MTM-K4",
            MultipleTryMetropolis(
                bs.log_target, k_proposals=4, proposal_std=proposal_std
            ),
        ),
    ]

    results = {}

    for name, algo in algorithms:
        print("\n>>> %s..." % name, end=" ", flush=True)

        start = time.time()
        samples, accept_rate = algo.sample(n_samples, burn_in=n_samples // 4)
        elapsed = time.time() - start

        prices = np.exp(-r * T) * np.maximum(np.exp(samples) - K, 0)
        price = np.mean(prices)
        error = abs(price - analytical_price)

        acf = compute_autocorrelation(prices)
        iat = compute_integrated_autocorrelation_time(acf)
        ess = n_samples / iat

        results[name] = {
            "price": price,
            "error": error,
            "time": elapsed,
            "iat": iat,
            "ess": ess,
        }

        print("Done! Time: %.2fs, IAT: %.1f, ESS: %.0f" % (elapsed, iat, ess))

    return results


def run_speedup_analysis(
    S0=100, K=100, T=1, r=0.05, sigma=0.2, n_samples=20000, proposal_std=0.3
):
    bs = BlackScholesModel(S0, K, T, r, sigma)

    print("\n" + "=" * 60)
    print("Speedup Analysis vs K")
    print("=" * 60)

    rwmh = RandomWalkMetropolis(bs.log_target, proposal_std=proposal_std)
    start = time.time()
    rwmh_samples, _ = rwmh.sample(n_samples, burn_in=n_samples // 4)
    rwmh_time = time.time() - start

    rwmh_prices = np.exp(-r * T) * np.maximum(np.exp(rwmh_samples) - K, 0)
    rwmh_acf = compute_autocorrelation(rwmh_prices)
    rwmh_iat = compute_integrated_autocorrelation_time(rwmh_acf)

    print("RWMH: Time=%.3fs, IAT=%.1f" % (rwmh_time, rwmh_iat))

    for k in [2, 4, 8]:
        mtm = MultipleTryMetropolis(
            bs.log_target, k_proposals=k, proposal_std=proposal_std
        )

        start = time.time()
        mtm_samples, _ = mtm.sample(n_samples, burn_in=n_samples // 4)
        mtm_time = time.time() - start

        mtm_prices = np.exp(-r * T) * np.maximum(np.exp(mtm_samples) - K, 0)
        mtm_acf = compute_autocorrelation(mtm_prices)
        mtm_iat = compute_integrated_autocorrelation_time(mtm_acf)

        time_speedup = rwmh_time / mtm_time
        iat_reduction = rwmh_iat / mtm_iat

        print(
            "K=%d: Time=%.3fs, IAT=%.1f, Speedup=%.2fx, IATRed=%.2fx"
            % (k, mtm_time, mtm_iat, time_speedup, iat_reduction)
        )


def run_baseline_comparison():
    S0, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
    n_samples = 50000

    bs = BlackScholesModel(S0, K, T, r, sigma)
    analytical_price = bs.call_price_analytical()

    print("\n" + "=" * 60)
    print("Baseline Comparison: MC vs MCMC")
    print("=" * 60)

    mean = np.log(S0) + (r - 0.5 * sigma**2) * T
    std = sigma * np.sqrt(T)

    start = time.time()
    mc_samples = np.random.normal(mean, std, n_samples)
    mc_time = time.time() - start

    mc_prices = np.exp(-r * T) * np.maximum(np.exp(mc_samples) - K, 0)
    mc_price = np.mean(mc_prices)
    mc_error = abs(mc_price - analytical_price)
    mc_std = np.std(mc_prices) / np.sqrt(n_samples)

    print(
        "MC: Price=%.4f, Error=%.4f, Std=%.4f, Time=%.4fs"
        % (mc_price, mc_error, mc_std, mc_time)
    )

    rwmh = RandomWalkMetropolis(bs.log_target, proposal_std=0.3)
    start = time.time()
    mcmc_samples, _ = rwmh.sample(n_samples, burn_in=n_samples // 4)
    mcmc_time = time.time() - start

    mcmc_prices = np.exp(-r * T) * np.maximum(np.exp(mcmc_samples) - K, 0)
    mcmc_price = np.mean(mcmc_prices)
    mcmc_error = abs(mcmc_price - analytical_price)

    mcmc_acf = compute_autocorrelation(mcmc_prices)
    mcmc_iat = compute_integrated_autocorrelation_time(mcmc_acf)
    mcmc_ess = n_samples / mcmc_iat

    print(
        "MCMC: Price=%.4f, Error=%.4f, Time=%.2fs, IAT=%.1f, ESS=%.0f"
        % (mcmc_price, mcmc_error, mcmc_time, mcmc_iat, mcmc_ess)
    )
    print(
        "\nConclusion: MC is faster for simple problems, MCMC useful for complex distributions"
    )


if __name__ == "__main__":
    np.random.seed(42)

    print("=" * 60)
    print("MCMC Option Pricing - Optimization Results")
    print("=" * 60)

    run_baseline_comparison()
    results = run_comparison(n_samples=20000)
    run_speedup_analysis(n_samples=20000)

    print("\n" + "=" * 60)
    print("Key Findings:")
    print("1. RWMH: Fast but high IAT")
    print("2. MTM: Higher acceptance, lower IAT")
    print("3. Trade-off: Computation time vs sampling efficiency")
    print("=" * 60)
