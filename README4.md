# src 与 figures 逐文件详解

这份文档不是“项目简介”，而是把仓库里的每个核心文件拆开讲清楚：它负责什么、输入是什么、输出是什么、在整个实验链条里站在哪一环。

## 1. 先说整体：这个项目到底怎么跑起来

这个仓库做的事情可以拆成 4 层：

1. **数学模型层**
   - 用 Black-Scholes 模型给出期权价格的解析解。
   - 同时把“期权定价”转成“从目标分布采样”的问题。

2. **采样算法层**
   - 用 `RandomWalkMetropolis` 做单提案采样。
   - 用 `MultipleTryMetropolis` 做多提案采样。
   - 在高级版里再加入局部平衡、多链并行等策略。

3. **评估指标层**
   - 看接受率、运行时间、IAT、ESS。
   - 这些指标用来判断“采样准不准、快不快、样本独不独立”。

4. **可视化层**
   - 把采样轨迹、分布图、自相关图、速度图画出来。
   - 最终保存到 `figures/` 目录。

所以整个项目的逻辑不是“先画图再采样”，而是：

`BlackScholesModel -> MCMC sampler -> metrics -> plotting -> figures`

---

## 2. `src/mcmc_option_pricing.py`：基础实验主文件

这是最核心的基础版实现。你可以把它理解为“第一版完整实验流水线”。

### 2.1 它负责什么

这个文件同时做了三件事：

1. **定义问题本身**
   - 定义 Black-Scholes 模型。
   - 提供期权解析解。
   - 把股票终值的对数价格分布写出来。

2. **定义采样器**
   - 单提案 RWMH。
   - 多提案 MTM。
   - 多链拼接版 ParallelMTM。

3. **定义实验和指标**
   - 运行采样。
   - 把采样结果转成期权价格估计。
   - 计算时间、接受率、ACF、IAT、ESS。

### 2.2 `BlackScholesModel` 在这里干什么

这个类是整个实验的“数学底座”。

#### `__init__(S0, K, T, r, sigma)`
保存 Black-Scholes 的基本参数：
- `S0`：初始股价
- `K`：行权价
- `T`：到期时间
- `r`：无风险利率
- `sigma`：波动率

这些参数决定了后面所有采样和定价都用什么分布。

#### `call_price_analytical()`
返回 Black-Scholes 公式下的解析解。

它的意义不是“用来采样”，而是作为**对照标准**：
- 采样出来的均值靠不靠近它？
- MCMC 的估计误差有多大？

#### `log_price_density(x)` / `log_pdf(x)` / `log_target(x)`
这几个函数都在描述同一个东西：
“终值对数价格 `x = ln(S_T)` 的目标分布”。

- `log_price_density(x)` 返回的是普通密度值。
- `log_pdf(x)` 返回的是对数密度。
- `log_target(x)` 只是把 `log_pdf(x)` 包装成采样器更容易调用的形式。

为什么要用对数密度？
- 数值更稳定。
- 接受率里要算比值，对数形式更方便。

### 2.3 `RandomWalkMetropolis` 在这里干什么

这是最标准的单提案 MCMC。

#### `__init__(target_log_pdf, proposal_std=0.5)`
传入：
- 目标分布的对数密度函数
- 提案分布的标准差

这意味着这个采样器是“通用的”，不是只给 Black-Scholes 用。

#### `sample(n_samples, x0=None, burn_in=1000)`
这是主采样函数。

它的执行顺序是：
1. 设定初始点 `x0`。
2. 每轮从当前点附近随机走一步：`proposal_x = current_x + N(0, proposal_std^2)`。
3. 算接受概率。
4. 根据随机数决定接不接受。
5. 丢掉 burn-in 之前的样本。

输出：
- `samples`：最终保留下来的样本序列。
- `acceptance_rate`：接受率。

它在整个实验里的角色：
- 基准算法。
- 作为 MTM 和高级算法的对照组。

