# 多提案 MCMC 在 Black-Scholes 期权定价中的效率研究

## 项目简介

本项目对应本科毕业论文终稿（`results/overleaf/MCMC_BS_project_4.2.pdf`），研究主题为：在 Black-Scholes 框架下比较单提案 RWMH 与多提案 MTM 的统计效率与计算成本权衡。项目目前已完成代码修复、实验复现实证、论文定稿与 XeLaTeX 导出流程。

核心结论：
- MTM 在 IAT/ESS 等统计效率指标上优于 RWMH；
- 串行实现下，提案数 K 增大导致运行时间显著上升；
- 在低维且可直接采样场景，Monte Carlo 仍是更高效基线。

## 论文与成果文件

- 论文 PDF（当前最终稿）：`results/overleaf/MCMC_BS_project_4.2.pdf`
- 论文 Markdown 终稿：`results/opencode/本科毕业论文-终稿.md`
- 研究报告版：`本科毕业论文-研究报告.md`
- 答辩口径：`答辩口径-详细版.md`
- Overleaf 主模板：`overleaf_main_xelatex.txt`
- Overleaf 正文（LaTeX body）：`overleaf_xelatex_code.txt`
- 单文件 XeLaTeX：`main_xelatex_rigorous.tex`

## 模型与实验设置

### Black-Scholes 参数

| 参数 | 符号 | 取值 |
|---|---|---:|
| 初始股价 | $S_0$ | 100 |
| 行权价 | $K$ | 100 |
| 到期时间 | $T$ | 1 |
| 无风险利率 | $r$ | 0.05 |
| 波动率 | $\sigma$ | 0.2 |

### 主要实验配置

- 主比较：`n_samples=20000`, `burn_in=n_samples//4`, `proposal_std=0.3`, `seed=42`
- 速度分析：`seed=42`
- 基线比较（MC vs MCMC）：`n_samples=50000`, `burn_in=n_samples//4`, `seed=42`
- 重复实验：`seed=42,43,44,45,46`

解析解（Analytical Price）：`10.450584`

## 最新核心结果（与论文终稿一致）

### 1) 主比较结果（seed=42）

| 方法 | 价格 | 绝对误差 | 接受率 | 时间(s) | IAT | ESS |
|---|---:|---:|---:|---:|---:|---:|
| RWMH | 10.7591 | 0.3085 | 59.21% | 0.88 | 10.0 | 2000 |
| MTM-K2 | 10.2750 | 0.1756 | 72.15% | 5.79 | 6.0 | 3333 |
| MTM-K4 | 10.3573 | 0.0933 | 80.40% | 9.25 | 5.0 | 4000 |
| MTM-K8 | 10.5741 | 0.1235 | 84.98% | 15.91 | 5.0 | 4000 |

### 2) 速度分析（seed=42）

| K | 时间(s) | IAT | 时间速度比 $t_{RWMH}/t_K$ | IAT 改善倍数 $\tau_{RWMH}/\tau_K$ |
|---:|---:|---:|---:|---:|
| 1 (RWMH) | 1.023 | 8.0 | 1.00x | 1.00x |
| 2 | 5.662 | 6.0 | 0.18x | 1.33x |
| 4 | 9.090 | 5.0 | 0.11x | 1.60x |
| 8 | 15.961 | 5.0 | 0.06x | 1.60x |

### 3) Monte Carlo 基线（seed=42）

| 方法 | 价格 | 绝对误差 | 标准误 | 时间(s) | IAT | ESS |
|---|---:|---:|---:|---:|---:|---:|
| Monte Carlo | 10.4462 | 0.0044 | 0.0657 | 0.0010 | - | - |
| MCMC (RWMH) | 10.4643 | 0.0137 | - | 2.48 | 8.0 | 6250 |

### 4) 5 次重复实验（42~46）摘要

- RWMH 价格均值±std：`10.6913 ± 0.3077`
- MTM-K2 价格均值±std：`10.5253 ± 0.1922`
- MTM-K4 价格均值±std：`10.5119 ± 0.2266`
- MTM-K8 价格均值±std：`10.4107 ± 0.1678`

对应数据文件：`docs/superpowers/notes/repeatability_all_methods_5seeds.csv`

## 代码结构

```text
MCMC-BS-project/
├── README.md
├── src/
│   ├── mcmc_option_pricing.py      # 基础 BS + RWMH/MTM
│   ├── mcmc_optimized.py           # 主实验、速度分析、基线比较
│   ├── mcmc_advanced.py            # LB-MTM、并行链、Geweke
│   ├── visualization.py
│   └── visualization_optimized.py  # 论文图表生成
├── docs/superpowers/notes/
│   ├── run_comparison_seed42_full.csv
│   ├── speedup_table_from_seed42.csv
│   ├── repeatability_all_methods_5seeds.csv
│   └── ...
├── results/overleaf/MCMC_BS_project_4.2.pdf
└── results/opencode/本科毕业论文-终稿.md
```

## 运行方式

在项目根目录执行：

```bash
python src/mcmc_optimized.py
python src/mcmc_advanced.py
python src/visualization_optimized.py
```

生成的典型图像：
- `comprehensive_analysis.png`
- `speedup_curves.png`
- `mcmc_comparison.png`

## XeLaTeX / Overleaf 导出

### 推荐上传到 Overleaf 的文件

1. `overleaf_main_xelatex.txt`（重命名为 `main.tex`）
2. `overleaf_xelatex_code.txt`
3. 所有图片资源（`*.png`）

### 正文转换脚本

- `scripts/build_xelatex_body.py`

该脚本会从 `results/opencode/本科毕业论文-终稿.md` 生成 `overleaf_xelatex_code.txt`，并自动处理目录渲染所需结构。

## 参考文献（项目核心）

1. Black, F., & Scholes, M. (1973). The pricing of options and corporate liabilities.
2. Merton, R. C. (1973). Theory of rational option pricing.
3. Metropolis, N., et al. (1953). Equation of state calculations by fast computing machines.
4. Hastings, W. K. (1970). Monte Carlo sampling methods using Markov chains.
5. Liu, J. S. (2004). Monte Carlo Strategies in Scientific Computing.
6. Glasserman, P. (2003). Monte Carlo Methods in Financial Engineering.
7. Robert, C. P., & Casella, G. (2004). Monte Carlo Statistical Methods.
8. Pozza, F., & Zanella, G. (2025). On the fundamental limitations of multi-proposal MCMC algorithms.
9. Neal, R. M. (2011). MCMC using Hamiltonian dynamics.
