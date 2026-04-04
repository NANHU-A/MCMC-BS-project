import numpy as np
from scipy.stats import norm
from scipy.special import logsumexp
import time


class BlackScholesModel:
    """Black-Scholes期权定价模型"""

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
        """解析解"""
        d1 = (np.log(self.S0 / self.K) + (self.r + 0.5 * self.sigma**2) * self.T) / (
            self.sigma * np.sqrt(self.T)
        )
        d2 = d1 - self.sigma * np.sqrt(self.T)
        return self.S0 * norm.cdf(d1) - self.K * np.exp(-self.r * self.T) * norm.cdf(d2)

    def log_pdf(self, x):
        """对数正态分布密度"""
        return norm.logpdf(x, loc=self.mean, scale=self.std)

    def log_target(self, x):
        return self.log_pdf(x)


class RandomWalkMetropolis:
    """标准单提案RWMH算法"""

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
    """Multiple-Try Metropolis (MTM)多提案算法"""

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


class LocallyBalancedMTM:
    """局部平衡MTM (LB-MTM) - 改进版多提案算法

    相比标准MTM，LB-MTM使用局部平衡权重，在高维问题中
    具有更快的收敛速度（来自JMLR 2024最新研究）
    """

    def __init__(self, log_pdf_func, k_proposals=4, proposal_std=0.5, tau=1.0):
        self.log_pdf_func = log_pdf_func
        self.k_proposals = k_proposals
        self.proposal_std = proposal_std
        self.tau = tau  # 温度参数，控制探索/利用平衡

    def local_balance_weight(self, log_pdf, current_log_pdf):
        """局部平衡权重函数"""
        return np.exp((log_pdf - current_log_pdf) / self.tau)

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
            proposals = current_x + np.random.randn(k) * proposal_std
            proposal_log_pdfs = np.array([self.log_pdf_func(p) for p in proposals])

            lb_weights = np.array(
                [
                    self.local_balance_weight(pdf, current_log_pdf)
                    for pdf in proposal_log_pdfs
                ]
            )
            lb_weights = lb_weights / np.sum(lb_weights)

            selected_idx = np.random.choice(k, p=lb_weights)
            selected_x = proposals[selected_idx]
            selected_log_pdf = proposal_log_pdfs[selected_idx]

            auxiliary_x = current_x + np.random.randn() * proposal_std
            auxiliary_log_pdf = self.log_pdf_func(auxiliary_x)

            backup_weights = lb_weights.copy()
            backup_weights[selected_idx] = 0
            if np.sum(backup_weights) > 0:
                backup_weights = backup_weights / np.sum(backup_weights)
                backup_idx = np.random.choice(k, p=backup_weights)
            else:
                backup_idx = selected_idx

            backup_x = proposals[backup_idx]
            backup_log_pdf = proposal_log_pdfs[backup_idx]

            log_accept_ratio = (
                selected_log_pdf + backup_log_pdf - current_log_pdf - auxiliary_log_pdf
            )

            if np.log(np.random.rand()) < log_accept_ratio:
                current_x = selected_x
                current_log_pdf = selected_log_pdf
                if i >= burn_in:
                    accepted += 1

            if i >= burn_in:
                samples[i - burn_in] = current_x

        return samples, accepted / n_samples


class ParallelMultiChain:
    """并行多链MCMC - 利用多核CPU并行运行多个链

    不同于单链MTM的"步内并行"，这是"链间并行"
    优点：无通信开销，易于实现
    缺点：无法共享信息减少burn-in
    """

    def __init__(self, sampler_class, n_chains=4, **sampler_kwargs):
        self.sampler_class = sampler_class
        self.n_chains = n_chains
        self.sampler_kwargs = sampler_kwargs

    def sample(self, n_samples_per_chain, burn_in=1000):
        """并行采样"""
        total_samples = n_samples_per_chain * self.n_chains
        all_samples = np.zeros(total_samples)

        for chain_id in range(self.n_chains):
            sampler = self.sampler_class(**self.sampler_kwargs)
            samples, _ = sampler.sample(n_samples_per_chain, burn_in=burn_in)
            all_samples[
                chain_id * n_samples_per_chain : (chain_id + 1) * n_samples_per_chain
            ] = samples

        return all_samples, self.n_chains


def compute_autocorrelation(samples, max_lag=50):
    """计算自相关函数"""
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
    """计算积分自相关时间 (IAT)"""
    n = len(acf)
    for i in range(1, n):
        if acf[i] < threshold:
            return i
    return n


def compute_geweke_diagnostic(samples, frac1=0.1, frac2=0.5):
    """Geweke收敛诊断 - 比较链前后部分的均值

    返回: z-score, |z| < 1.96 表示收敛
    """
    n = len(samples)
    samples1 = samples[: int(n * frac1)]
    samples2 = samples[int(n * (1 - frac2)) :]

    mean1, var1 = np.mean(samples1), np.var(samples1)
    mean2, var2 = np.mean(samples2), np.var(samples2)

    z_score = (mean1 - mean2) / np.sqrt(var1 / len(samples1) + var2 / len(samples2))
    return z_score


