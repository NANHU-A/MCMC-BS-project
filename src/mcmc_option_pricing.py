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

    def call_price_analytical(self):
        d1 = (np.log(self.S0 / self.K) + (self.r + 0.5 * self.sigma**2) * self.T) / (
            self.sigma * np.sqrt(self.T)
        )
        d2 = d1 - self.sigma * np.sqrt(self.T)
        return self.S0 * norm.cdf(d1) - self.K * np.exp(-self.r * self.T) * norm.cdf(d2)

    def log_price_density(self, x):
        mean = np.log(self.S0) + (self.r - 0.5 * self.sigma**2) * self.T
        var = self.sigma**2 * self.T
        return norm.pdf(x, loc=mean, scale=np.sqrt(var))

    def log_pdf(self, x):
        mean = np.log(self.S0) + (self.r - 0.5 * self.sigma**2) * self.T
        var = self.sigma**2 * self.T
        return norm.logpdf(x, loc=mean, scale=np.sqrt(var))

    def log_target(self, x):
        return self.log_pdf(x)


class RandomWalkMetropolis:
    def __init__(self, target_log_pdf, proposal_std=0.5):
        self.target_log_pdf = target_log_pdf
        self.proposal_std = proposal_std

    def sample(self, n_samples, x0=None, burn_in=1000):
        if x0 is None:
            x0 = np.random.randn()

        samples = np.zeros(n_samples)
        current_x = x0
        current_log_pdf = self.target_log_pdf(current_x)

        accepted = 0

        for i in range(n_samples + burn_in):
            proposal_x = current_x + np.random.randn() * self.proposal_std
            proposal_log_pdf = self.target_log_pdf(proposal_x)

            log_accept_ratio = proposal_log_pdf - current_log_pdf

            if np.log(np.random.rand()) < log_accept_ratio:
                current_x = proposal_x
                current_log_pdf = proposal_log_pdf
                if i >= burn_in:
                    accepted += 1

            if i >= burn_in:
                samples[i - burn_in] = current_x

        acceptance_rate = accepted / n_samples
        return samples, acceptance_rate


