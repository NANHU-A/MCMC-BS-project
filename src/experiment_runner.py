"""
实验运行器

自动化运行MCMC实验，比较不同算法的性能
支持批量运行、结果收集和性能报告
"""

import numpy as np
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

# 导入算法模块
try:
    from mcmc_optimized import (
        BlackScholesModel,
        RandomWalkMetropolis,
        MultipleTryMetropolis,
        compute_autocorrelation,
        compute_integrated_autocorrelation_time
    )
    OLD_ALGOS_AVAILABLE = True
except ImportError:
    OLD_ALGOS_AVAILABLE = False
    print("警告: 无法导入原始算法模块")

try:
    from mcmc_vectorized import (
        VectorizedBlackScholesModel,
        VectorizedRandomWalkMetropolis,
        VectorizedMultipleTryMetropolis,
        BatchVectorizedMTM,
        compute_autocorrelation_vectorized,
        compute_iat_windowed
    )
    VECTORIZED_ALGOS_AVAILABLE = True
except ImportError:
    VECTORIZED_ALGOS_AVAILABLE = False
    print("警告: 无法导入向量化算法模块")

try:
    from diagnostics import (
        compute_acf,
        compute_iat_windowed as diag_iat_windowed,
        compute_ess,
        compute_geweke
    )
    DIAGNOSTICS_AVAILABLE = True
except ImportError:
    DIAGNOSTICS_AVAILABLE = False
    print("警告: 无法导入诊断工具模块")


class ExperimentResult:
    """实验结果容器"""
    
    def __init__(self, algorithm_name: str, config: Dict):
        self.algorithm_name = algorithm_name
        self.config = config
        self.start_time = None
        self.end_time = None
        self.samples = None
        self.acceptance_rate = 0.0
        self.metrics = {}
    
    def start(self):
        """开始计时"""
        self.start_time = time.time()
    
    def stop(self):
        """停止计时"""
        self.end_time = time.time()
    
    def compute_metrics(self, bs_model, K: float, r: float, T: float):
        """计算性能指标"""
        if self.samples is None:
            return
        
        # 计算运行时间
        self.metrics['run_time'] = self.end_time - self.start_time
        
        # 计算期权价格
        prices = np.exp(-r * T) * np.maximum(np.exp(self.samples) - K, 0)
        price = np.mean(prices)
        analytical_price = bs_model.call_price_analytical()
        
        self.metrics['price'] = price
        self.metrics['analytical_price'] = analytical_price
        self.metrics['price_error'] = abs(price - analytical_price)
        
        # 计算自相关和ESS
        if DIAGNOSTICS_AVAILABLE:
            acf = compute_acf(prices, max_lag=100)
            iat = diag_iat_windowed(acf)
            ess = compute_ess(prices, method='windowed')
            z_score, p_value = compute_geweke(prices)
        else:
            # 使用简单方法
            acf = compute_autocorrelation(prices, max_lag=100)
            iat = compute_integrated_autocorrelation_time(acf)
            ess = len(prices) / iat if iat > 0 else 0
            z_score, p_value = np.nan, np.nan
        
        self.metrics['iat'] = iat
        self.metrics['ess'] = ess
        self.metrics['efficiency'] = ess / self.metrics['run_time'] if self.metrics['run_time'] > 0 else 0
        self.metrics['geweke_z'] = z_score
        self.metrics['geweke_p'] = p_value
        
        # 接受率
        self.metrics['acceptance_rate'] = self.acceptance_rate
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'algorithm': self.algorithm_name,
            'config': self.config,
            'run_time': self.metrics.get('run_time', 0),
            'acceptance_rate': self.metrics.get('acceptance_rate', 0),
            'price': self.metrics.get('price', 0),
            'analytical_price': self.metrics.get('analytical_price', 0),
            'price_error': self.metrics.get('price_error', 0),
            'iat': self.metrics.get('iat', 0),
            'ess': self.metrics.get('ess', 0),
            'efficiency': self.metrics.get('efficiency', 0),
            'geweke_z': self.metrics.get('geweke_z', np.nan),
            'geweke_p': self.metrics.get('geweke_p', np.nan),
            'timestamp': datetime.now().isoformat()
        }