### 2.4 `MultipleTryMetropolis` 在这里干什么

这是多提案版本的核心。

#### 和 RWMH 的区别

RWMH 每步只提 1 个候选；MTM 每步提 `k_proposals` 个候选。

简单说：
- RWMH 是“只看一个备选项”。
- MTM 是“同时看多个备选项，再挑一个更合适的”。

#### `sample()` 的关键步骤

1. 生成 `k` 个 forward proposals。
2. 计算每个 proposal 的对数密度。
3. 按权重挑一个候选。
4. 再生成 backward proposals。
5. 用 forward/backward 的 logsumexp 差值算接受率。

这个设计的意义：
- 它想提高“走对方向”的概率。
- 这样样本相关性通常会下降。
- 但每一步计算也更重，所以时间未必更快。

### 2.5 `ParallelMTM` 在这里干什么

这个类不是标准 MTM 的一步内并行，而是“多条链拼起来”。

它的作用是：
- 把总样本数切成多个链分别跑。
- 最后把各链结果拼接。

它表达的是一种“并行思想”，但它并不是真正的 GPU/多线程并行。

### 2.6 指标函数在这里干什么

#### `compute_autocorrelation(samples, max_lag=50)`
计算样本序列的自相关函数。

它回答的问题是：
“当前样本和前面几个样本有多像？”

如果自相关高，说明样本之间独立性差。

#### `compute_integrated_autocorrelation_time(acf)`
估计积分自相关时间 IAT。

它回答的问题是：
“要把相关样本折算成独立样本，大概要打几折？”

IAT 越小越好。

### 2.7 `run_experiment()` 在这里干什么

这是基础实验的一次完整运行。

它会：
1. 创建 `BlackScholesModel`。
2. 算解析解。
3. 跑 RWMH。
4. 跑 MTM-K2、MTM-K4、MTM-K8。
5. 把采样样本变成期权价格。
6. 计算误差、接受率、时间、IAT、ESS。

所以它是“从模型到结果表”的主入口。

### 2.8 `compare_speedup_vs_k()` 在这里干什么

这是专门看“提案数 K 变化时发生了什么”的实验。

它的重点不是价格，而是：
- K 变大时，时间会怎么变？
- IAT 会怎么变？

这个函数是后面速度曲线图的数值来源之一。

### 2.9 这份文件在项目中的位置

一句话说：

`mcmc_option_pricing.py` 是“基础版实验发动机”。

它把：
- 数学模型
- 采样器
- 指标
- 实验入口

全部放在一个文件里，适合先理解原理。

---

## 3. `src/mcmc_optimized.py`：优化版主实验文件

这个文件是基础版的升级版，目标是把实验跑得更干净、更快、更适合做主结果。

### 3.1 它和基础版的关系

它和 `mcmc_option_pricing.py` 很像，但做了两个核心优化：

1. **预计算**
   - 先把 `log_S0`、`mean`、`std` 算好。
   - 避免每次调用都重复算。

2. **实验组织更清晰**
   - 更偏向“正式出图”和“结果汇总”。

### 3.2 `BlackScholesModel` 的区别

这里多了 `_setup_precomputed()`。

#### `_setup_precomputed()`
预先算好：
- `log_S0`
- `mean`
- `std`

这样后面 `log_pdf(x)` 直接用缓存值，不用反复计算。

这看起来是小优化，但在大量采样时会省很多重复开销。

### 3.3 `RandomWalkMetropolis`

逻辑和基础版一样，仍然是单提案随机游走。

区别主要是：
- 变量转成了更明确的浮点形式。
- 代码更紧凑。
- 更适合大规模实验。

### 3.4 `MultipleTryMetropolis`

仍然是 MTM，但实现更强调数值稳定性。

比如：
- 通过 `forward_weights = exp(forward_log_pdf - max)` 防止指数溢出。
- 通过 `logsumexp()` 来算接受率，避免直接算概率比导致精度问题。

