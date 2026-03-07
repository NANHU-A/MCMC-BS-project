#!/usr/bin/env python3
"""
测试向量化MCMC算法的正确性和性能
"""

import numpy as np
import time
from mcmc_vectorized import (
    VectorizedBlackScholesModel,
    VectorizedRandomWalkMetropolis,
    VectorizedMultipleTryMetropolis,
    BatchVectorizedMTM,
    compute_autocorrelation_vectorized,
    compute_iat_windowed
)
from mcmc_optimized import (
    BlackScholesModel,
    RandomWalkMetropolis,
    MultipleTryMetropolis,
    compute_autocorrelation,
    compute_integrated_autocorrelation_time
)

def test_vectorization_support():
    """测试向量化log-PDF计算"""
    print("测试向量化log-PDF计算支持...")
    
    S0, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
    
    # 创建两个版本的模型
    bs_old = BlackScholesModel(S0, K, T, r, sigma)
    bs_new = VectorizedBlackScholesModel(S0, K, T, r, sigma)
    
    # 测试标量输入
    x_scalar = 4.0
    old_scalar = bs_old.log_pdf(x_scalar)
    new_scalar = bs_new.log_pdf(x_scalar)
    
    print(f"标量输入: x={x_scalar}")
    print(f"  原始版本: {old_scalar:.6f}")
    print(f"  向量化版本: {new_scalar:.6f}")
    print(f"  差异: {abs(old_scalar - new_scalar):.10f}")
    
    # 测试数组输入
    x_array = np.array([3.5, 4.0, 4.5, 5.0])
    new_array = bs_new.log_pdf(x_array)
    
    print(f"\n数组输入: x={x_array}")
    print(f"  向量化版本结果: {new_array}")
    
    # 验证一致性：逐个计算与批量计算比较
    manual_results = np.array([bs_old.log_pdf(x) for x in x_array])
    print(f"  逐个计算: {manual_results}")
    print(f"  最大差异: {np.max(np.abs(new_array - manual_results)):.10f}")
    
    if np.allclose(new_array, manual_results, rtol=1e-10):
        print("✓ 向量化计算正确！")
    else:
        print("✗ 向量化计算有误！")
    
    return np.allclose(new_array, manual_results, rtol=1e-10)

def test_algorithm_correctness(n_samples=5000):
    """测试算法正确性（小规模）"""
    print(f"\n测试算法正确性 (n_samples={n_samples})...")
    
    S0, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
    bs = VectorizedBlackScholesModel(S0, K, T, r, sigma)
    analytical_price = bs.call_price_analytical()
    
    # 测试RWMH
    print("\n1. 测试RWMH:")
    rwmh_old = RandomWalkMetropolis(bs.log_target, proposal_std=0.3)
    rwmh_new = VectorizedRandomWalkMetropolis(bs.log_target, proposal_std=0.3)
    
    start = time.time()
    samples_old, accept_old = rwmh_old.sample(n_samples, burn_in=1000)
    time_old = time.time() - start
    
    start = time.time()
    samples_new, accept_new = rwmh_new.sample(n_samples, burn_in=1000)
    time_new = time.time() - start
    
    # 计算期权价格
    prices_old = np.exp(-r * T) * np.maximum(np.exp(samples_old) - K, 0)
    prices_new = np.exp(-r * T) * np.maximum(np.exp(samples_new) - K, 0)
    
    price_old = np.mean(prices_old)
    price_new = np.mean(prices_new)
    
    print(f"  原始RWMH: 时间={time_old:.3f}s, 接受率={accept_old:.3f}, 价格={price_old:.6f}")
    print(f"  向量化RWMH: 时间={time_new:.3f}s, 接受率={accept_new:.3f}, 价格={price_new:.6f}")
    print(f"  价格差异: {abs(price_old - price_new):.6f}")
    
    # 测试MTM-K4
    print("\n2. 测试MTM-K4:")
    mtm_old = MultipleTryMetropolis(bs.log_target, k_proposals=4, proposal_std=0.3)
    mtm_new = VectorizedMultipleTryMetropolis(bs.log_target, k_proposals=4, proposal_std=0.3)
    
    start = time.time()
    samples_old, accept_old = mtm_old.sample(n_samples, burn_in=1000)
    time_old = time.time() - start
    
    start = time.time()
    samples_new, accept_new = mtm_new.sample(n_samples, burn_in=1000)
    time_new = time.time() - start
    
    prices_old = np.exp(-r * T) * np.maximum(np.exp(samples_old) - K, 0)
    prices_new = np.exp(-r * T) * np.maximum(np.exp(samples_new) - K, 0)
    
    price_old = np.mean(prices_old)
    price_new = np.mean(prices_new)
    
    print(f"  原始MTM: 时间={time_old:.3f}s, 接受率={accept_old:.3f}, 价格={price_old:.6f}")
    print(f"  向量化MTM: 时间={time_new:.3f}s, 接受率={accept_new:.3f}, 价格={price_new:.6f}")
    print(f"  价格差异: {abs(price_old - price_new):.6f}")
    
    return True

