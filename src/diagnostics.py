"""
高级MCMC诊断工具

本模块提供更准确的收敛诊断和性能评估工具：
1. 窗口化IAT估计（比简单阈值法更稳定）
2. R-hat收敛诊断（Gelman-Rubin统计量）
3. 有效样本量(ESS)计算
4. Geweke收敛诊断
5. 迹图分析
6. 自相关函数(ACF)分析
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
import warnings


def compute_acf(samples: np.ndarray, max_lag: Optional[int] = None) -> np.ndarray:
    """计算自相关函数
    
    参数：
        samples: 样本序列
        max_lag: 最大滞后，默认min(100, len(samples)//4)
    
    返回：
        acf: 自相关函数值数组，acf[0] = 1.0
    """
    n = len(samples)
    if max_lag is None:
        max_lag = min(100, n // 4)
    max_lag = min(max_lag, n - 1)
    
    mean = np.mean(samples)
    var = np.var(samples, ddof=0)
    
    if var == 0:
        return np.ones(max_lag + 1)
    
    acf = np.zeros(max_lag + 1)
    acf[0] = 1.0
    
    # 向量化计算自相关
    for lag in range(1, max_lag + 1):
        acf[lag] = np.sum((samples[lag:] - mean) * (samples[:-lag] - mean)) / ((n - lag) * var)
    
    return acf


def compute_iat_windowed(acf: np.ndarray, window_size: int = 10, threshold: float = 0.05) -> float:
    """窗口化积分自相关时间估计
    
    使用滑动窗口检测自相关衰减，比简单阈值法更稳定
    
    参数：
        acf: 自相关函数
        window_size: 窗口大小
        threshold: 阈值，窗口内所有值小于此阈值时停止
    
    返回：
        iat: 积分自相关时间
    """
    n = len(acf)
    if n < window_size:
        return 1.0
    
    iat = 1.0
    found_cutoff = False
    
    for i in range(1, n - window_size + 1):
        window = acf[i:i + window_size]
        
        # 检查窗口是否低于阈值或出现负相关
        if np.all(np.abs(window) < threshold) or np.any(window < -threshold):
            # 使用到窗口中间位置的和作为IAT估计
            cutoff = i + window_size // 2
            iat = 1 + 2 * np.sum(acf[1:cutoff])
            found_cutoff = True
            break
    
    # 如果没有找到合适的截断点，使用全部ACF
    if not found_cutoff:
        iat = 1 + 2 * np.sum(acf[1:])
    
    return max(iat, 1.0)


def compute_ess(samples: np.ndarray, method: str = 'windowed') -> float:
    """计算有效样本量
    
    参数：
        samples: 样本序列
        method: 计算方法，'windowed'或'simple'
    
    返回：
        ess: 有效样本量
    """
    n = len(samples)
    
    if method == 'simple':
        # 简单阈值法
        acf = compute_acf(samples, max_lag=min(100, n // 4))
        for i in range(1, len(acf)):
            if acf[i] < 0.05:
                iat = 1 + 2 * np.sum(acf[1:i])
                return n / max(iat, 1.0)
        iat = 1 + 2 * np.sum(acf[1:])
        return n / max(iat, 1.0)
    
    elif method == 'windowed':
        # 窗口化方法（默认）
        acf = compute_acf(samples, max_lag=min(200, n // 2))
        iat = compute_iat_windowed(acf)
        return n / iat
    
    else:
        raise ValueError(f"未知的ESS计算方法: {method}")


def compute_rhat(chains: List[np.ndarray]) -> float:
    """计算R-hat统计量（Gelman-Rubin收敛诊断）
    
    参数：
        chains: 多个独立链的样本列表
    
    返回：
        r_hat: R-hat统计量，<1.1表示收敛
    """
    m = len(chains)  # 链的数量
    if m < 2:
        return np.nan
    
    # 每链的样本数量（假设相同）
    n = len(chains[0])
    
    # 计算每链的均值和方差
    chain_means = np.array([np.mean(chain) for chain in chains])
    chain_vars = np.array([np.var(chain, ddof=1) for chain in chains])
    
    # 总体均值
    overall_mean = np.mean(chain_means)
    
    # 链间方差 B/n
    B_over_n = np.var(chain_means, ddof=1) if m > 1 else 0
    
    # 链内平均方差 W
    W = np.mean(chain_vars)
    
    # 估计的边际后验方差
    var_plus = (n - 1) / n * W + B_over_n
    
    # 计算R-hat
    r_hat = np.sqrt(var_plus / W) if W > 0 else np.nan
    
    return r_hat


def compute_geweke(samples: np.ndarray, frac1: float = 0.1, frac2: float = 0.5) -> Tuple[float, float]:
    """Geweke收敛诊断
    
    比较链的前后部分，计算z-score
    
    参数：
        samples: 样本序列
        frac1: 前部分比例（默认10%）
        frac2: 后部分比例（默认50%）
    
    返回：
        z_score: z统计量
        p_value: p值（双侧检验）
    """
    n = len(samples)
    
    if n < 100:
        warnings.warn(f"样本量{n}较小，Geweke诊断可能不可靠")
        return np.nan, np.nan
    
    n1 = int(n * frac1)
    n2 = int(n * frac2)
    
    if n1 < 10 or n2 < 10:
        warnings.warn(f"分段样本量太小（n1={n1}, n2={n2}）")
        return np.nan, np.nan
    
    # 前部分和后部分
    samples1 = samples[:n1]
    samples2 = samples[-n2:]
    
    mean1, var1 = np.mean(samples1), np.var(samples1, ddof=1)
    mean2, var2 = np.mean(samples2), np.var(samples2, ddof=1)
    
    if var1 == 0 or var2 == 0:
        return np.nan, np.nan
    
    # 计算z-score
    se = np.sqrt(var1 / n1 + var2 / n2)
    z_score = (mean1 - mean2) / se if se > 0 else np.nan
    
    # 计算双侧p值
    if not np.isnan(z_score):
        from scipy.stats import norm
        p_value = 2 * (1 - norm.cdf(np.abs(z_score)))
    else:
        p_value = np.nan
    
    return z_score, p_value


def compute_effective_sample_size_multivariate(samples: np.ndarray, method: str = 'multivariate') -> float:
    """多变量有效样本量估计
    
    对于高维问题，计算所有分量的最小ESS
    
    参数：
        samples: 样本矩阵，形状为(n_samples, n_dimensions)
        method: 计算方法
    
    返回：
        min_ess: 所有分量的最小ESS
    """
    if samples.ndim == 1:
        return compute_ess(samples, method='windowed')
    
    n_samples, n_dims = samples.shape
    ess_values = np.zeros(n_dims)
    
    for d in range(n_dims):
        ess_values[d] = compute_ess(samples[:, d], method='windowed')
    
    return np.min(ess_values)


def plot_convergence_diagnostics(samples: np.ndarray, title: str = "收敛诊断"):
    """生成收敛诊断图（简化版，返回文本分析）
    
    在实际应用中，此函数会生成matplotlib图形
    这里返回文本分析结果
    """
    n = len(samples)
    
    # 计算各项诊断统计量
    ess = compute_ess(samples, method='windowed')
    acf = compute_acf(samples, max_lag=min(100, n // 4))
    iat = compute_iat_windowed(acf)
    z_score, p_value = compute_geweke(samples)
    
    analysis = f"""
{'='*60}
收敛诊断报告: {title}
{'='*60}

基本统计:
- 样本数量: {n}
- 样本均值: {np.mean(samples):.6f}
- 样本标准差: {np.std(samples):.6f}
- 接受率: 需要在算法中记录

自相关分析:
- 积分自相关时间(IAT): {iat:.2f}
- 有效样本量(ESS): {ess:.0f} ({ess/n*100:.1f}% of total)
- ESS/秒: 需要运行时间数据

收敛诊断:
- Geweke z-score: {z_score:.3f} {'(收敛)' if abs(z_score) < 2 else '(可能未收敛)'}
- Geweke p-value: {p_value:.4f}

建议:
"""
    
    if ess < 100:
        analysis += "- 警告: ESS < 100，结果可能不可靠\n"
        analysis += "- 建议: 增加样本量或改进算法\n"
    elif ess < 1000:
        analysis += "- ESS在可接受范围，但对于精确估计可能不足\n"
        analysis += "- 建议: 考虑增加样本量\n"
    else:
        analysis += "- ESS良好，结果可靠\n"
    
    if abs(z_score) > 2:
        analysis += "- 警告: Geweke诊断表明可能未收敛\n"
        analysis += "- 建议: 增加燃烧期或检查算法参数\n"
    
    if iat > 50:
        analysis += "- 警告: IAT很高，样本相关性很强\n"
        analysis += "- 建议: 考虑使用多提案算法或调整提案分布\n"
    
    analysis += f"{'='*60}"
    
    return analysis


def batch_diagnostics(samples_list: List[np.ndarray], 
                      names: Optional[List[str]] = None) -> Dict:
    """批量运行诊断，比较多个算法
    
    参数：
        samples_list: 样本列表
        names: 算法名称列表
    
    返回：
        diagnostics_dict: 诊断结果字典
    """
    if names is None:
        names = [f"算法_{i+1}" for i in range(len(samples_list))]
    
    if len(samples_list) != len(names):
        raise ValueError("样本列表和名称列表长度必须相同")
    
    results = {}
    
    for i, (samples, name) in enumerate(zip(samples_list, names)):
        n = len(samples)
        acf = compute_acf(samples, max_lag=min(100, n // 4))
        iat = compute_iat_windowed(acf)
        ess = n / iat
        z_score, p_value = compute_geweke(samples)
        
        results[name] = {
            'n_samples': n,
            'mean': float(np.mean(samples)),
            'std': float(np.std(samples)),
            'iat': float(iat),
            'ess': float(ess),
            'ess_percent': float(ess / n * 100),
            'geweke_z': float(z_score) if not np.isnan(z_score) else None,
            'geweke_p': float(p_value) if not np.isnan(p_value) else None,
            'converged': abs(z_score) < 2 if not np.isnan(z_score) else None
        }
    
    return results


def compare_algorithms(results: Dict) -> str:
    """比较多个算法的诊断结果
    
    参数：
        results: batch_diagnostics的输出
    
    返回：
        comparison: 比较报告
    """
    comparison = f"""
{'='*80}
算法性能比较
{'='*80}
{'算法':<15} {'样本数':<10} {'IAT':<10} {'ESS':<10} {'ESS%':<8} {'Geweke':<10} {'收敛'}
{'-'*80}
"""
    
    for name, stats in results.items():
        geweke_str = f"{stats['geweke_z']:.2f}" if stats['geweke_z'] is not None else "N/A"
        converged_str = "✓" if stats['converged'] else "✗" if stats['converged'] is not None else "?"
        
        comparison += f"{name:<15} {stats['n_samples']:<10} {stats['iat']:<10.2f} "
        comparison += f"{stats['ess']:<10.0f} {stats['ess_percent']:<8.1f} "
        comparison += f"{geweke_str:<10} {converged_str}\n"
    
    # 找出最佳算法
    best_by_ess = max(results.items(), key=lambda x: x[1]['ess'] if not np.isnan(x[1]['ess']) else -np.inf)
    best_by_iat = min(results.items(), key=lambda x: x[1]['iat'] if not np.isnan(x[1]['iat']) else np.inf)
    
    comparison += f"{'-'*80}\n"
    comparison += f"最佳ESS: {best_by_ess[0]} (ESS={best_by_ess[1]['ess']:.0f})\n"
    comparison += f"最佳IAT: {best_by_iat[0]} (IAT={best_by_iat[1]['iat']:.2f})\n"
    comparison += f"{'='*80}"
    
    return comparison


# 示例使用函数
def example_usage():
    """诊断工具使用示例"""
    print("诊断工具使用示例")
    print("=" * 60)
    
    # 生成示例数据
    np.random.seed(42)
    n_samples = 5000
    
    # 创建两个链（模拟收敛和未收敛）
    chain1 = np.random.normal(0, 1, n_samples)  # 收敛链
    chain2 = np.concatenate([
        np.random.normal(2, 1, n_samples // 2),  # 前半部分均值不同
        np.random.normal(0, 1, n_samples // 2)   # 后半部分
    ])  # 未收敛链
    
    # 计算单个链的诊断
    print("\n1. 单个链诊断:")
    analysis1 = plot_convergence_diagnostics(chain1, "收敛链示例")
    print(analysis1)
    
    # 计算R-hat（多链诊断）
    print("\n2. 多链诊断 (R-hat):")
    chains = [chain1, chain1.copy()]  # 两个相同的链
    r_hat = compute_rhat(chains)
    print(f"R-hat (相同链): {r_hat:.4f} {'(<1.1，收敛)' if r_hat < 1.1 else '(≥1.1，可能未收敛)'}")
    
    chains2 = [chain1, chain2]  # 一个收敛一个未收敛
    r_hat2 = compute_rhat(chains2)
    print(f"R-hat (不同链): {r_hat2:.4f} {'(<1.1，收敛)' if r_hat2 < 1.1 else '(≥1.1，可能未收敛)'}")
    
    # 批量诊断
    print("\n3. 批量诊断:")
    samples_list = [chain1, chain2]
    names = ["收敛链", "未收敛链"]
    results = batch_diagnostics(samples_list, names)
    comparison = compare_algorithms(results)
    print(comparison)
    
    print("\n4. ESS计算比较:")
    ess_simple = compute_ess(chain1, method='simple')
    ess_windowed = compute_ess(chain1, method='windowed')
    print(f"简单方法ESS: {ess_simple:.0f}")
    print(f"窗口化方法ESS: {ess_windowed:.0f}")
    print(f"差异: {abs(ess_simple - ess_windowed):.0f} ({abs(ess_simple - ess_windowed)/ess_windowed*100:.1f}%)")


if __name__ == "__main__":
    example_usage()