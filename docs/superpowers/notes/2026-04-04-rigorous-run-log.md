标题：本科论文严谨修订运行日志
日期：2026-04-04

环境信息

- commit: `a56967e`
- branch: `thesis-rigorous-revision`
- python: `3.10.20 (Anaconda)`
- platform: `Windows-10-10.0.26200-SP0`
- numpy: `2.2.6`
- scipy: `1.15.2`
- matplotlib: `3.10.8`

建议图10项闭环清单（初始快照，历史记录）

| 序号 | 建议项 | 对应动作 | 状态 |
|---|---|---|---|
| 1 | 修复MTM价格估计偏差 | 代码审计+主实验重跑+表4-1/4-2更新 | 初始快照 |
| 2 | 增加3~5次独立重复实验 | 5个种子(42~46)重复+均值±std | 初始快照 |
| 3 | 统一图表格式 | 图号/表号统一+无效引用清理 | 初始快照 |
| 4 | 补充一句说明+小结 | 4.7与5.2强化权衡结论 | 初始快照 |
| 5 | 文献综述微扩(可选) | 1.2补前沿与局限一句 | 初始快照 |
| 6 | 补全实验数据表格 | 表4-1/4-2/4-3填实测值 | 初始快照 |
| 7 | 修正算法伪代码错误 | 2.3/3.2公式与伪代码一致化 | 初始快照 |
| 8 | 生成并插入真实图表 | 重跑visualization并更新引用 | 初始快照 |
| 9 | 明确目标分布数学形式 | 2.3补ln(S_T)正态密度 | 初始快照 |
| 10 | 补充收敛诊断证据 | Geweke(和可选R-hat) | 初始快照 |

基线快照（待对比）

- 当前第4章已有表4-1/4-2/4-3，数值来自历史记录而非本次完整闭环运行。
- 当前结论已写“MTM统计效率高但时间成本高”，待本次运行后重写为严格证据口径。

运行记录

- 主实验脚本：`src/mcmc_optimized.py`
  - 配置：`n_samples=20000`, `burn_in=n_samples//4`, `proposal_std=0.3`, `seed=42`（`src/mcmc_optimized.py` 为全局一次设种；结构化复算脚本为每个算法独立重置seed）
  - 输出摘要（结构化复算）：
    - RWMH: price=10.7591, error=0.3085, acc=59.21%, time=0.88s, IAT=10.0, ESS=2000
    - MTM-K2: price=10.2750, error=0.1756, acc=72.15%, time=5.79s, IAT=6.0, ESS=3333
    - MTM-K4: price=10.3573, error=0.0933, acc=80.40%, time=9.25s, IAT=5.0, ESS=4000
    - MTM-K8: price=10.5741, error=0.1235, acc=84.98%, time=15.91s, IAT=5.0, ESS=4000

- 速度分析复算：`docs/superpowers/notes/2026-04-04-speedup-results.csv`
  - time_speedup: K=2 (0.15x), K=4 (0.10x), K=8 (0.06x)
  - IATReduction: K=2 (1.67x), K=4 (2.00x), K=8 (2.00x)

- 基准比较脚本：`run_baseline_comparison`
  - 配置：`n_samples=50000`, `burn_in=n_samples//4`, `seed=42`
  - MC: price=10.4462, error=0.0044, std=0.0657, time=0.00s
  - MCMC-RWMH: price=10.4643, error=0.0137, time=2.15s, IAT=8.0, ESS=6250, acc=59.27%

- 5次独立重复实验：`docs/superpowers/notes/2026-04-04-repeatability-results.csv`
  - seeds: 42,43,44,45,46
  - RWMH: price mean=10.6913, std=0.3077; IAT mean=8.8
  - MTM-K4: price mean=10.5119, std=0.2266; IAT mean=5.8
  - 方向一致性：MTM-K4 的误差均值低于 RWMH，且 IAT 均值低于 RWMH。

- 收敛诊断脚本：`src/mcmc_advanced.py`
  - Geweke 阈值：`|z|<1.96`
  - RWMH: z=-2.90 (未通过)
  - MTM-K4: z=-0.08 (通过)
  - LB-MTM: z=0.43 (通过)
  - Parallel-MTM: z=-0.75 (通过)
  - R-hat: 当前脚本未直接输出，按规范采用 Geweke 作为本次主证据。

- 图表生成：`src/visualization_optimized.py`
  - 已修复脚本末尾语法错误并重跑成功。
  - 产物：`comprehensive_analysis.png`, `speedup_curves.png`。

建议图10项闭环状态更新

| 序号 | 建议项 | 对应动作 | 位置说明 | 状态 |
|---|---|---|---|---|
| 1 | 修复MTM价格估计偏差 | 代码审计+主实验重跑+表4-1/4-2更新 | `src/mcmc_optimized.py`, `src/mcmc_option_pricing.py`, 报告4.2/4.3 | 已落实 |
| 2 | 增加3~5次独立重复实验 | 5个种子(42~46)重复+均值±std | `2026-04-04-repeatability-results.csv`, 报告表4-1、4.6 | 已落实 |
| 3 | 统一图表格式 | 图号/表号统一+无效引用清理 | 报告4.5图号与图文件映射 | 已落实 |
| 4 | 补充一句说明+小结 | 4.7与5.2强化权衡结论 | 报告4.7、5.2 | 已落实 |
| 5 | 文献综述微扩(可选) | 1.2补前沿与局限一句 | 报告1.2新增段落（[8][9]） | 已落实 |
| 6 | 补全实验数据表格 | 表4-1/4-2/4-3填实测值 | 报告表4-1/4-2/4-3 | 已落实 |
| 7 | 修正算法伪代码错误 | 2.3/3.2公式与伪代码一致化 | 报告2.3、3.2；源码MTM接受率修正 | 已落实 |
| 8 | 生成并插入真实图表 | 重跑visualization并更新引用 | `comprehensive_analysis.png`, `speedup_curves.png`, 报告4.5 | 已落实 |
| 9 | 明确目标分布数学形式 | 2.3补ln(S_T)正态密度 | 报告2.3新增目标分布公式 | 已落实 |
| 10 | 补充收敛诊断证据 | Geweke(和可选R-hat) | `2026-04-04-convergence-results.csv`, 报告4.6 | 已落实 |