这类细节对 MCMC 很重要，因为采样步数一多，数值问题会放大。

### 3.5 `compute_autocorrelation()` 和 `compute_integrated_autocorrelation_time()`

它们仍然承担和基础版相同的职责：
- ACF 看相关性结构。
- IAT 看“有效独立程度”。

不同的是，优化版后面会被更系统地用于图像生成。

### 3.6 `run_comparison()`

这是优化版的核心实验之一。

它做的是：
- 先跑解析解。
- 再跑 RWMH。
- 再跑 MTM-K2、MTM-K4。
- 输出每种方法的价格、误差、时间、IAT、ESS。

这个函数更像论文里的“主比较表”。

### 3.7 `run_speedup_analysis()`

这是专门研究 K 的函数。

它会先跑 RWMH，作为基准时间和基准 IAT，然后对 K=2、4、8 分别跑 MTM。

它关注两个量：
- `time_speedup = rwmh_time / mtm_time`
- `iat_reduction = rwmh_iat / mtm_iat`

这两个量是“时间效率”和“采样质量提升”的两面。

### 3.8 `run_baseline_comparison()`

这个函数把**普通 Monte Carlo** 和 **MCMC** 放在一起比。

它的意义是告诉读者：
- 对于这个简单的 Black-Scholes 问题，直接 MC 往往更快。
- MCMC 的价值不是在最简单问题上赢速度，而是在复杂目标分布上更有用。

这是一个很重要的“方法边界说明”。

### 3.9 `if __name__ == "__main__"`

这里说明这个文件既可以被导入，也可以单独运行。

单独运行时它会：
- 先跑 baseline 比较。
- 再跑主比较。
- 再跑 speedup 分析。

所以它是整个优化实验的“执行入口”。

---

## 4. `src/mcmc_advanced.py`：高级算法实验文件

这个文件不是基础比较，而是展示“更进一步”的采样设计。

### 4.1 它的定位

它在实验链条里的作用是：
- 证明项目不只会做基础 RWMH/MTM。
- 还会做局部平衡、并行多链、额外收敛诊断。

### 4.2 `BlackScholesModel`

和前两个文件一样，仍然负责 Black-Scholes 目标分布和解析解。

这说明：
- 三个文件虽然算法不同，但实验对象是同一个。
- 这样才能公平比较。

### 4.3 `RandomWalkMetropolis`

这里是标准 RWMH 的高级版实现。

它和前面的区别不在算法本身，而在这份文件被纳入了更完整的比较体系。

### 4.4 `MultipleTryMetropolis`

这里仍然是标准 MTM，多提案、多候选、再做接受拒绝。

它是高级算法对照的基础项。

### 4.5 `LocallyBalancedMTM`

这是这份文件最关键的新东西。

#### 它想解决什么

标准 MTM 虽然能多看几个候选，但权重设计还是比较“普通”。
局部平衡 MTM 想做的是：
- 在探索和利用之间找到更好的平衡。
- 让权重更贴近当前状态附近的局部结构。

#### `local_balance_weight(log_pdf, current_log_pdf)`

这个函数把候选点的 log 密度和当前点比较，再通过温度参数 `tau` 控制权重强弱。

直观理解：
- `tau` 大：更偏探索。
- `tau` 小：更偏利用。

#### `sample()`

这个采样器的流程比标准 MTM 更复杂：
1. 生成多个 proposals。
2. 算局部平衡权重。
3. 按权重选一个候选。
4. 再构造辅助变量。
5. 再算接受率。

它的目标是提高复杂分布下的混合效率。

### 4.6 `ParallelMultiChain`

这不是“一个链里多提案”，而是“多条链并行”。

它的意义：
- 可以把多个独立链跑起来。
- 适合多核 CPU。
- 适合展示工程上的并行思路。