def performance_comparison(n_samples=20000):
    """性能对比测试"""
    print(f"\n性能对比测试 (n_samples={n_samples})...")
    
    S0, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
    bs = VectorizedBlackScholesModel(S0, K, T, r, sigma)
    analytical_price = bs.call_price_analytical()
    
    algorithms = [
        ("RWMH (原始)", RandomWalkMetropolis(bs.log_target, proposal_std=0.3)),
        ("RWMH (向量化)", VectorizedRandomWalkMetropolis(bs.log_target, proposal_std=0.3)),
        ("MTM-K4 (原始)", MultipleTryMetropolis(bs.log_target, k_proposals=4, proposal_std=0.3)),
        ("MTM-K4 (向量化)", VectorizedMultipleTryMetropolis(bs.log_target, k_proposals=4, proposal_std=0.3)),
        ("MTM-K8 (向量化)", VectorizedMultipleTryMetropolis(bs.log_target, k_proposals=8, proposal_std=0.3)),
        ("批量MTM-K8", BatchVectorizedMTM(bs.log_target, k_proposals=8, proposal_std=0.3, batch_size=100)),
    ]
    
    results = []
    
    for name, algo in algorithms:
        print(f"\n>>> 测试 {name}...")
        
        # 运行算法
        start = time.time()
        samples, accept_rate = algo.sample(n_samples, burn_in=n_samples // 4)
        elapsed = time.time() - start
        
        # 计算期权价格
        prices = np.exp(-r * T) * np.maximum(np.exp(samples) - K, 0)
        price = np.mean(prices)
        error = abs(price - analytical_price)
        
        # 计算统计量
        if "向量化" in name or "批量" in name:
            acf = compute_autocorrelation_vectorized(prices, max_lag=100)
            iat = compute_iat_windowed(acf)
        else:
            acf = compute_autocorrelation(prices, max_lag=100)
            iat = compute_integrated_autocorrelation_time(acf)
        
        ess = n_samples / iat
        efficiency = ess / elapsed if elapsed > 0 else 0
        
        results.append({
            'name': name,
            'time': elapsed,
            'accept_rate': accept_rate,
            'price': price,
            'error': error,
            'iat': iat,
            'ess': ess,
            'efficiency': efficiency
        })
        
        print(f"    时间: {elapsed:.3f}s, 接受率: {accept_rate:.3f}")
        print(f"    价格: {price:.6f}, 误差: {error:.6f}")
        print(f"    IAT: {iat:.2f}, ESS: {ess:.0f}, 效率: {efficiency:.0f} ESS/s")
    
    # 输出对比表格
    print("\n" + "=" * 100)
    print("性能对比汇总")
    print("=" * 100)
    print(f"{'算法':<20} {'时间(s)':<10} {'接受率':<10} {'ESS':<10} {'效率(ESS/s)':<15} {'加速比':<10}")
    print("-" * 100)
    
    # 计算基准（原始RWMH）
    baseline_time = None
    for r in results:
        if r['name'] == "RWMH (原始)":
            baseline_time = r['time']
            break
    
    for r in results:
        speedup = baseline_time / r['time'] if baseline_time and r['time'] > 0 else 0
        print(f"{r['name']:<20} {r['time']:<10.3f} {r['accept_rate']:<10.3f} {r['ess']:<10.0f} {r['efficiency']:<15.0f} {speedup:<10.2f}x")
    
    print("=" * 100)
    
    # 分析性能提升
    print("\n性能提升分析:")
    print("-" * 50)
    
    # 找到对应的算法对
    pairs = [
        ("RWMH (原始)", "RWMH (向量化)"),
        ("MTM-K4 (原始)", "MTM-K4 (向量化)"),
    ]
    
    for old_name, new_name in pairs:
        old_data = next(r for r in results if r['name'] == old_name)
        new_data = next(r for r in results if r['name'] == new_name)
        
        time_improvement = old_data['time'] / new_data['time'] if new_data['time'] > 0 else 0
        eff_improvement = new_data['efficiency'] / old_data['efficiency'] if old_data['efficiency'] > 0 else 0
        
        print(f"{old_name} → {new_name}:")
        print(f"  时间: {old_data['time']:.3f}s → {new_data['time']:.3f}s (提升: {time_improvement:.2f}x)")
        print(f"  效率: {old_data['efficiency']:.0f} → {new_data['efficiency']:.0f} ESS/s (提升: {eff_improvement:.2f}x)")
    
    return results

def test_memory_usage():
    """测试内存使用情况"""
    print("\n测试内存使用情况...")
    
    import sys
    
    S0, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
    bs = VectorizedBlackScholesModel(S0, K, T, r, sigma)
    
    # 测试不同样本大小的内存使用
    sample_sizes = [1000, 5000, 10000, 20000]
    
    print(f"{'样本数量':<10} {'内存估算(MB)':<15} {'说明':<30}")
    print("-" * 60)
    
    for n in sample_sizes:
        # 估算内存使用
        # 样本数组: n * 8 bytes (float64)
        # 随机数数组: (n + burn_in) * k * 8 bytes
        k = 4
        burn_in = n // 4
        total_iter = n + burn_in
        
        samples_mem = n * 8 / (1024**2)  # MB
        rand_mem = total_iter * k * 8 / (1024**2)  # MB
        total_mem = samples_mem + rand_mem
        
        print(f"{n:<10} {total_mem:<15.3f} {'MTM-K4算法估计值':<30}")
    
    print("\n说明:")
    print("1. 向量化算法通过预生成随机数减少函数调用")
    print("2. 内存使用与K值成正比，但通常可接受")
    print("3. 对于超大样本，建议使用批量处理或在线统计")

def main():
    """主测试函数"""
    print("=" * 70)
    print("向量化MCMC算法测试套件")
    print("=" * 70)
    
    np.random.seed(42)
    
    # 运行测试
    test_vectorization_support()
    test_algorithm_correctness(n_samples=3000)
    results = performance_comparison(n_samples=10000)  # 使用较小样本以快速测试
    test_memory_usage()
    
    print("\n" + "=" * 70)
    print("测试完成!")
    print("=" * 70)

if __name__ == "__main__":
    main()