class MultipleTryMetropolis:
    def __init__(self, target_log_pdf, k_proposals=4, proposal_std=0.5):
        self.target_log_pdf = target_log_pdf
        self.k_proposals = k_proposals
        self.proposal_std = proposal_std

    def sample(self, n_samples, x0=None, burn_in=1000):
        if x0 is None:
            x0 = np.random.randn()

        samples = np.zeros(n_samples)
        current_x = x0
        current_log_pdf = self.target_log_pdf(current_x)

        accepted = 0

        k = int(self.k_proposals)
        proposal_std = float(self.proposal_std)

        for i in range(n_samples + burn_in):
            forward_proposals = current_x + np.random.randn(k) * proposal_std
            forward_log_pdf = np.array(
                [self.target_log_pdf(p) for p in forward_proposals]
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
                backward_log_pdf[1:] = np.array([self.target_log_pdf(p) for p in draws])

            log_accept_ratio = logsumexp(forward_log_pdf) - logsumexp(backward_log_pdf)

            if np.log(np.random.rand()) < log_accept_ratio:
                current_x = selected_x
                current_log_pdf = selected_log_pdf
                if i >= burn_in:
                    accepted += 1

            if i >= burn_in:
                samples[i - burn_in] = current_x

        acceptance_rate = accepted / n_samples
        return samples, acceptance_rate


class ParallelMTM:
    def __init__(self, target_log_pdf, n_chains=4, proposal_std=0.5):
        self.target_log_pdf = target_log_pdf
        self.n_chains = n_chains
        self.proposal_std = proposal_std

    def sample(self, n_samples, burn_in=1000):
        n_per_chain = n_samples // self.n_chains
        all_samples = []

        for _ in range(self.n_chains):
            mtm = MultipleTryMetropolis(
                self.target_log_pdf, k_proposals=4, proposal_std=self.proposal_std
            )
            samples, _ = mtm.sample(n_per_chain, burn_in=burn_in)
            all_samples.append(samples)

        return np.concatenate(all_samples), self.n_chains * 0.25


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


def compute_integrated_autocorrelation_time(acf):
    n = len(acf)
    for i in range(1, n):
        if acf[i] < 0:
            return i
    return n


def run_experiment(
    S0=100, K=100, T=1, r=0.05, sigma=0.2, n_samples=20000, proposal_std=0.3
):
    bs = BlackScholesModel(S0, K, T, r, sigma)

    analytical_price = bs.call_price_analytical()
    print(f"Analytical Call Price: {analytical_price:.6f}")

    print("\n=== Random Walk Metropolis-Hastings ===")
    rwmh = RandomWalkMetropolis(bs.log_target, proposal_std=proposal_std)

    start_time = time.time()
    rwmh_samples, rwmh_accept = rwmh.sample(n_samples, burn_in=2000)
    rwmh_time = time.time() - start_time

    rwmh_prices = np.exp(-r * T) * np.maximum(np.exp(rwmh_samples) - K, 0)
    rwmh_price = np.mean(rwmh_prices)
    rwmh_error = abs(rwmh_price - analytical_price)

    rwmh_acf = compute_autocorrelation(rwmh_prices)
    rwmh_iat = compute_integrated_autocorrelation_time(rwmh_acf)

    print(f"Price: {rwmh_price:.6f} (Error: {rwmh_error:.6f})")
    print(f"Acceptance Rate: {rwmh_accept:.4f}")
    print(f"Time: {rwmh_time:.4f}s")
    print(f"Integrated Autocorrelation Time: {rwmh_iat:.2f}")
    print(f"Effective Sample Size: {n_samples / rwmh_iat:.2f}")

    results = {
        "rwmh": {
            "price": rwmh_price,
            "error": rwmh_error,
            "acceptance_rate": rwmh_accept,
            "time": rwmh_time,
            "iat": rwmh_iat,
            "ess": n_samples / rwmh_iat,
        }
    }

    for k in [2, 4, 8]:
        print(f"\n=== Multiple-Try Metropolis (K={k}) ===")
        mtm = MultipleTryMetropolis(
            bs.log_target, k_proposals=k, proposal_std=proposal_std
        )

        start_time = time.time()
        mtm_samples, mtm_accept = mtm.sample(n_samples, burn_in=2000)
        mtm_time = time.time() - start_time

        mtm_prices = np.exp(-r * T) * np.maximum(np.exp(mtm_samples) - K, 0)
        mtm_price = np.mean(mtm_prices)
        mtm_error = abs(mtm_price - analytical_price)

        mtm_acf = compute_autocorrelation(mtm_prices)
        mtm_iat = compute_integrated_autocorrelation_time(mtm_acf)

        print(f"Price: {mtm_price:.6f} (Error: {mtm_error:.6f})")
        print(f"Acceptance Rate: {mtm_accept:.4f}")
        print(f"Time: {mtm_time:.4f}s")
        print(f"Integrated Autocorrelation Time: {mtm_iat:.2f}")
        print(f"Effective Sample Size: {n_samples / mtm_iat:.2f}")

        results[f"mtm_k{k}"] = {
            "price": mtm_price,
            "error": mtm_error,
            "acceptance_rate": mtm_accept,
            "time": mtm_time,
            "iat": mtm_iat,
            "ess": n_samples / mtm_iat,
        }

    return results


def compare_speedup_vs_k(
    S0=100, K=100, T=1, r=0.05, sigma=0.2, n_samples=20000, proposal_std=0.3
):
    bs = BlackScholesModel(S0, K, T, r, sigma)

    print("\n=== Speedup Comparison vs K ===")

    rwmh = RandomWalkMetropolis(bs.log_target, proposal_std=proposal_std)
    start = time.time()
    rwmh_samples, _ = rwmh.sample(n_samples, burn_in=2000)
    rwmh_time = time.time() - start

    rwmh_prices = np.exp(-r * T) * np.maximum(np.exp(rwmh_samples) - K, 0)
    rwmh_acf = compute_autocorrelation(rwmh_prices)
    rwmh_iat = compute_integrated_autocorrelation_time(rwmh_acf)

    print(f"RWMH: Time={rwmh_time:.4f}s, IAT={rwmh_iat:.2f}")

    k_values = [2, 4, 8, 16]
    speedup_data = []

    for k in k_values:
        mtm = MultipleTryMetropolis(
            bs.log_target, k_proposals=k, proposal_std=proposal_std
        )
        start = time.time()
        mtm_samples, _ = mtm.sample(n_samples, burn_in=2000)
        mtm_time = time.time() - start

        mtm_prices = np.exp(-r * T) * np.maximum(np.exp(mtm_samples) - K, 0)
        mtm_acf = compute_autocorrelation(mtm_prices)
        mtm_iat = compute_integrated_autocorrelation_time(mtm_acf)

        speedup = rwmh_time / mtm_time
        iat_reduction = rwmh_iat / mtm_iat if mtm_iat > 0 else 0

        speedup_data.append(
            {
                "k": k,
                "time": mtm_time,
                "iat": mtm_iat,
                "speedup": speedup,
                "iat_reduction": iat_reduction,
            }
        )

        print(
            f"K={k}: Time={mtm_time:.4f}s, IAT={mtm_iat:.2f}, Speedup={speedup:.2f}x, IAT Reduction={iat_reduction:.2f}x"
        )

    return speedup_data


if __name__ == "__main__":
    np.random.seed(42)
    results = run_experiment()
    speedup_data = compare_speedup_vs_k()