它的局限：
- 链之间不共享信息。
- 不能减少单链 burn-in 的问题。

### 4.7 `compute_geweke_diagnostic()`

这是一个收敛诊断函数。

它做的是：
- 比较链前段均值和后段均值。
- 看两段差异是否足够小。

如果 `|z| < 1.96`，通常表示链前后没有显著差异，收敛性更可信。

### 4.8 `run_advanced_comparison()`

这是高级实验的总入口。

它比较：
- RWMH
- MTM-K4
- LB-MTM
- Parallel MTM

它输出：
- 时间
- IAT
- ESS
- Geweke 诊断

这份输出通常比基础版更像论文里的“方法增强对比表”。

---

## 5. `src/visualization.py`：基础图生成文件

这个文件的核心任务只有一个：把基础实验结果画成图。

### 5.1 它依赖谁

它从 `mcmc_option_pricing.py` 导入：
- `BlackScholesModel`
- `RandomWalkMetropolis`
- `MultipleTryMetropolis`
- `compute_autocorrelation`
- `compute_integrated_autocorrelation_time`

也就是说，这个文件本身不定义实验逻辑，它是“展示层”。

### 5.2 `plot_comparison()`

这个函数负责生成 `mcmc_comparison.png`。

它画 4 个子图：

#### 左上：样本路径

画的是前 500 步样本轨迹。

它想表达的是：
- 链是怎么走的。
- RWMH 和 MTM 的移动模式有什么不同。

#### 右上：分布直方图

把样本分布和真实密度放一起。

它想表达的是：
- 采样结果是否贴近目标分布。

#### 左下：自相关

用 `acorr()` 画 ACF。

它想表达的是：
- 哪个算法样本相关性更强。
- 哪个算法更“独立”。

#### 右下：时间与 IAT 双轴图

一边是运行时间，一边是 IAT。

它想表达的是：
- 算法不是只看快不快，还要看样本质量。

### 5.3 `plot_speedup_curve()`

这个函数负责生成 `speedup_analysis.png`。

它画两类关系：

#### 左图：速度比 vs K

比较观测到的速度变化和参考线：
- O(K) 线性增长
- O(log K) 对数增长

它想说明：
- 理论加速并不一定完全体现在串行 Python 上。

#### 右图：IAT 降低 vs K

它想说明：
- 虽然时间不一定更快，但相关性往往在下降。
- 这就是多提案方法的统计价值。

### 5.4 这份文件的作用总结

一句话：

`visualization.py` 是基础实验的“出图脚本”。

它不负责证明理论，只负责把实验结果变成能看懂的图。

---

## 6. `src/visualization_optimized.py`：综合图生成文件

这是优化版对应的可视化脚本，图比基础版更完整。

### 6.1 它依赖谁

它从 `mcmc_optimized.py` 导入：
- 模型类
- 采样器类
- 指标函数

说明它依赖的是优化版实验结果，不是基础版。

### 6.2 `plot_comprehensive_analysis()`

这个函数生成 `comprehensive_analysis.png`。

它一共画 6 个面板。

#### 面板 1：前 500 步样本轨迹

看不同算法如何移动。

#### 面板 2：分布对比

看样本是否逼近真实分布。

#### 面板 3：ACF 曲线

看样本相关性随滞后怎么衰减。

#### 面板 4：IAT 与 ESS

看“独立性”和“有效样本数”的对比。

#### 面板 5：累计均值收敛图

看估计值是否逐渐靠近解析解。

#### 面板 6：时间 vs 效率

把时间和 ESS/s 放一起看。

这个面板很关键，因为它让你看到：
- 有的算法样本质量更好，但代价更贵。
- 采样效率不是单一维度。

### 6.3 `plot_speedup_curves()`

这个函数生成 `speedup_curves.png`。

它画 3 个面板：

#### 左图：时间随 K 变化

说明 K 越大，计算越重。

#### 中图：IAT 随 K 变化

