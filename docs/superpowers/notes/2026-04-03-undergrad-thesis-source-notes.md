# 本科论文写作事实提取笔记（master）

## 1. 事实分级与冲突处理

- 一级事实：`src/*.py` 中可执行算法逻辑与函数实现。
- 二级事实：`README.md`、`README2.md` 的叙述性总结与历史实验记录。
- 冲突规则：若叙述数值与源码流程不完全一致，正文优先采用一级事实，并在实验分析中指出差异来源。

## 2. 结构化事实表

| 类别 | 事实 | 证据路径 |
|---|---|---|
| 概念 | 研究对象为 Black-Scholes 看涨期权定价与 MCMC 采样效率比较 | `README.md` |
| 概念 | 关键对比算法：RWMH 与 MTM（K=2,4,8） | `src/mcmc_option_pricing.py` |
| 概念 | 统计诊断指标：ACF、IAT、ESS，扩展含 Geweke | `src/mcmc_option_pricing.py`, `src/mcmc_advanced.py` |
| 实现 | Black-Scholes 模型类 `BlackScholesModel` 提供解析解与目标密度 | `src/mcmc_option_pricing.py`, `src/mcmc_optimized.py` |
| 实现 | RWMH 核心采样器 `RandomWalkMetropolis.sample` | `src/mcmc_option_pricing.py`, `src/mcmc_optimized.py` |
| 实现 | MTM 采样器 `MultipleTryMetropolis.sample`（含权重选择与接受拒绝） | `src/mcmc_option_pricing.py`, `src/mcmc_optimized.py` |
| 实现 | 高级扩展 `LocallyBalancedMTM` 与 `ParallelMultiChain` | `src/mcmc_advanced.py` |
| 实验 | 运行入口：`run_experiment`, `run_comparison`, `run_speedup_analysis`, `run_advanced_comparison` | `src/mcmc_option_pricing.py`, `src/mcmc_optimized.py`, `src/mcmc_advanced.py` |
| 可视化 | 主要图像产出 `comprehensive_analysis.png`, `speedup_curves.png` | `src/visualization_optimized.py` |
| 记录结果 | README 中给出代表性结果：IAT 随 K 提升下降，但总时间增加 | `README.md` |

## 3. 章节证据映射（citation map）

| 章节 | 核心内容 | 主要证据 |
|---|---|---|
| 摘要/Abstract | 问题、方法、结论概述 | `README.md`, `src/mcmc_optimized.py` |
| 第1章 绪论 | 背景、意义、研究现状与贡献 | `README.md`, `README2.md`（仅概念核对） |
| 第2章 理论基础 | BS、MC、MCMC、MTM、诊断指标公式 | `src/mcmc_option_pricing.py`, `src/mcmc_advanced.py` |
| 第3章 方法与实现 | 模块架构、函数职责、流程伪代码 | `src/mcmc_option_pricing.py`, `src/mcmc_optimized.py`, `src/mcmc_advanced.py` |
| 第4章 实验结果与分析 | 参数设置、结果对比、效率权衡、图表引用 | `README.md`, `src/visualization_optimized.py` |
| 第5章 结论与展望 | 研究结论、局限、未来工作 | `README.md`, `src/mcmc_advanced.py` |
| 附录 | 复现实验命令与关键函数说明 | `src/*.py`, `README.md` |

## 4. DoD 支撑性检查

- 中英文摘要：可支持。
- 第1章至第5章：可支持。
- 公式 >=8：可支持（BS、MC、MH、MTM、ACF、IAT、ESS、加速比等）。
- 表格 >=3：可支持。
- 图示引用位 >=3：可支持（`comprehensive_analysis.png`, `speedup_curves.png`, `mcmc_comparison.png`）。
- 参考文献 >=8：可支持（经典与近年 MCMC/MTM/BS 文献）。