def run_advanced_comparison():
    """高级对比实验：包含LB-MTM和多链并行"""
    S0, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
    n_samples = 20000

    bs = BlackScholesModel(S0, K, T, r, sigma)
    analytical_price = bs.call_price_analytical()

    print("=" * 70)
    print("Advanced MCMC Comparison: RWMH vs MTM vs LB-MTM vs Parallel")
    print("=" * 70)
    print("Analytical Price: %.6f" % analytical_price)
    print("=" * 70)

    print("\n>>> Running RWMH...")
    rwmh = RandomWalkMetropolis(bs.log_target, proposal_std=0.3)
    start = time.time()
    rwmh_samples, rwmh_acc = rwmh.sample(n_samples, burn_in=n_samples // 4)
    rwmh_time = time.time() - start
    rwmh_prices = np.exp(-r * T) * np.maximum(np.exp(rwmh_samples) - K, 0)
    rwmh_acf = compute_autocorrelation(rwmh_prices)
    rwmh_iat = compute_integrated_autocorrelation_time(rwmh_acf)
    rwmh_ess = n_samples / rwmh_iat
    rwmh_geweke = compute_geweke_diagnostic(rwmh_prices)
    print(
        "    Time: %.2fs, IAT: %.1f, ESS: %.0f, Geweke: %.2f"
        % (rwmh_time, rwmh_iat, rwmh_ess, rwmh_geweke)
    )

    print("\n>>> Running MTM-K4...")
    mtm = MultipleTryMetropolis(bs.log_target, k_proposals=4, proposal_std=0.3)
    start = time.time()
    mtm_samples, mtm_acc = mtm.sample(n_samples, burn_in=n_samples // 4)
    mtm_time = time.time() - start
    mtm_prices = np.exp(-r * T) * np.maximum(np.exp(mtm_samples) - K, 0)
    mtm_acf = compute_autocorrelation(mtm_prices)
    mtm_iat = compute_integrated_autocorrelation_time(mtm_acf)
    mtm_ess = n_samples / mtm_iat
    mtm_geweke = compute_geweke_diagnostic(mtm_prices)
    print(
        "    Time: %.2fs, IAT: %.1f, ESS: %.0f, Geweke: %.2f"
        % (mtm_time, mtm_iat, mtm_ess, mtm_geweke)
    )

    print("\n>>> Running LB-MTM (Locally Balanced)...")
    lb_mtm = LocallyBalancedMTM(bs.log_target, k_proposals=4, proposal_std=0.3, tau=1.0)
    start = time.time()
    lb_samples, lb_acc = lb_mtm.sample(n_samples, burn_in=n_samples // 4)
    lb_time = time.time() - start
    lb_prices = np.exp(-r * T) * np.maximum(np.exp(lb_samples) - K, 0)
    lb_acf = compute_autocorrelation(lb_prices)
    lb_iat = compute_integrated_autocorrelation_time(lb_acf)
    lb_ess = n_samples / lb_iat
    lb_geweke = compute_geweke_diagnostic(lb_prices)
    print(
        "    Time: %.2fs, IAT: %.1f, ESS: %.0f, Geweke: %.2f"
        % (lb_time, lb_iat, lb_ess, lb_geweke)
    )

    print("\n>>> Running Parallel MTM (4 chains)...")
    pmc = ParallelMultiChain(
        MultipleTryMetropolis,
        n_chains=4,
        log_pdf_func=bs.log_target,
        k_proposals=4,
        proposal_std=0.3,
    )
    start = time.time()
    pmc_samples, _ = pmc.sample(n_samples // 4, burn_in=n_samples // 10)
    pmc_time = time.time() - start
    pmc_prices = np.exp(-r * T) * np.maximum(np.exp(pmc_samples) - K, 0)
    pmc_acf = compute_autocorrelation(pmc_prices)
    pmc_iat = compute_integrated_autocorrelation_time(pmc_acf)
    pmc_ess = len(pmc_samples) / pmc_iat
    pmc_geweke = compute_geweke_diagnostic(pmc_prices)
    print(
        "    Time: %.2fs, IAT: %.1f, ESS: %.0f, Geweke: %.2f"
        % (pmc_time, pmc_iat, pmc_ess, pmc_geweke)
    )

    print("\n" + "=" * 70)
    print("Summary:")
    print("-" * 70)
    print("%-15s %8s %8s %8s %10s" % ("Algorithm", "Time(s)", "IAT", "ESS", "Geweke"))
    print("-" * 70)
    print(
        "%-15s %8.2f %8.1f %8.0f %10.2f"
        % ("RWMH", rwmh_time, rwmh_iat, rwmh_ess, rwmh_geweke)
    )
    print(
        "%-15s %8.2f %8.1f %8.0f %10.2f"
        % ("MTM-K4", mtm_time, mtm_iat, mtm_ess, mtm_geweke)
    )
    print(
        "%-15s %8.2f %8.1f %8.0f %10.2f"
        % ("LB-MTM", lb_time, lb_iat, lb_ess, lb_geweke)
    )
    print(
        "%-15s %8.2f %8.1f %8.0f %10.2f"
        % ("Parallel-MTM", pmc_time, pmc_iat, pmc_ess, pmc_geweke)
    )
    print("-" * 70)
    print("Note: Geweke |z| < 1.96 indicates convergence")
    print("=" * 70)


def explain_algorithms():
    """解释各种算法的特点"""
    print("""
============================================================
                    算法解释
============================================================

1. RWMH (Random Walk Metropolis-Hastings)
   - 最基础的MCMC算法
   - 每次产生1个候选样本
   - 优点：简单，内存需求低
   - 缺点：高维问题收敛慢

2. MTM (Multiple-Try Metropolis)
   - 每次产生K个候选样本
   - 根据权重选择最优候选
   - 优点：更高接受率，降低样本相关性
   - 缺点：计算量增加O(K)

3. LB-MTM (Locally Balanced MTM)
   - 改进版MTM，使用局部平衡权重
   - 优点：收敛更快，特别适合高维问题
   - 论文：JMLR 2024 - Improving MTM with Local Balancing

4. Parallel Multi-Chain
   - 并行运行多个独立MCMC链
   - 优点：无通信开销，易于实现
   - 缺点：无法共享信息

============================================================
""")


if __name__ == "__main__":
    np.random.seed(42)
    explain_algorithms()
    run_advanced_comparison()