class ExperimentRunner:
    """实验运行器"""
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.results = []
        
        # 默认模型参数
        self.model_params = {
            'S0': 100.0,
            'K': 100.0,
            'T': 1.0,
            'r': 0.05,
            'sigma': 0.2
        }
    
    def set_model_params(self, **kwargs):
        """设置模型参数"""
        self.model_params.update(kwargs)
    
    def run_algorithm(self, algorithm_name: str, algorithm_config: Dict, 
                     n_samples: int = 20000, burn_in: int = 5000) -> ExperimentResult:
        """运行单个算法"""
        print(f"\n运行算法: {algorithm_name}")
        print(f"配置: {algorithm_config}")
        
        # 创建模型
        S0 = self.model_params['S0']
        K = self.model_params['K']
        T = self.model_params['T']
        r = self.model_params['r']
        sigma = self.model_params['sigma']
        
        # 选择模型实现
        if algorithm_config.get('vectorized', False) and VECTORIZED_ALGOS_AVAILABLE:
            bs_model = VectorizedBlackScholesModel(S0, K, T, r, sigma)
        else:
            bs_model = BlackScholesModel(S0, K, T, r, sigma)
        
        # 创建算法实例
        algo_type = algorithm_config.get('type', 'rwmh')
        
        result = ExperimentResult(algorithm_name, algorithm_config)
        result.start()
        
        try:
            if algo_type == 'rwmh':
                # 随机游走Metropolis-Hastings
                if algorithm_config.get('vectorized', False) and VECTORIZED_ALGOS_AVAILABLE:
                    algo = VectorizedRandomWalkMetropolis(
                        bs_model.log_target,
                        proposal_std=algorithm_config.get('proposal_std', 0.3)
                    )
                else:
                    algo = RandomWalkMetropolis(
                        bs_model.log_target,
                        proposal_std=algorithm_config.get('proposal_std', 0.3)
                    )
                
                samples, accept_rate = algo.sample(n_samples, burn_in=burn_in)
            
            elif algo_type == 'mtm':
                # Multiple-Try Metropolis
                k = algorithm_config.get('k_proposals', 4)
                
                if algorithm_config.get('vectorized', False) and VECTORIZED_ALGOS_AVAILABLE:
                    if algorithm_config.get('batch', False):
                        algo = BatchVectorizedMTM(
                            bs_model.log_target,
                            k_proposals=k,
                            proposal_std=algorithm_config.get('proposal_std', 0.3),
                            batch_size=algorithm_config.get('batch_size', 100)
                        )
                    else:
                        algo = VectorizedMultipleTryMetropolis(
                            bs_model.log_target,
                            k_proposals=k,
                            proposal_std=algorithm_config.get('proposal_std', 0.3)
                        )
                else:
                    algo = MultipleTryMetropolis(
                        bs_model.log_target,
                        k_proposals=k,
                        proposal_std=algorithm_config.get('proposal_std', 0.3)
                    )
                
                samples, accept_rate = algo.sample(n_samples, burn_in=burn_in)
            
            else:
                raise ValueError(f"未知算法类型: {algo_type}")
            
            result.samples = samples
            result.acceptance_rate = accept_rate
            result.stop()
            
            # 计算指标
            result.compute_metrics(bs_model, K, r, T)
            
            print(f"  完成! 时间: {result.metrics['run_time']:.3f}s, 接受率: {accept_rate:.3f}")
            print(f"  价格: {result.metrics['price']:.6f}, 误差: {result.metrics['price_error']:.6f}")
            print(f"  IAT: {result.metrics['iat']:.2f}, ESS: {result.metrics['ess']:.0f}")
            
            return result
            
        except Exception as e:
            print(f"  错误: {e}")
            result.stop()
            return None
    
    def run_benchmark_suite(self, n_samples: int = 20000):
        """运行基准测试套件"""
        print("=" * 70)
        print("运行MCMC算法基准测试套件")
        print("=" * 70)
        
        # 算法配置列表
        algorithms = [
            {
                'name': 'RWMH (原始)',
                'config': {'type': 'rwmh', 'vectorized': False, 'proposal_std': 0.3}
            },
            {
                'name': 'RWMH (向量化)',
                'config': {'type': 'rwmh', 'vectorized': True, 'proposal_std': 0.3}
            },
            {
                'name': 'MTM-K4 (原始)',
                'config': {'type': 'mtm', 'vectorized': False, 'k_proposals': 4, 'proposal_std': 0.3}
            },
            {
                'name': 'MTM-K4 (向量化)',
                'config': {'type': 'mtm', 'vectorized': True, 'k_proposals': 4, 'proposal_std': 0.3}
            },
            {
                'name': 'MTM-K8 (向量化)',
                'config': {'type': 'mtm', 'vectorized': True, 'k_proposals': 8, 'proposal_std': 0.3}
            },
            {
                'name': '批量MTM-K8',
                'config': {'type': 'mtm', 'vectorized': True, 'k_proposals': 8, 
                          'proposal_std': 0.3, 'batch': True, 'batch_size': 100}
            }
        ]
        
        # 运行所有算法
        self.results = []
        for algo_spec in algorithms:
            result = self.run_algorithm(
                algo_spec['name'],
                algo_spec['config'],
                n_samples=n_samples,
                burn_in=n_samples // 4
            )
            
            if result:
                self.results.append(result)
        
        # 保存结果
        self.save_results()
        
        # 生成报告
        self.generate_report()
    
    def save_results(self, filename: Optional[str] = None):
        """保存实验结果"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"experiment_results_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # 转换结果为字典
        results_dict = {
            'model_params': self.model_params,
            'results': [r.to_dict() for r in self.results]
        }
        
        # 保存到JSON文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False)
        
        print(f"\n结果已保存到: {filepath}")
        return filepath
    
    def generate_report(self):
        """生成性能报告"""
        if not self.results:
            print("没有实验结果可报告")
            return
        
        print("\n" + "=" * 80)
        print("MCMC算法性能报告")
        print("=" * 80)
        
        # 表头
        print(f"{'算法':<20} {'时间(s)':<10} {'接受率':<10} {'ESS':<10} {'效率(ESS/s)':<15} {'加速比':<10}")
        print("-" * 80)
        
        # 计算基准（第一个RWMH）
        baseline_time = None
        baseline_eff = None
        for result in self.results:
            if "RWMH (原始)" in result.algorithm_name:
                baseline_time = result.metrics['run_time']
                baseline_eff = result.metrics['efficiency']
                break
        
        # 输出结果
        for result in self.results:
            time_val = result.metrics.get('run_time', 0)
            accept_rate = result.metrics.get('acceptance_rate', 0)
            ess = result.metrics.get('ess', 0)
            efficiency = result.metrics.get('efficiency', 0)
            
            # 计算加速比
            if baseline_time and time_val > 0:
                speedup = baseline_time / time_val
            else:
                speedup = 0
            
            print(f"{result.algorithm_name:<20} {time_val:<10.3f} {accept_rate:<10.3f} "
                  f"{ess:<10.0f} {efficiency:<15.0f} {speedup:<10.2f}x")
        
        print("-" * 80)
        
        # 性能提升分析
        if baseline_time:
            print("\n性能提升分析:")
            print("-" * 50)
            
            # 找到关键算法对
            algo_pairs = [
                ("RWMH (原始)", "RWMH (向量化)"),
                ("MTM-K4 (原始)", "MTM-K4 (向量化)"),
            ]
            
            for old_name, new_name in algo_pairs:
                old_result = next((r for r in self.results if old_name in r.algorithm_name), None)
                new_result = next((r for r in self.results if new_name in r.algorithm_name), None)
                
                if old_result and new_result:
                    old_time = old_result.metrics['run_time']
                    new_time = new_result.metrics['run_time']
                    old_eff = old_result.metrics['efficiency']
                    new_eff = new_result.metrics['efficiency']
                    
                    if old_time > 0 and new_time > 0:
                        time_improvement = old_time / new_time
                        eff_improvement = new_eff / old_eff if old_eff > 0 else 0
                        
                        print(f"{old_name} → {new_name}:")
                        print(f"  时间: {old_time:.3f}s → {new_time:.3f}s (提升: {time_improvement:.2f}x)")
                        print(f"  效率: {old_eff:.0f} → {new_eff:.0f} ESS/s (提升: {eff_improvement:.2f}x)")
        
        print("\n收敛诊断:")
        print("-" * 50)
        for result in self.results:
            z_score = result.metrics.get('geweke_z', np.nan)
            if not np.isnan(z_score):
                status = "✓ 收敛" if abs(z_score) < 2 else "✗ 可能未收敛"
                print(f"{result.algorithm_name:<20}: |z|={abs(z_score):.2f} {status}")
        
        print("\n" + "=" * 80)


def quick_benchmark():
    """快速基准测试（用于快速验证）"""
    print("快速基准测试")
    print("=" * 60)
    
    # 创建运行器
    runner = ExperimentRunner(output_dir="quick_results")
    
    # 运行较小的测试
    runner.run_benchmark_suite(n_samples=5000)
    
    print("\n测试完成！")


def main():
    """主函数"""
    print("MCMC实验运行器")
    print("=" * 60)
    
    # 检查模块可用性
    print("模块检查:")
    print(f"  原始算法: {'可用' if OLD_ALGOS_AVAILABLE else '不可用'}")
    print(f"  向量化算法: {'可用' if VECTORIZED_ALGOS_AVAILABLE else '不可用'}")
    print(f"  诊断工具: {'可用' if DIAGNOSTICS_AVAILABLE else '不可用'}")
    
    # 运行基准测试
    if OLD_ALGOS_AVAILABLE:
        print("\n开始运行基准测试...")
        runner = ExperimentRunner()
        runner.run_benchmark_suite(n_samples=10000)  # 使用较小样本以快速运行
    else:
        print("\n错误: 需要原始算法模块才能运行基准测试")
        print("请确保mcmc_optimized.py存在")


if __name__ == "__main__":
    import sys
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)