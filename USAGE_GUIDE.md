# MCMC-BS项目优化版本使用指南

## 🚀 快速开始

### 1. 环境准备
```bash
# 安装依赖
pip install numpy scipy matplotlib

# 可选：安装高级功能依赖
pip install pyyaml pandas seaborn tqdm
```

### 2. 验证安装
```bash
# 运行演示脚本
python demo_optimized.py
```

### 3. 运行性能测试
```bash
# 运行完整性能对比
python src/experiment_runner.py
```

## 📋 优化功能概览

### 核心优化
- **向量化MTM算法**: 显著提高计算速度
- **高级诊断工具**: 改进收敛性分析
- **配置管理系统**: 简化实验设置
- **实验自动化**: 批量运行和结果收集

### 向后兼容性
- 原始API完全保持不变
- 现有代码无需修改
- 可以逐步迁移到新功能

## 🔧 详细使用说明

### 1. 使用向量化算法

#### 基本用法
```python
from src.mcmc_vectorized import (
    VectorizedBlackScholesModel,
    VectorizedMultipleTryMetropolis
)

# 创建模型
bs = VectorizedBlackScholesModel(S0=100, K=100, T=1, r=0.05, sigma=0.2)

# 创建算法
mtm = VectorizedMultipleTryMetropolis(
    log_pdf_func=bs.log_target,
    k_proposals=4,          # 提案数量
    proposal_std=0.3        # 提案标准差
)

# 采样
samples, accept_rate = mtm.sample(
    n_samples=20000,        # 总样本数
    burn_in=5000,           # 燃烧期
    x0=None                 # 初始值（可选）
)

print(f"接受率: {accept_rate:.3f}")
print(f"样本均值: {np.mean(samples):.6f}")
```

#### 批量处理版本
```python
from src.mcmc_vectorized import BatchVectorizedMTM

# 批量处理算法（适合大样本）
batch_mtm = BatchVectorizedMTM(
    log_pdf_func=bs.log_target,
    k_proposals=8,
    proposal_std=0.3,
    batch_size=100          # 批量大小
)

samples, accept_rate = batch_mtm.sample(n_samples=50000, burn_in=10000)
```

### 2. 使用诊断工具

#### 收敛性分析
```python
from src.diagnostics import (
    compute_acf,
    compute_iat_windowed,
    compute_ess,
    plot_convergence_diagnostics
)

# 计算自相关函数
acf = compute_acf(samples, max_lag=100)

# 计算积分自相关时间
iat = compute_iat_windowed(acf)

# 计算有效样本量
ess = compute_ess(samples, method='windowed')

# 生成完整诊断报告
report = plot_convergence_diagnostics(samples, "算法诊断报告")
print(report)
```

#### 多算法比较
```python
from src.diagnostics import batch_diagnostics, compare_algorithms

# 假设有多个算法的样本
samples_list = [samples1, samples2, samples3]
names = ["RWMH", "MTM-K4", "MTM-K8"]

# 批量诊断
results = batch_diagnostics(samples_list, names)

# 生成比较报告
comparison = compare_algorithms(results)
print(comparison)
```

### 3. 使用配置系统

#### 创建实验配置
```python
from src.config import (
    ExperimentConfig,
    AlgorithmType,
    get_default_rwmh_config,
    get_mtm_comparison_configs
)

# 获取默认配置
config = get_default_rwmh_config()
print(f"实验名称: {config.name}")
print(f"样本数量: {config.n_samples}")

# 获取MTM对比实验配置
mtm_configs = get_mtm_comparison_configs()
for cfg in mtm_configs:
    print(f"{cfg.name}: K={cfg.algorithm.k_proposals}")

# 保存配置到文件
config.to_yaml("my_experiment.yaml")
config.to_json("my_experiment.json")
```

#### 从文件加载配置
```python
from src.config import ExperimentConfig

# 从YAML文件加载
config = ExperimentConfig.from_yaml("my_experiment.yaml")

# 从JSON文件加载
config = ExperimentConfig.from_json("my_experiment.json")

# 使用配置
print(f"模型参数: S0={config.model.S0}, K={config.model.K}")
print(f"算法参数: 类型={config.algorithm.algorithm_type.value}")
```

### 4. 使用实验运行器

#### 自动运行基准测试
```python
from src.experiment_runner import ExperimentRunner

# 创建运行器
runner = ExperimentRunner(output_dir="results")

# 设置模型参数（可选）
runner.set_model_params(S0=105, K=95, sigma=0.25)

# 运行基准测试套件
runner.run_benchmark_suite(n_samples=20000)

# 结果自动保存到 results/ 目录
```

#### 自定义实验
```python
from src.experiment_runner import ExperimentRunner

runner = ExperimentRunner(output_dir="custom_results")

# 运行单个算法
result = runner.run_algorithm(
    algorithm_name="我的MTM算法",
    algorithm_config={
        'type': 'mtm',
        'vectorized': True,
        'k_proposals': 4,
        'proposal_std': 0.3
    },
    n_samples=10000,
    burn_in=2500
)

if result:
    print(f"运行时间: {result.metrics['run_time']:.3f}s")
    print(f"有效样本量: {result.metrics['ess']:.0f}")
```

## 📊 性能优化建议

### 1. 算法选择指南
| 场景 | 推荐算法 | 说明 |
|------|----------|------|
| 快速原型 | RWMH (向量化) | 简单快速，适合初步测试 |
| 中等精度 | MTM-K4 (向量化) | 平衡速度和效果 |
| 高精度 | MTM-K8 (批量) | 高ESS，适合最终结果 |
| 大样本 | BatchVectorizedMTM | 内存优化，适合>50000样本 |