说明 K 越大，样本相关性通常下降。

#### 右图：ESS/second

说明“单位时间能产出多少有效样本”。

这张图最适合回答的问题是：
“多提案到底值不值？”

### 6.4 这份文件的作用总结

一句话：

`visualization_optimized.py` 是“论文主图生成器”。

它把优化版实验整理成更像最终报告的综合图。

---

## 7. `src/__init__.py`

这个文件很短，但它的作用也很明确：

### 它干什么

- 让 `src` 目录成为一个 Python 包。
- 方便其他脚本从 `src` 导入模块。

### 它不干什么

- 不定义实验。
- 不生成图。
- 不做采样。

所以它是“包标识文件”，不是实验逻辑文件。

---

## 8. `figures/` 目录每张图的详细说明

### 8.1 `figures/comprehensive_analysis.png`

**生成文件：** `src/visualization_optimized.py`

**它讲的是什么：**
- 这是整套实验最完整的一张总图。
- 它回答的不是单一问题，而是“算法效果整体如何”。

**你从这张图里能读出什么：**
- 链有没有收敛。
- 样本分布像不像目标分布。
- 哪个算法自相关更低。
- 哪个算法 ESS 更高。
- 哪个算法更快。
- 时间和效率怎么权衡。

**为什么重要：**
- 这类图适合放在正文结果页，作为总览图。

### 8.2 `figures/speedup_curves.png`

**生成文件：** `src/visualization_optimized.py`

**它讲的是什么：**
- 研究提案数 K 增大以后，时间、IAT、效率分别怎么变化。

**你从这张图里能读出什么：**
- K 增大后，时间一般会上升。
- 但 IAT 往往会下降。
- 关键问题是 ESS/s 是否真的提升。

**为什么重要：**
- 它直接回答“多提案是不是越多越好”。

### 8.3 `figures/mcmc_comparison.png`

**生成文件：** `src/visualization.py`

**它讲的是什么：**
- 基础版 RWMH 和 MTM 的直接对比。

**你从这张图里能读出什么：**
- MTM 的轨迹是否更平稳。
- 分布是否更贴目标。
- 自相关是否更低。
- 时间和 IAT 是否出现 trade-off。

**为什么重要：**
- 适合先给读者一个直观印象。

### 8.4 `figures/speedup_analysis.png`

**生成文件：** `src/visualization.py`

**它讲的是什么：**
- K 变化时，时间加速比和 IAT 降低倍数如何变化。

**你从这张图里能读出什么：**
- 理论上的速度扩展和实际 Python 串行实现之间有差距。
- 但统计效率的改善仍然存在。

**为什么重要：**
- 它帮助解释“为什么结果没那么快，但仍然有价值”。

---

## 9. 按“读代码”的顺序再讲一遍

如果你想真正掰开揉碎理解，建议这样看：

1. 先看 `mcmc_option_pricing.py`
   - 明白问题怎么变成采样问题。
   - 明白 RWMH 和 MTM 是怎么写的。

2. 再看 `visualization.py`
   - 看基础实验结果怎么被画出来。

3. 再看 `mcmc_optimized.py`
   - 看优化版怎么减少重复计算。
   - 看主实验如何整理对比指标。

4. 再看 `visualization_optimized.py`
   - 看综合图如何把所有信息拼起来。

5. 最后看 `mcmc_advanced.py`
   - 看 LB-MTM 和多链并行这些扩展策略。

---

## 10. 最后用最短的话总结每个文件

- `mcmc_option_pricing.py`：基础版算法与实验主流程。
- `mcmc_optimized.py`：优化版算法与主结果统计。
- `mcmc_advanced.py`：高级算法扩展与额外诊断。
- `visualization.py`：基础版结果出图。
- `visualization_optimized.py`：综合图和速度图出图。
- `__init__.py`：包标识文件。
- `figures/`：保存最终输出图。
