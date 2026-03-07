#!/usr/bin/env python3
"""
优化功能演示

展示优化后的MCMC项目功能：
1. 向量化算法性能
2. 高级诊断工具
3. 配置管理系统
4. 实验自动化
"""

import numpy as np
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def demo_vectorized_algorithms():
    """演示向量化算法"""
    print("=" * 70)
    print("向量化算法演示")
    print("=" * 70)
    
    try:
        from mcmc_vectorized import (
            VectorizedBlackScholesModel,
            VectorizedRandomWalkMetropolis,
            VectorizedMultipleTryMetropolis,
            run_vectorized_comparison
        )
        
        # 创建模型
        bs = VectorizedBlackScholesModel(S0=100, K=100, T=1, r=0.05, sigma=0.2)
        analytical_price = bs.call_price_analytical()
        print(f"Black-Scholes模型已创建")
        print(f"解析解价格: {analytical_price:.6f}")
        
        # 测试向量化log-PDF
        print("\n测试向量化log-PDF计算:")
        test_points = np.array([3.5, 4.0, 4.5, 5.0])
        log_probs = bs.log_pdf(test_points)
        print(f"  输入: {test_points}")
        print(f"  输出: {log_probs}")
        
        # 运行小型性能比较
        print("\n运行小型性能比较 (n_samples=5000)...")
        results = run_vectorized_comparison.__wrapped__()  # 调用原始函数
        
        return True
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保已安装所需依赖")
        return False
    except Exception as e:
        print(f"运行错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_diagnostics():
    """演示诊断工具"""
    print("\n" + "=" * 70)
    print("诊断工具演示")
    print("=" * 70)
    
    try:
        from diagnostics import (
            compute_acf,
            compute_iat_windowed,
            compute_ess,
            compute_geweke,
            plot_convergence_diagnostics
        )
        
        # 生成示例数据
        np.random.seed(42)
        n_samples = 2000
        
        # 收敛的链
        converged_chain = np.random.normal(0, 1, n_samples)
        
        # 未收敛的链（均值漂移）
        unconverged_chain = np.concatenate([
            np.random.normal(2, 1, n_samples // 2),
            np.random.normal(0, 1, n_samples // 2)
        ])
        
        print("1. 计算自相关函数:")
        acf = compute_acf(converged_chain, max_lag=30)
        print(f"   ACF长度: {len(acf)}")
        print(f"   前5个值: {acf[:5]}")
        
        print("\n2. 计算IAT和ESS:")
        iat = compute_iat_windowed(acf)
        ess = compute_ess(converged_chain, method='windowed')
        print(f"   IAT: {iat:.2f}")
        print(f"   ESS: {ess:.0f} ({ess/n_samples*100:.1f}% of total)")
        
        print("\n3. Geweke收敛诊断:")
        z_score, p_value = compute_geweke(converged_chain)
        print(f"   收敛链: z={z_score:.3f}, p={p_value:.4f}")
        
        z_score2, p_value2 = compute_geweke(unconverged_chain)
        print(f"   未收敛链: z={z_score2:.3f}, p={p_value2:.4f}")
        
        print("\n4. 生成诊断报告:")
        report = plot_convergence_diagnostics(converged_chain, "收敛链示例")
        print(report[:500] + "...")  # 只打印前500字符
        
        return True
        
    except ImportError as e:
        print(f"导入错误: {e}")
        return False
    except Exception as e:
        print(f"运行错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_config_system():
    """演示配置系统"""
    print("\n" + "=" * 70)
    print("配置系统演示")
    print("=" * 70)
    
    try:
        from config import (
            ExperimentConfig,
            AlgorithmType,
            get_default_rwmh_config,
            get_mtm_comparison_configs,
            create_experiment_suite
        )
        
        print("1. 创建默认配置:")
        config = get_default_rwmh_config()
        print(f"   实验名称: {config.name}")
        print(f"   样本数量: {config.n_samples}")
        print(f"   算法类型: {config.algorithm.algorithm_type.value}")
        
        print("\n2. 创建MTM对比实验配置:")
        mtm_configs = get_mtm_comparison_configs()
        for cfg in mtm_configs:
            print(f"   - {cfg.name}: K={cfg.algorithm.k_proposals}")
        
        print("\n3. 创建完整实验套件:")
        suite = create_experiment_suite()
        print(f"   包含 {len(suite)} 个实验:")
        for name in suite.keys():
            print(f"     - {name}")
        
        print("\n4. 配置转换为字典:")
        config_dict = config.to_dict()
        print(f"   配置键: {list(config_dict.keys())}")
        
        # 尝试保存配置（可能因为文件权限失败，但尝试）
        try:
            config.to_yaml("demo_config.yaml")
            print("   YAML配置文件已保存: demo_config.yaml")
            
            # 清理
            if os.path.exists("demo_config.yaml"):
                os.remove("demo_config.yaml")
                
        except Exception as e:
            print(f"   保存配置文件时出错: {e}")
        
        return True
        
    except ImportError as e:
        print(f"导入错误: {e}")
        return False
    except Exception as e:
        print(f"运行错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_experiment_runner():
    """演示实验运行器"""
    print("\n" + "=" * 70)
    print("实验运行器演示")
    print("=" * 70)
    
    try:
        from experiment_runner import quick_benchmark
        
        print("运行快速基准测试...")
        print("注意: 这可能需要几分钟时间，具体取决于系统性能")
        print("按Ctrl+C可以中断测试")
        
        response = input("\n是否继续? (y/n): ").strip().lower()
        if response == 'y':
            quick_benchmark()
            return True
        else:
            print("跳过基准测试")
            return True
            
    except ImportError as e:
        print(f"导入错误: {e}")
        print("实验运行器需要原始算法模块")
        return False
    except KeyboardInterrupt:
        print("\n用户中断")
        return True
    except Exception as e:
        print(f"运行错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主演示函数"""
    print("MCMC-BS项目优化功能演示")
    print("=" * 70)
    
    # 检查Python环境
    print("Python环境检查:")
    print(f"  Python版本: {sys.version.split()[0]}")
    
    try:
        import numpy as np
        print(f"  NumPy版本: {np.__version__}")
    except ImportError:
        print("  错误: NumPy未安装")
        print("  请安装: pip install numpy")
        return
    
    try:
        import scipy
        print(f"  SciPy版本: {scipy.__version__}")
    except ImportError:
        print("  警告: SciPy未安装，部分功能可能受限")
    
    # 运行演示
    success_count = 0
    total_demos = 4
    
    print(f"\n开始运行 {total_demos} 个演示...")
    
    # 演示1: 向量化算法
    if demo_vectorized_algorithms():
        success_count += 1
    
    # 演示2: 诊断工具
    if demo_diagnostics():
        success_count += 1
    
    # 演示3: 配置系统
    if demo_config_system():
        success_count += 1
    
    # 演示4: 实验运行器
    if demo_experiment_runner():
        success_count += 1
    
    # 总结
    print("\n" + "=" * 70)
    print("演示完成总结")
    print("=" * 70)
    print(f"成功运行: {success_count}/{total_demos} 个演示")
    
    if success_count == total_demos:
        print("🎉 所有演示成功完成!")
        print("\n下一步建议:")
        print("1. 运行完整测试: python src/test_vectorized.py")
        print("2. 运行性能对比: python src/experiment_runner.py")
        print("3. 查看优化总结: 阅读 OPTIMIZATION_SUMMARY.md")
    elif success_count >= 2:
        print("✓ 大部分演示成功完成")
        print("\n部分模块可能由于依赖问题未能运行")
        print("请检查错误信息并安装所需依赖")
    else:
        print("⚠️ 只有少数演示成功")
        print("\n请检查:")
        print("1. 依赖是否安装: numpy, scipy, pyyaml")
        print("2. 文件路径是否正确")
        print("3. Python版本是否兼容")
    
    print("\n优化文件清单:")
    print("-" * 40)
    optimized_files = [
        "src/mcmc_vectorized.py",
        "src/diagnostics.py", 
        "src/config.py",
        "src/experiment_runner.py",
        "src/test_vectorized.py",
        "OPTIMIZATION_SUMMARY.md",
        "demo_optimized.py"
    ]
    
    for file in optimized_files:
        if os.path.exists(file):
            print(f"✓ {file}")
        else:
            print(f"✗ {file} (未找到)")
    
    print("\n" + "=" * 70)
    print("感谢使用MCMC-BS项目优化版本!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n意外错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)