### 2. 参数调优
```python
# 提案标准差调整
# 目标接受率: 0.2-0.4
proposal_std = 0.3  # 初始值

# K值选择
# K=4: 平衡选择
# K=8: 更高ESS
# K>16: 收益递减

# 批量大小
# batch_size=100: 通用设置
# batch_size=500: 大样本优化
# batch_size=50: 内存敏感
```

### 3. 收敛判断标准
- **ESS > 1000**: 基本可靠
- **ESS > 5000**: 良好精度
- **Geweke |z| < 2**: 链已收敛
- **R-hat < 1.1**: 多链收敛

## 🔍 故障排除

### 常见问题

#### 1. 导入错误
```python
# 错误: ModuleNotFoundError
# 解决: 确保src目录在Python路径中
import sys
sys.path.insert(0, '/path/to/project')
```

#### 2. 数值问题
```python
# 错误: NaN或inf值
# 解决: 检查模型参数，确保数值稳定
# 使用向量化版本的log_softmax避免下溢
```

#### 3. 性能问题
```python
# 问题: 运行太慢
# 解决: 
# 1. 使用向量化算法
# 2. 减小K值
# 3. 增加批量大小
# 4. 减少样本数量进行测试
```

#### 4. 内存问题
```python
# 问题: 内存不足
# 解决:
# 1. 使用批量处理算法
# 2. 减少样本数量
# 3. 增加批量大小减少内存碎片
```

### 调试建议
```python
import numpy as np

# 设置随机种子确保可重复性
np.random.seed(42)

# 从小样本开始测试
n_samples = 1000  # 测试用
n_samples = 10000  # 开发用  
n_samples = 50000  # 生产用

# 启用详细输出
import logging
logging.basicConfig(level=logging.INFO)
```

## 📈 示例工作流程

### 工作流程1: 算法开发
```python
# 1. 创建模型
from src.mcmc_vectorized import VectorizedBlackScholesModel
bs = VectorizedBlackScholesModel(S0=100, K=100, T=1, r=0.05, sigma=0.2)

# 2. 测试新算法
from src.mcmc_vectorized import VectorizedMultipleTryMetropolis
mtm = VectorizedMultipleTryMetropolis(bs.log_target, k_proposals=4, proposal_std=0.3)
samples, accept_rate = mtm.sample(n_samples=5000, burn_in=1000)

# 3. 评估性能
from src.diagnostics import plot_convergence_diagnostics
report = plot_convergence_diagnostics(samples, "新算法测试")
print(report)

# 4. 参数调优
# 调整proposal_std直到接受率在0.2-0.4之间
```

### 工作流程2: 实验研究
```python
# 1. 设计实验
from src.config import create_experiment_suite
suite = create_experiment_suite()

# 2. 自动运行实验
from src.experiment_runner import ExperimentRunner
runner = ExperimentRunner(output_dir="study_results")

for name, config in suite.items():
    print(f"运行实验: {name}")
    # 根据配置运行算法...

# 3. 分析结果
import json
import pandas as pd

with open("study_results/experiment_results_*.json", "r") as f:
    results = json.load(f)

# 转换为DataFrame分析
df = pd.DataFrame(results['results'])
print(df[['algorithm', 'run_time', 'ess', 'efficiency']])
```

### 工作流程3: 教学演示
```python
# 1. 运行演示
python demo_optimized.py

# 2. 交互式探索
from src.mcmc_vectorized import run_vectorized_comparison
results = run_vectorized_comparison()

# 3. 可视化结果
import matplotlib.pyplot as plt
# ... 使用matplotlib创建教学图表
```

## 🎯 最佳实践

### 代码质量
1. **使用类型提示**: 提高代码可读性和可维护性
2. **添加文档字符串**: 说明函数用途和参数
3. **错误处理**: 使用try-except处理边界情况
4. **日志记录**: 记录重要事件和调试信息

### 实验可重复性
1. **设置随机种子**: `np.random.seed(42)`
2. **保存配置**: 实验参数保存到文件
3. **记录结果**: 保存实验结果和元数据
4. **版本控制**: 代码和配置使用git管理

### 性能优化
1. **向量化计算**: 使用NumPy向量化操作
2. **避免Python循环**: 特别是在内层循环
3. **内存管理**: 注意大数组的内存使用
4. **批量处理**: 适合大规模计算

## 📚 学习资源

### 项目文档
1. `README.md` - 项目概述和原始文档
2. `OPTIMIZATION_SUMMARY.md` - 优化技术细节
3. `IMPLEMENTATION_SUMMARY.md` - 实施总结
4. 本使用指南

### 代码示例
1. `demo_optimized.py` - 完整功能演示
2. `src/test_vectorized.py` - 测试用例
3. `src/experiment_runner.py` - 实验自动化示例

### 外部资源
1. **NumPy文档**: 向量化编程指南
2. **MCMC理论**: 《Bayesian Data Analysis》
3. **性能优化**: Python性能优化技巧
4. **可视化**: Matplotlib和Seaborn教程

## 🤝 贡献指南

### 报告问题
1. 描述问题和复现步骤
2. 提供错误信息和环境信息
3. 建议可能的解决方案

### 提交改进
1. 从优化分支创建特性分支
2. 添加测试用例
3. 更新文档
4. 提交Pull Request

### 代码规范
1. 遵循现有代码风格
2. 添加类型提示
3. 编写文档字符串
4. 确保向后兼容性

## 📞 支持

### 获取帮助
1. 查看项目文档
2. 运行演示脚本
3. 检查常见问题
4. 提交GitHub Issue

### 进一步学习
1. 阅读源代码注释
2. 修改参数观察效果
3. 实现自己的算法变体
4. 扩展到新应用场景

---

**祝您使用愉快！** 🎉

*MCMC-BS项目优化版本*
*更新于 2024年*