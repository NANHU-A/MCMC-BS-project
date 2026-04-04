标题：第2/4/5章关键结论追溯矩阵
日期：2026-04-04

| 章节位置 | 结论/内容 | 表图编号 | 数据来源脚本 | 配置 | 种子 | 时间戳 |
|---|---|---|---|---|---|---|
| 2.3 | 目标分布定义为 ln(S_T) 的正态密度 | 公式段 | `src/mcmc_option_pricing.py` | BS默认参数 | 不适用 | 2026-04-04 17:57:20 |
| 3.2 | RWMH/MTM 伪代码与实现一致 | 3.2.1/3.2.2 | `src/mcmc_optimized.py` | `proposal_std=0.3` | 42 | 2026-04-04 17:57:45 |
| 4.2 | 主比较表格（价格/误差/接受率/IAT/ESS） | 表4-1 | `src/mcmc_optimized.py` | `n_samples=20000,burn_in=n//4` | 42 | 2026-04-04 17:55:42 |
| 4.2 | 5次重复均值±std | 表4-1 | `src/mcmc_optimized.py` | 同上 | 42~46 | 2026-04-04 17:56:46 |
| 4.3 | 速度比与IAT改善倍数 | 表4-2 | `src/mcmc_optimized.py` | `n_samples=20000,burn_in=n//4` | 42 | 2026-04-04 17:51:51 |
| 4.4 | MC vs MCMC 基准比较 | 表4-3 | `src/mcmc_optimized.py` | `n_samples=50000,burn_in=n//4` | 42 | 2026-04-04 17:50:24 |
| 4.5 | 综合分析图与速度曲线图 | 图4-1/4-2 | `src/visualization_optimized.py` | 默认绘图配置 | 42 | 2026-04-04 17:48:20 |
| 4.6 | Geweke收敛诊断与阈值判断 | 文本段 | `src/mcmc_advanced.py` | `n_samples=20000` | 42 | 2026-04-04 18:08:32 |
| 5.2 | 串行实现成本高、统计效率与时间成本权衡 | 表5-1+5.2 | 由4.2/4.3/4.6汇总 | 同上 | 同上 | 2026-04-04 17:57:58 |

说明

- 主证据文件：
  - `docs/superpowers/notes/2026-04-04-main-experiment-results.csv`
  - `docs/superpowers/notes/2026-04-04-repeatability-results.csv`
  - `docs/superpowers/notes/2026-04-04-speedup-results.csv`
  - `docs/superpowers/notes/2026-04-04-baseline-results.csv`
  - `docs/superpowers/notes/2026-04-04-convergence-results.csv`
- 若与历史README数字冲突，以本次运行结果为准。
