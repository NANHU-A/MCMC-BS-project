# 🎲 MCMC期权定价 - 小白入门指南

> 这是什么项目？它能帮我理解多提案MCMC算法吗？
> 
> **答：当然可以！** 本指南专门为零基础读者设计，手把手带你入门。

---

## 📖 第一章：什么是期权定价？

### 1.1 生活中的"期权"例子

想象一下：

> 你想买一套房子🏠，现在价格是100万。
> 
> 你和房东签了一个合同：**一年后**，你可以用**100万**的价格买下这套房子。
> 
> 如果一年后房价涨到120万，你会执行合同，省20万！
> 
> 如果一年后房价跌到80万，你可以选择不买，只亏手续费。

这就是**看涨期权(Call Option)**：
- 🎯 权利：一年后可以买
- 💰 定价：现在就要给一笔"定金"（期权费）

### 1.2 如何计算期权价格？

数学上，期权价格 = 📊 **未来收益的期望值**

```
期权价格 = e^(-rT) × E[max(股价 - 行权价, 0)]
```

其中：
- `r` = 无风险利率（银行存款利率）
- `T` = 到期时间
- `E[]` = 期望值

**难点**：我们需要模拟股票价格的随机波动！

---

## 🎲 第二章：蒙特卡洛方法 - 用随机模拟解决问题

### 2.1 蒙特卡洛的基本思想

> **核心思想**：用大量随机样本估算答案

想象你要估算圆形面积：
1. 在正方形里随机撒点
2. 数有多少点落在圆内
3. 圆面积 ≈ (圆内点数/总点数) × 正方形面积

这就是**蒙特卡洛方法**！📍

### 2.2 股票价格模拟

股票价格服从**几何布朗运动**：

```
S_T = S_0 × exp((r - σ²/2)T + σ × W)

其中：
- S_0 = 初始股价 (100元)
- r = 无风险利率 (5%)
- σ = 波动率 (20%)
- W = 随机波动 (标准正态分布)
```

Python实现：
```python
import numpy as np

S0, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
n_samples = 50000

# 模拟n_samples条可能的股价路径
mean = np.log(S0) + (r - 0.5 * sigma**2) * T
std = sigma * np.sqrt(T)
stock_prices = np.random.normal(mean, std, n_samples)

# 计算期权收益
payoffs = np.exp(-r * T) * np.maximum(np.exp(stock_prices) - K, 0)

# 期权价格 = 平均收益
option_price = np.mean(payoffs)
print(f"期权价格: {option_price:.4f}")  # ≈ 10.45
```

### 2.3 蒙特卡洛的优缺点

| 优点 | 缺点 |
|------|------|
| ✅ 简单直观 | ❌ 收敛慢 (∝ 1/√N) |
| ✅ 适合高维问题 | ❌ 样本独立假设 |
| ✅ 并行友好 | ❌ 无解析解时效率低 |

---

## 🔗 第三章：马尔可夫链蒙特卡洛(MCMC)

### 3.1 为什么需要MCMC？

对于**复杂分布**（如贝叶斯后验），我们往往：
- 知道概率密度函数的形式 `π(x) ∝ f(x)`
- 但无法直接从中采样

**MCMC的核心思想**：构建一条马尔可夫链，使其平稳分布 = 目标分布

### 3.2 Metropolis-Hastings算法

最简单的MCMC算法：

```python
def metropolis_hastings(target_pdf, n_samples, proposal_std):
    samples = []
    x = x0  # 初始位置
    
    for i in range(n_samples):
        # 1. 提议新位置 (随机游走)
        x_new = x + np.random.randn() * proposal_std
        
        # 2. 计算接受概率
        alpha = target_pdf(x_new) / target_pdf(x)
        
        # 3. 接受或拒绝
        if np.random.rand() < alpha:
            x = x_new  # 接受
        
        samples.append(x)
    
    return samples
```

**关键点**：
- 📍 只知道 `π(x)` 就可以，不需要归一化常数
- 🔄 样本之间有相关性（这是代价！）
- ⚖️ 满足细致平衡，保证收敛到目标分布

---

## 🚀 第四章：多提案MCMC (MTM)

### 4.1 MTM的核心思想

RWMH每次只产生**1个**候选样本，MTM一次产生**K个**：

```
RWMH:  提议1个 → 选择1个
MTM:   提议K个 → 根据权重选择1个 ← 充分利用信息！
```

### 4.2 为什么要用多个提案？

想象你在黑暗中找出口：

| 方法 | 策略 | 效率 |
|------|------|------|
| RWMH | 每步只探查1个方向 | ⏳ 慢 |
| MTM | 每步探查K个方向，选最优 | ⚡ 快 |

**多提案的优势**：
1. ✅ 更高的接受率
2. ✅ 更低的样本相关性
3. ✅ 更好的收敛性
4. ✅ 天然适合并行计算

### 4.3 MTM算法步骤

