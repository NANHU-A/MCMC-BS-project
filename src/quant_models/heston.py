"""
Heston随机波动率模型
用于量化金融中的期权定价和波动率建模
"""

import numpy as np
from scipy.stats import norm
from scipy.optimize import minimize
import warnings

warnings.filterwarnings("ignore")


class HestonModel:
    """Heston随机波动率模型

    模型方程:
    dS_t = μS_t dt + √v_t S_t dW_t^1
    dv_t = κ(θ - v_t) dt + ξ√v_t dW_t^2
    dW_t^1 dW_t^2 = ρ dt

    参数:
    - v0: 初始方差
    - theta: 长期方差
    - kappa: 方差回复速度
    - xi: 波动率的波动率
    - rho: 两个布朗运动的相关系数
    """

    def __init__(
        self, S0=100.0, v0=0.04, theta=0.04, kappa=1.0, xi=0.3, rho=-0.7, r=0.05
    ):
        """
        初始化Heston模型参数

        Args:
            S0: 初始资产价格
            v0: 初始方差
            theta: 长期方差均值
            kappa: 方差回复速度
            xi: 波动率的波动率 (vol of vol)
            rho: 资产价格与方差的相关系数
            r: 无风险利率
        """
        self.S0 = S0
        self.v0 = v0
        self.theta = theta
        self.kappa = kappa
        self.xi = xi
        self.rho = rho
        self.r = r

        # 参数约束检查
        self._validate_parameters()

    def _validate_parameters(self):
        """验证参数满足Heston模型约束"""
        assert self.v0 > 0, "初始方差v0必须为正"
        assert self.theta > 0, "长期方差theta必须为正"
        assert self.kappa > 0, "回复速度kappa必须为正"
        assert self.xi > 0, "波动率的波动率xi必须为正"
        assert -1 <= self.rho <= 1, "相关系数rho必须在[-1, 1]范围内"

        # Feller条件: 2*kappa*theta > xi^2 确保方差保持为正
        feller_condition = 2 * self.kappa * self.theta - self.xi**2
        if feller_condition <= 0:
            warnings.warn(
                f"Feller条件不满足: 2*kappa*theta - xi^2 = {feller_condition:.4f} <= 0"
            )

    def simulate_path(self, T=1.0, n_steps=252, n_paths=10000):
        """
        模拟Heston模型路径 (欧拉离散化)

        Args:
            T: 时间期限
            n_steps: 时间步数
            n_paths: 模拟路径数

        Returns:
            S_t: 资产价格路径 (n_paths × (n_steps+1))
            v_t: 方差路径 (n_paths × (n_steps+1))
        """
        dt = T / n_steps

        # 初始化数组
        S_t = np.zeros((n_paths, n_steps + 1))
        v_t = np.zeros((n_paths, n_steps + 1))

        S_t[:, 0] = self.S0
        v_t[:, 0] = self.v0

        # 生成相关布朗运动
        for t in range(n_steps):
            # 生成相关标准正态随机变量
            Z1 = np.random.randn(n_paths)
            Z2 = self.rho * Z1 + np.sqrt(1 - self.rho**2) * np.random.randn(n_paths)

            # 确保方差非负 (反射边界)
            v_prev = v_t[:, t]
            sqrt_v = np.sqrt(np.maximum(v_prev, 1e-10))

            # 更新方差
            v_next = (
                v_prev
                + self.kappa * (self.theta - v_prev) * dt
                + self.xi * sqrt_v * np.sqrt(dt) * Z2
            )
            v_t[:, t + 1] = np.maximum(v_next, 1e-10)  # 反射边界

            # 更新资产价格
            S_t[:, t + 1] = S_t[:, t] * np.exp(
                (self.r - 0.5 * v_prev) * dt + sqrt_v * np.sqrt(dt) * Z1
            )

        return S_t, v_t

    def call_price_mc(self, K, T=1.0, n_steps=252, n_paths=50000):
        """
        蒙特卡洛法计算欧式看涨期权价格

        Args:
            K: 行权价
            T: 到期时间
            n_steps: 时间步数
            n_paths: 模拟路径数

        Returns:
            price: 期权价格
            std_err: 标准误差
        """
        S_T, _ = self.simulate_path(T, n_steps, n_paths)
        S_T_final = S_T[:, -1]

        # 计算收益
        payoffs = np.maximum(S_T_final - K, 0)
        price = np.exp(-self.r * T) * np.mean(payoffs)
        std_err = np.exp(-self.r * T) * np.std(payoffs) / np.sqrt(n_paths)

        return price, std_err

    def log_likelihood(self, price_data, vol_data):
        """
        计算给定价格和波动率数据的对数似然函数
        用于MCMC参数估计

        Args:
            price_data: 价格时间序列
            vol_data: 波动率时间序列

        Returns:
            log_likelihood: 对数似然值
        """
        # 简化版本 - 实际应基于Heston模型的转移密度
        # 这里使用近似高斯似然
        n = len(price_data) - 1

        if n <= 1:
            return -np.inf

        # 计算对数收益
        returns = np.diff(np.log(price_data))
        vol_values = vol_data[:-1]  # 与收益对应

        # 基于条件正态假设的似然
        # 假设: returns ~ N((r - v/2)*dt, v*dt)
        dt = 1.0 / 252  # 假设日度数据

        # 预测收益
        expected_returns = (self.r - 0.5 * vol_values) * dt

        # 对数似然
        log_likelihood = (
            -0.5 * n * np.log(2 * np.pi * dt)
            - 0.5 * np.sum(np.log(vol_values))
            - 0.5 * np.sum((returns - expected_returns) ** 2 / (vol_values * dt))
        )

        return log_likelihood

    def calibrate_to_market(self, market_prices, strikes, T, method="least_squares"):
        """
        校准模型参数使其匹配市场价格

        Args:
            market_prices: 市场价格列表
            strikes: 行权价列表
            T: 到期时间
            method: 校准方法 ('least_squares' 或 'mcmc')

        Returns:
            calibrated_params: 校准后的参数
        """
        if method == "least_squares":
            return self._calibrate_least_squares(market_prices, strikes, T)
        elif method == "mcmc":
            return self._calibrate_mcmc(market_prices, strikes, T)
        else:
            raise ValueError(f"未知校准方法: {method}")

    def _calibrate_least_squares(self, market_prices, strikes, T):
        """最小二乘法校准"""

        def objective(params):
            v0, theta, kappa, xi, rho = params
            model = HestonModel(self.S0, v0, theta, kappa, xi, rho, self.r)

            errors = []
            for K, market_price in zip(strikes, market_prices):
                model_price, _ = model.call_price_mc(K, T, n_paths=10000)
                errors.append(model_price - market_price)

            return np.sum(np.array(errors) ** 2)

        # 初始猜测
        x0 = [self.v0, self.theta, self.kappa, self.xi, self.rho]

        # 参数边界
        bounds = [
            (1e-4, 1.0),  # v0
            (1e-4, 1.0),  # theta
            (0.1, 10.0),  # kappa
            (0.01, 1.0),  # xi
            (-0.99, 0.99),  # rho
        ]

        result = minimize(objective, x0, bounds=bounds, method="L-BFGS-B")

        if result.success:
            self.v0, self.theta, self.kappa, self.xi, self.rho = result.x
            print(f"校准成功! MSE: {result.fun:.6f}")
            print(
                f"校准后参数: v0={self.v0:.4f}, theta={self.theta:.4f}, "
                f"kappa={self.kappa:.4f}, xi={self.xi:.4f}, rho={self.rho:.4f}"
            )
        else:
            print(f"校准失败: {result.message}")

        return result.x

    def _calibrate_mcmc(self, market_prices, strikes, T):
        """MCMC法校准 - 返回后验分布"""
        # 这里返回简化版本，实际应实现完整MCMC
        print("MCMC校准将在完整版本中实现")
        return [self.v0, self.theta, self.kappa, self.xi, self.rho]

    def get_implied_volatility(self, market_price, K, T=1.0, method="bisection"):
        """
        计算隐含波动率

        Args:
            market_price: 市场价格
            K: 行权价
            T: 到期时间
            method: 计算方法 ('bisection' 或 'newton')

        Returns:
            implied_vol: 隐含波动率
        """
        if method == "bisection":
            return self._implied_vol_bisection(market_price, K, T)
        else:
            return self._implied_vol_newton(market_price, K, T)

    def _implied_vol_bisection(self, market_price, K, T, tol=1e-6, max_iter=100):
        """二分法计算隐含波动率"""

        # 简化为Black-Scholes隐含波动率
        def bs_price(sigma):
            d1 = (np.log(self.S0 / K) + (self.r + 0.5 * sigma**2) * T) / (
                sigma * np.sqrt(T)
            )
            d2 = d1 - sigma * np.sqrt(T)
            return self.S0 * norm.cdf(d1) - K * np.exp(-self.r * T) * norm.cdf(d2)

        # 二分法搜索
        low, high = 0.001, 5.0

        for i in range(max_iter):
            mid = (low + high) / 2
            price_mid = bs_price(mid)

            if abs(price_mid - market_price) < tol:
                return mid

            if price_mid < market_price:
                low = mid
            else:
                high = mid

        return (low + high) / 2


class HestonMCMC:
    """Heston模型的MCMC参数估计"""

    def __init__(self, price_data, dt=1 / 252):
        """
        初始化Heston MCMC估计器

        Args:
            price_data: 价格时间序列
            dt: 时间间隔 (年化)
        """
        self.price_data = price_data
        self.dt = dt
        self.log_returns = np.diff(np.log(price_data))
        self.n_obs = len(self.log_returns)

    def prior_log_pdf(self, params):
        """
        先验分布的对数密度

        Args:
            params: [kappa, theta, xi, rho, v0]

        Returns:
            log_prior: 先验对数密度
        """
        kappa, theta, xi, rho, v0 = params

        # 独立先验
        log_prior = 0.0

        # kappa ~ Gamma(2, 0.5)
        if kappa > 0:
            log_prior += (2 - 1) * np.log(kappa) - kappa / 0.5
        else:
            return -np.inf

        # theta ~ Gamma(1, 0.04)
        if theta > 0:
            log_prior += (1 - 1) * np.log(theta) - theta / 0.04
        else:
            return -np.inf

        # xi ~ Gamma(1, 0.3)
        if xi > 0:
            log_prior += (1 - 1) * np.log(xi) - xi / 0.3
        else:
            return -np.inf

        # rho ~ Uniform(-1, 1)
        if -1 <= rho <= 1:
            log_prior += np.log(0.5)  # 1/(1-(-1)) = 0.5
        else:
            return -np.inf

        # v0 ~ Gamma(1, 0.04)
        if v0 > 0:
            log_prior += (1 - 1) * np.log(v0) - v0 / 0.04
        else:
            return -np.inf

        return log_prior

    def likelihood_log_pdf(self, params):
        """
        似然函数的对数密度 (近似)

        基于Euler离散化的Heston模型
        """
        kappa, theta, xi, rho, v0 = params

        # 简化的似然函数 - 实际应更复杂
        # 这里使用基于Euler近似的条件正态似然

        v = np.zeros(self.n_obs + 1)
        v[0] = v0

        log_likelihood = 0.0

        for t in range(self.n_obs):
            # 预测方差
            v_pred = v[t] + kappa * (theta - v[t]) * self.dt

            # 方差过程的对数似然 (近似)
            log_likelihood += -0.5 * np.log(2 * np.pi * xi**2 * v[t] * self.dt)

            # 价格过程的对数似然
            # 假设: log_return ~ N((r - v/2)*dt, v*dt)
            mu = (0.05 - 0.5 * v[t]) * self.dt  # 假设r=0.05
            sigma2 = v[t] * self.dt

            log_likelihood += (
                -0.5 * np.log(2 * np.pi * sigma2)
                - 0.5 * (self.log_returns[t] - mu) ** 2 / sigma2
            )

            # 更新方差 (简化)
            v[t + 1] = max(v_pred, 1e-10)

        return log_likelihood

    def posterior_log_pdf(self, params):
        """后验分布的对数密度"""
        log_prior = self.prior_log_pdf(params)
        if not np.isfinite(log_prior):
            return -np.inf

        log_likelihood = self.likelihood_log_pdf(params)

        return log_prior + log_likelihood

    def estimate(self, n_samples=20000, burn_in=5000):
        """
        使用MCMC估计参数

        Args:
            n_samples: MCMC样本数
            burn_in: burn-in期

        Returns:
            samples: 参数样本
            acceptance_rate: 接受率
        """
        # 初始值
        initial_params = [1.0, 0.04, 0.3, -0.7, 0.04]

        # 使用Random Walk Metropolis
        n_params = len(initial_params)
        samples = np.zeros((n_samples, n_params))
        current = np.array(initial_params)
        current_log_pdf = self.posterior_log_pdf(current)

        accepted = 0
        proposal_std = np.array([0.1, 0.01, 0.05, 0.1, 0.01])  # 提案分布标准差

        for i in range(n_samples + burn_in):
            # 提议新参数
            proposal = current + proposal_std * np.random.randn(n_params)

            # 确保参数在合理范围内
            proposal[0] = max(proposal[0], 0.01)  # kappa
            proposal[1] = max(proposal[1], 0.001)  # theta
            proposal[2] = max(proposal[2], 0.01)  # xi
            proposal[3] = max(min(proposal[3], 0.99), -0.99)  # rho
            proposal[4] = max(proposal[4], 0.001)  # v0

            proposal_log_pdf = self.posterior_log_pdf(proposal)

            # Metropolis接受概率
            log_alpha = proposal_log_pdf - current_log_pdf

            if np.log(np.random.rand()) < log_alpha:
                current = proposal
                current_log_pdf = proposal_log_pdf
                if i >= burn_in:
                    accepted += 1

            if i >= burn_in:
                samples[i - burn_in] = current

        acceptance_rate = accepted / n_samples

        return samples, acceptance_rate