```python
def multiple_try_metropolis(target_pdf, K, proposal_std, n_samples):
    x = x0
    samples = []
    
    for i in range(n_samples):
        # 步骤1: 一次生成K个候选样本
        proposals = [x + np.random.randn() * proposal_std for _ in range(K)]
        
        # 步骤2: 计算每个候选的权重
        weights = [target_pdf(p) for p in proposals]
        weights = weights / sum(weights)  # 归一化
        
        # 步骤3: 根据权重选择
        selected_idx = np.random.choice(K, p=weights)
        x_new = proposals[selected_idx]
        
        # 步骤4: 接受-拒绝准则
        if accept_with_probability(x, x_new, selected_idx):
            x = x_new
        
        samples.append(x)
    
    return samples
```

### 4.4 局部平衡MTM (LB-MTM) - 2024最新改进

2024年JMLR最新研究提出**局部平衡权重**：

```python
def local_balance_weight(log_pdf, current_log_pdf, tau=1.0):
    """tau控制探索/利用平衡
    - tau大: 探索性更强
    - tau小: 利用性更强
    """
    return np.exp((log_pdf - current_log_pdf) / tau)
```

**优势**：在高维问题中收敛更快！

---

## 📊 第五章：实验结果解读

### 5.1 评价指标

| 指标 | 含义 | 理想值 |
|------|------|--------|
| **接受率** | 候选被接受的比例 | 23-50% |
| **IAT** (积分自相关时间) | 样本相关程度 | 越小越好 |
| **ESS** (有效样本量) | 实际独立样本数 | ESS = N/IAT |
| **Geweke** | 收敛诊断 | \|z\| < 1.96 |

### 5.2 实验结果

```
======================================================================
算法对比结果
======================================================================
算法            时间(s)    IAT     ESS     Geweke(收敛诊断)
----------------------------------------------------------------------
RWMH             0.86    10.0    2000      -2.90 ❌
MTM-K4           9.19     5.0    4000      -0.08 ✅
LB-MTM           5.48     4.0    5000       0.43 ✅
Parallel-MTM    10.43     5.0    4000      -0.75 ✅
----------------------------------------------------------------------
```

### 5.3 结果解读

| 结论 | 解释 |
|------|------|
| RWMH的Geweke=-2.90 | ❌ 链未收敛，结果不可靠 |
| MTM系列ESS=4000~5000 | ✅ 有效样本量整体高于RWMH |
| MTM接受率更高 | 更好地探索状态空间 |
| 多链并行使ESS相同 | 但可利用多核CPU加速 |

---

## 🛠️ 第六章：运行代码

### 6.1 环境要求

```bash
# 安装Python依赖
pip install numpy scipy matplotlib
```

### 6.2 运行实验

```bash
cd src

# 基础实验
python mcmc_optimized.py

# 高级实验（含LB-MTM）
python mcmc_advanced.py

# 生成图表
python visualization_optimized.py
```

### 6.3 代码结构

```
src/
├── mcmc_option_pricing.py    # 基础实现
├── mcmc_optimized.py         # 优化版本
├── mcmc_advanced.py          # 高级版本（含LB-MTM）
└── visualization_optimized.py # 可视化
```

---

## 🤔 第七章：常见问题

### Q1: MTM比RWMH慢，为什么还要用它？

> A: **时间不是唯一指标！**
> 
> - MTM的ESS（有效样本量）更高
> - 在复杂问题中，RWMH可能永远无法收敛
> - MTM可以并行化，GPU上K=100000都有可能

### Q2: 什么是"IAT"（积分自相关时间）？

> A: 想象你在走路📸拍照：
> - 每步都拍 → 照片相关性100%
> - 每10步拍一张 → 照片相关性低
> 
> IAT就是描述这种"相关程度"的指标，**越小越好**！

### Q3: Geweke诊断是什么？

> A: 比较链**开头10%**和**最后50%**的均值差异
> - |z| < 1.96 → 链已收敛 ✅
> - |z| >= 1.96 → 链未收敛 ❌

### Q4: 如何选择合适的K值？

> A: 经验法则：
> - K=2~4: 性价比最高
> - K>16: 收益递减，计算量翻倍
> - 高维问题: 考虑K>100

---

## 📚 第八章：延伸学习

### 推荐资源

| 资源 | 难度 | 链接 |
|------|------|------|
| Monte Carlo Methods in Financial Engineering | 中级 | Glasserman, Springer |
| Monte Carlo Strategies in Scientific Computing | 高级 | Liu, Springer |
| MTM Local Balancing (JMLR 2024) | 高级 | jmlr.org/papers/v24/22-1351 |

### 进阶方向

1. **GPU加速**：利用CUDA并行 Thousands of proposals
2. **哈密顿蒙特卡洛(HMC)**：利用梯度信息
3. **变分推断**：用神经网络近似后验
4. **贝叶斯金融**：波动率建模、风险管理

---

## 📝 总结

| 概念 | 核心要点 |
|------|----------|
| 期权定价 | 未来收益的期望值 |
| 蒙特卡洛 | 用随机样本估计 |
| MCMC | 构建马尔可夫链采样 |
| RWMH | 每次1个候选 |
| MTM | 每次K个候选，选最优 |
| LB-MTM | 2024改进版，高维更有效 |
| ESS | 有效样本量 = N/IAT |

**记住**：没有最好的算法，只有最适合的算法！🎯

---

*本项目用于本科毕业论文研究，欢迎交流讨论！*
