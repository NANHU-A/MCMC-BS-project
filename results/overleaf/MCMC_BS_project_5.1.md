# MCMC_BS_project_5.1

## Page 1

多提案 MCMC 算法在 Black-Scholes 期权定
价中的效率研究

## Page 2

原创性声明和版权使用授权书

## Page 3

武汉大学本科毕业论文（设计）
中文摘要
期权定价是金融工程中的核心问题。虽然 Black-Scholes 模型在理想参数下有解
析解，但在分布结构更复杂、或需要刻画参数不确定性时，仍要依赖随机模拟。本
文以 master 分支代码为对象，对随机游走 Metropolis-Hastings（RWMH）与多提案
Multiple-TryMetropolis（MTM）进行对比，重点讨论多提案机制带来的统计效率提升，
以及相应的计算开销。
研究首先给出Black-Scholes看涨期权定价公式与MonteCarlo估计框架，再构建
MCMC抽样流程，把期权支付函数的期望估计转化为目标分布上的样本均值估计。评
估指标采用接受率、积分自相关时间（IAT）和有效样本量（ESS），并与运行时间结
合做权衡分析。基于项目实验记录和源码逻辑，在本报告采用的配置下，随着提案数
K增大，MTM在IAT与ESS上优于单提案RWMH，同时总运行时间增加，呈现“统
计效率提升”与“墙钟成本上升”并存的结果。
本文的主要贡献是：在本科毕业论文框架下，将算法原理、代码实现和实验证据
组织到同一条可追溯证据链中，形成可复现的研究报告结构，并为后续拓展到高维模
型、并行硬件或自适应提案机制打下基础。
关键词：期权定价；Black-Scholes；马尔可夫链蒙特卡洛；Multiple-TryMetropolis；
有效样本量
Abstract
Option pricing is a central topic in financial engineering. Although the Black-Scholes
model provides a closed-form solution under idealized assumptions, stochastic simulation
remains essential when the target distribution becomes complex. This report studies the
masterbranchimplementationandcomparesRandomWalkMetropolis-Hastings(RWMH)
with Multiple-Try Metropolis (MTM), focusing on the gain in statistical efficiency and the
associatedcomputationalcost.
WefirstpresenttheBlack-ScholescallpricingformulaandtheMonteCarloestimation
framework,thenformulateMCMC-basedsamplingforexpectationestimationunderthetar-
getdistribution. Performanceisevaluatedbyacceptancerate,integratedautocorrelationtime
(IAT), and effective sample size (ESS), together with wall-clock runtime to quantify practi-
cal efficiency trade-offs. Based on the project evidence and source-level logic, the results
I

## Page 4

武汉大学本科毕业论文（设计）
indicate that increasing the number of proposals K in MTM often improves IAT and ESS
comparedwithsingle-proposalRWMH,whiletotalruntimemayincrease.
The main contribution of this report is the integration of theory, implementation, and
experimental evidence into one reproducible narrative. This structure also supports future
extensionstohigh-dimensionalsettings,parallelhardware,andadaptiveproposaldesigns.
Keywords: Option Pricing; Black-Scholes; Markov Chain Monte Carlo; Multiple-Try
Metropolis;EffectiveSampleSize
II

## Page 5

目 录
中文摘要 I
Abstract I
1 第 1 章绪论 1
1.1 1.1研究背景与意义.................................................. 1
1.2 1.2国内外研究现状.................................................. 1
1.3 1.3研究问题与本文贡献............................................. 2
1.4 1.4本章小结 ......................................................... 3
2 第 2 章理论基础 3
2.1 2.1Black-Scholes模型与欧式看涨期权解析解 ...................... 3
2.2 2.2MonteCarlo与MCMC 估计框架 ................................ 4
2.3 2.3RWMH与MTM 机制 ............................................ 4
2.4 2.4统计诊断指标 .................................................... 5
2.5 2.5本章小结 ......................................................... 6
3 第 3 章方法与实现 6
3.1 3.1项目结构与模块职责............................................. 6
3.2 3.2核心算法流程伪代码............................................. 7
3.3 3.3参数设置与可复现策略 .......................................... 8
3.4 3.4本章小结 ......................................................... 9
4 第 4 章实验结果与分析 9
4.1 4.1实验设计与评价指标............................................. 9
4.2 4.2基础结果对比 .................................................... 10
4.3 4.3速度与效率的权衡分析 .......................................... 10
4.4 4.4与MonteCarlo基线比较......................................... 11
4.5 4.5图示证据与可视化说明 .......................................... 11
4.6 4.6差异来源与有效性讨论 .......................................... 13
III

## Page 6

武汉大学本科毕业论文（设计）
4.7 4.7本章小结 ......................................................... 13
5 第 5 章结论与展望 13
5.1 5.1主要结论 ......................................................... 13
5.2 5.2研究局限 ......................................................... 14
5.3 5.3未来工作 ......................................................... 14
5.4 5.4本章小结 ......................................................... 14
6 参考文献 14
7 附录 15
7.1 附录A 复现实验环境与命令 ........................................ 15
7.2 附录B冲突处理与证据追溯规则.................................... 16
7.3 附录C关键函数说明 ................................................ 16
IV

## Page 7

武汉大学本科毕业论文（设计）
第 1 章绪论
1.1 研究背景与意义
金融衍生品定价问题长期是概率统计与应用数学的重要交叉方向。看涨期权价格
可视为风险中性测度下未来贴现收益的期望值，其本质属于随机变量函数的积分估计
问题。对于Black-Scholes这类理想模型，解析公式可直接给出定价结果[1][2]；但在
参数不确定、模型扩展或后验推断情景中，数值采样方法仍具有现实意义[6]。
蒙特卡洛（Monte Carlo, MC）方法以独立同分布样本进行期望估计，框架简洁，
但在复杂目标分布下效率受限 [5][6]。马尔可夫链蒙特卡洛（MCMC）通过构造平稳
分布为目标分布的马尔可夫链完成抽样，避免直接采样困难[3][4][7]。单提案RWMH
实现简单，但样本相关性较高时会降低有效样本产出。多提案MTM在一次迭代中产
生多个候选点并进行加权选择，在既有文献与本项目实验中均表现出更强的混合能力
[8]。
从本科毕业论文角度，本研究价值在于：一方面，展示概率模型、数值算法与统
计诊断指标的系统衔接；另一方面，给出 “统计效率与计算成本” 共同衡量的实验分
析路径，体现应用统计问题中的方法选择逻辑。
图1-1展示本研究的总体技术路线：模型定义、采样算法设计、指标评估与结果
解释。
1.2 国内外研究现状
经典文献中，Black-Scholes模型为欧式期权定价提供了里程碑式解析表达[1][2]。
随后大量研究关注随机模拟在复杂金融积分中的作用，MCMC 在后验采样与不确定
性量化中逐步成熟[5][7]。Metropolis-Hastings体系作为通用抽样框架，强调详细平衡
条件与遍历性基础[3][4]。近年来，多提案机制（如MTM）与局部平衡思想在改进混
合效率方面受到关注[8]。
同时，近年研究也指出多提案算法存在 “统计效率提升与计算成本上升并行” 的
结构性限制 [8]；在更高维模型中，基于梯度的 HMC 路线常被作为对照思路 [9]。这
一前沿认识与本文第4章的实证结果方向一致。
结合本项目代码，src/mcmc_option_pricing.py与src/mcmc_optimized.py已
将RWMH、MTM及ACF/IAT/ESS指标计算落地，src/mcmc_advanced.py进一步引
入 Locally Balanced MTM 与多链并行比较，体现了从基础算法到改进算法的递进结
1

## Page 8

武汉大学本科毕业论文（设计）
图1-1: 图1-1研究技术路线示意图
构。
表1-1给出本文所依托研究脉络与项目对应关系。
研究方向 代表方法 本项目对应
解析定价 Black-Scholes公式 BlackScholesModel.call_price_analytical
随机模拟 MonteCarlo run_baseline_comparison中MC基准
MCMC单提案 RWMH RandomWalkMetropolis.sample
MCMC多提案 MTM/LB-MTM MultipleTryMetropolis.sample,LocallyBalancedMTM.sample
1.3 研究问题与本文贡献
本文集中回答三个问题：
1. 在当前 Black-Scholes 目标分布下，MTM 相较 RWMH 能否显著降低样本相关
性？
2. 统计效率改进（IAT降低、ESS提升）是否会被计算时间开销抵消？
3. 如何将“理论-代码-实验”整合为本科论文可答辩的研究叙述？
对应贡献如下：
2

## Page 9

武汉大学本科毕业论文（设计）
• 建立了“模型公式-采样器-诊断指标”统一框架；
• 明确给出源码级证据路径，保证实验分析可追溯；
• 形成适配数学与统计学院本科论文规范的完整报告结构。
1.4 本章小结
本章明确了研究背景、问题与贡献。下一章将给出核心理论基础，包括 Black-
Scholes 解析定价、MCMC 机制及效率评价指标定义，为后续方法与实验分析奠定数
学基础。
第 2 章理论基础
2.1 Black-Scholes 模型与欧式看涨期权解析解
在风险中性测度下，股票价格服从几何布朗运动：
dS
t
= rdt+σdW .
t
S
t
其终值可写为：
[( ) ]
√
1
S = S exp r− σ2 T +σ TZ , Z ∼ N(0,1).
T 0
2
欧式看涨期权价格定义为：
[ ]
C = e −rT E (S −K)+ .
T
Black-Scholes解析公式为：
C = S Φ(d )−Ke −rTΦ(d ),
0 1 2
其中
ln(S /K)+(r+ 1σ2)T √
d = 0 √ 2 , d = d −σ T.
1 2 1
σ T
该 公 式 在 src/mcmc_option_pricing.py 与 src/mcmc_optimized.py 的
BlackScholesModel.call_price_analytical中实现。
3

## Page 10

武汉大学本科毕业论文（设计）
2.2 Monte Carlo 与 MCMC 估计框架
标准MonteCarlo估计器为：
∑N
1
C ˆ = e −rT(S(i) −K)+.
MC N T
i=1
当直接采样困难或希望在更复杂目标分布上估计积分时，可构造马尔可夫链样本
X(i) ∼ π（渐近意义），并采用：
∑N
1
I ˆ = h(X(i)).
MCMC
N
i=1
在本研究中，h(x) 对应贴现支付函数，run_baseline_comparison 展示了
MC 与 MCMC 的基准比较流程（证据来源：src/mcmc_optimized.py；参数：
n_samples=50000；随机种子：42）。
2.3 RWMH 与 MTM 机制
本文采样变量定义为X = lnS ，其目标分布由Black-Scholes终值分布直接给出：
T
( )
1
X ∼ N(µ,σ2 ), µ = lnS + r− σ2 T, σ2 = σ2T.
X 0 2 X
对应密度函数写为：
( )
1 (x−µ)2
π(x) = √ exp − .
2πσ2 2σ2
X X
RWMH采用随机游走提案x′ ∼ q(x′|x)，接受概率为：
{ }
π(x′)q(x|x′)
′
α(x,x) = min 1, .
π(x)q(x′|x)
对称提案时可化简为：
{ }
π(x′)
′
α(x,x) = min 1, .
π(x)
MTM每轮生成 K 个候选点 {y }K ，按权重选择候选并执行接受-拒绝。高层表
j j=1
达可写为：
4

## Page 11

武汉大学本科毕业论文（设计）
w
w ∝ π(y ), Pr(y 被选中) = ∑ j .
j j j K w
l=1 l
项 目 实 现 位 于 MultipleTryMetropolis.sample（证 据 来 源：
src/mcmc_option_pricing.py、src/mcmc_optimized.py）。
在src/mcmc_advanced.py中，LocallyBalancedMTM.local_balance_weight给
出局部平衡权重：
( )
logπ(y)−logπ(x)
w (y|x) = exp .
LB
τ
2.4 统计诊断指标
自相关函数（ACF）定义为：
Cov(X ,X )
t t+k
ρ = .
k
Var(X )
t
积分自相关时间（IAT）可表示为：
∑∞
τ = 1+2 ρ .
int k
k=1
有效样本量（ESS）定义为：
N
ESS = .
τ
int
效率指标（每秒有效样本）可写为：
ESS
Eff = .
t
run
速度比可定义为：
t
RWMH
Speedup = .
time t
MTM
以上指标在compute_autocorrelation、compute_integrated_autocorrelation_time
以 及 实 验 驱 动 函 数 中 体 现 （证 据 来 源：src/mcmc_option_pricing.py、
src/mcmc_optimized.py）。
5

## Page 12

武汉大学本科毕业论文（设计）
图2-1: 图2-1ACF对比示意
图2-1展示ACF随滞后变化的典型对比结果。
2.5 本章小结
本章构建了本文所需的理论框架：从Black-Scholes解析定价到MCMC采样，再
到IAT/ESS等统计效率指标。下一章将在此基础上给出代码实现路径、算法流程与实
验设计细节。
第 3 章方法与实现
3.1 项目结构与模块职责
本研究在master分支的核心代码模块可概括为四类：
模块文件 主要内容 在论文中的角色
src/mcmc_option_pricing.py 基础BS+RWMH/MTM+试验函数 方法基线与主比较来源
src/mcmc_optimized.py 优化版本、基准比较、速度分析 主实验结论的可复现实现
src/mcmc_advanced.py LB-MTM、并行多链、Geweke 拓展实验与讨论支撑
src/visualization_optimized.py 综合图与加速曲线绘制 图示证据来源
其中，BlackScholesModel 负责目标分布及解析解，RandomWalkMetropolis 与
6

## Page 13

武汉大学本科毕业论文（设计）
图3-1: 图3-1源码模块映射图
MultipleTryMetropolis负责采样，run_*系列函数负责实验编排和结果输出。
图3-1给出“源码到论文章节”的映射关系示意。
3.2 核心算法流程伪代码
3.2.1RWMH伪代码
Input: target log density log￿, proposal std s, sample size N, burn-in B
Initialize x0
for i = 1 to N + B:
propose x' = x + Normal(0, s^2)
log￿ = log￿(x') - log￿(x)
if log(U) < log￿:
x = x'
if i > B:
store x
Output: samples, acceptance rate
对 应 实 现：RandomWalkMetropolis.sample（证 据 来 源：
src/mcmc_optimized.py）。
3.2.2MTM伪代码
Input: target log density log￿, proposal count K, proposal std s
Initialize x
for each iteration:
generate forward set y1,...,yK from Normal(x, s^2)
7

## Page 14

武汉大学本科毕业论文（设计）
compute forward weights wj = exp(log￿(yj) - max log￿(y))
sample y* from normalized forward weights
build backward set: x plus K-1 draws from Normal(y*, s^2)
compute log_accept_ratio = logsumexp(log￿(forward set)) - logsumexp(log￿(backward set))
accept or reject y*
对 应 实 现：MultipleTryMetropolis.sample（证 据 来 源：
src/mcmc_option_pricing.py）。
3.2.3实验评价流程
Set model params (S0, K, T, r, sigma)
Run samplers (RWMH / MTM-K2 / MTM-K4 / ...)
Transform log-price samples to discounted payoffs
Compute ACF, IAT, ESS and runtime
Compare error to analytical price and summarize trade-offs
对 应 实 现：run_comparison, run_speedup_analysis,
run_advanced_comparison。
3.3 参数设置与可复现策略
典型参数设置如下：
• Black-Scholes参数：S = 100,K = 100,T = 1,r = 0.05,σ = 0.2；
0
• 采样规模：主比较实验n_samples=20000，基准比较实验n_samples=50000；
• burn-in：主比较实验使用 burn_in=n_samples//4，并行多链示例使用
burn_in=n_samples//10；
• 随机种子：np.random.seed(42)。
上述设置在 if __name__ == "__main__" 入口及对应 run_* 函数中可见
（证 据 来 源：src/mcmc_optimized.py、src/mcmc_advanced.py； 主 比 较 配 置：
n_samples=20000, burn_in=n_samples//4；基准比较配置：n_samples=50000,
burn_in=n_samples//4； 并 行 多 链 配 置：n_samples_per_chain=5000,
burn_in=n_samples//10；随机种子：42）。
表3-2给出本文实验参数清单。
8

## Page 15

武汉大学本科毕业论文（设计）
参数类别 参数名 取值 来源
模型参数 S ,K,T,r,σ 100,100,1,0.05,0.2 run_*默认参数
0
采样设置 n_samples 20000/50000 run_comparison,run_baseline_comparison
提案设置 proposal_std,k_proposals 0.3,2/4/8 RandomWalkMetropolis,MultipleTryMetropolis
随机性控制 seed 42 主程序入口
3.4 本章小结
本章从实现层面给出了算法到代码的对应关系与实验流程。下一章将对结果进行
定量整理，并讨论统计效率提升与计算时间成本之间的权衡关系。
第 4 章实验结果与分析
4.1 实验设计与评价指标
本章围绕RWMH与MTM（K=2,4,8）在Black-Scholes目标分布下的性能进行比
较，评价维度包括：
1. 定价精度（相对解析解绝对误差）；
2. 运行时间（秒）；
3. 统计效率（IAT、ESS）；
4. 接受率（AcceptanceRate）。
解析解基准为C = 10.450584。
BS
本章采用三组真实运行结果：
• 主比较实验：seed=42, n_samples=20000, proposal_std=0.3；
• 速度分析实验：seed=42；
• MC基线比较实验：seed=42, n_samples=50000。
其中，5 次重复实验（seed=42~46）的均值与标准差用于稳健性补充，不替代主
实验单次结果。
9

## Page 16

武汉大学本科毕业论文（设计）
4.2 基础结果对比
表 4-1 给出主比较实验（seed=42）结果，并列出 5 次重复实验的价格均值 ±
标准差（解析解为基准，主实验配置：n_samples=20000, burn_in=n_samples//4,
proposal_std=0.3, seed=42；重复实验种子：42~46）。
方法 价格估计(seed=42) 价格均值±std(5次) 绝对误差(seed=42) 接受率(seed=42) 时间(s,seed=42) IAT(seed=42) ESS(seed=42)
解析解 10.450584 - - - - - -
RWMH 10.7591 10.6913±0.3077 0.3085 59.21% 0.88 10.0 2000
MTM-K2 10.2750 10.5253±0.1922 0.1756 72.15% 5.79 6.0 3333
MTM-K4 10.3573 10.5119±0.2266 0.0933 80.40% 9.25 5.0 4000
MTM-K8 10.5741 10.4107±0.1678 0.1235 84.98% 15.91 5.0 4000
在seed=42的单次结果中，MTM-K4的绝对误差最小（0.0933）；随K增大，接受
率由59.21%（RWMH）提升至84.98%（MTM-K8），且IAT从10.0降至5.0、ESS从
2000提升至4000。与此同时，运行时间由0.88s增至15.91s。该结果表明：多提案机
制可提高样本质量，但在当前串行实现下需要付出明显时间成本。
4.3 速度与效率的权衡分析
定义时间速度比：
t
RWMH
Speedup = .
time t
MTM(K)
定义相关性改善比：
τ
RWMH
IATReduction = .
τ
MTM(K)
表4-2展示speedup分析实验（seed=42）下不同K的时间与统计效率关系。
K值 时间(s) IAT 时间速度比 IAT改善倍数
1(RWMH) 1.023 8.0 1.00x 1.00x
2 5.662 6.0 0.18x 1.33x
10

## Page 17

武汉大学本科毕业论文（设计）
K值 时间(s) IAT 时间速度比 IAT改善倍数
4 9.090 5.0 0.11x 1.60x
8 15.961 5.0 0.06x 1.60x
结果表明，在当前串行实现中，K 增大时 IAT 由 8.0 下降至 5.0，但运行时间由
1.023s上升至15.961s，因此墙钟时间不呈现加速。该现象由run_speedup_analysis
实验日志直接支持（证据来源：src/mcmc_optimized.py；配置：n_samples=20000,
burn_in=n_samples//4, proposal_std=0.3；种子：42）。
4.4 与 Monte Carlo 基线比较
基 于 run_baseline_comparison 的 复 算 记 录 （证 据 来 源：
src/mcmc_optimized.py； 配 置：n_samples=50000, burn_in=n_samples//4；
随机种子：42），可得到表4-3所示结论。
方法 价格 误差 标准误 时间 (s) IAT ESS 接受率
MonteCarlo 10.4462 0.0044 0.0657 0.0010 - - -
MCMC(RWMH) 10.4643 0.0137 - 2.48 8.0 6250 日志未打印
对于当前低维、目标分布可直接采样的场景，MC具有明显时间优势；MCMC的
核心价值更多体现在复杂目标分布、后验推断或高维问题中。
4.5 图示证据与可视化说明
本项目可视化脚本src/visualization_optimized.py生成如下关键图：
• 图 4-1 综合分析图：comprehensive_analysis.png（样本路径、分布、ACF、
IAT/ESS对比）；
• 图4-2加速曲线图：speedup_curves.png（时间、IAT、ESS/s随K变化）；
• 图4-3辅助比较图：mcmc_comparison.png（用于展示方法对比关系）。
11

## Page 18

武汉大学本科毕业论文（设计）
图4-4: 图4-1综合分析图
图4-5: 图4-2加速曲线图
图4-3: 图4-3MCMC比较图
12

## Page 19

武汉大学本科毕业论文（设计）
4.6 差异来源与有效性讨论
README中个别历史结果数字与本次运行存在差异，原因如下：
1. 不同版本实现细节（如 burn-in 比例、阈值设置） ，对应 run_comparison、
run_speedup_analysis与compute_integrated_autocorrelation_time；
2. 运行环境与随机序列不同，导致同一参数下的统计量存在数值波动；
3. 可 视 化 脚 本 中 的 部 分 时 间 数 据 采 用 固 定 展 示 值， 对 应
visualization_optimized.py中示例时间常量。
为验证稳健性，本文补充了 5 次独立重复实验（种子 42~46）。结果显示：三种
MTM方法在误差上均优于RWMH，其中MTM-K2在5/5次实验中误差低于RWMH，
MTM-K4与MTM-K8均为4/5次；同时三种MTM的平均IAT均低于RWMH（RWMH:
8.8；MTM-K2: 6.0；MTM-K4: 5.8；MTM-K8: 5.4）。这说明在当前实验设置下，多提
案机制在统计效率方面具有稳定优势，但其时间开销仍是主要约束。
4.7 本章小结
本章表明：在本次可复现实验配置下，MTM在统计效率指标上整体优于RWMH，
但串行实现使时间成本显著上升。第 4 章的核心结论可概括为 “统计效率提升与时间
成本增加并存”，这一结论也构成第5章研究局限与后续改进的直接依据。
第 5 章结论与展望
5.1 主要结论
本文基于项目当前代码版本的实测结果，围绕 “多提案 MCMC 在期权定价中的
效率表现”进行了系统分析，主要结论如下：
1. 在统计效率指标上，MTM 通过多候选机制降低了样本相关性，IAT 下降、ESS
提升具有可观测性；
2. 在计算时间指标上，串行实现下提案数增加会显著增加开销，导致时间速度比
低于RWMH；
3. 在方法选择上，应根据问题复杂度与计算资源综合权衡，不能仅依据单一指标
判断算法优劣。
13

## Page 20

武汉大学本科毕业论文（设计）
5.2 研究局限
• 实验主要集中于Black-Scholes框架，目标分布复杂度有限；
• 本次实验主要基于串行 CPU 实现，MTM 的计算成本较高，尚未在并行硬件上
验证潜在加速收益；
• 虽已补充 5 次独立重复实验，但仍缺少更大样本规模与更多市场情景下的稳健
性检验；
• 当前收敛诊断以Geweke为主，后续仍需补充R-hat与多链联合诊断。
5.3 未来工作
可进一步开展以下方向：
1. 在GPU/多核并行环境下实现多提案并行，检验理论加速上界；
2. 将方法扩展到随机波动率模型或更高维后验采样任务；
3. 引入自适应提案尺度与自适应K选择策略；
4. 完善收敛诊断体系（R-hat、多链一致性检验）。
表5-1总结本文结论、局限与展望对应关系。
维度 当前结论 后续改进
统计效率 MTM在IAT/ESS上有优势 扩展到高维任务验证稳健性
时间效率 串行环境下时间成本偏高 并行化实现与硬件加速
诊断完整性 已含 ACF/IAT/ESS/Geweke 增加多链一致性指标
5.4 本章小结
本文完成了面向本科毕业论文要求的研究闭环：问题提出、理论推导、算法实现、
实验比较与结论提炼。整体结果支持 “多提案提升统计效率但存在计算代价” 的核心
判断。
参考文献
[1] Black F, Scholes M. The pricing of options and corporate liabilities[J]. Journal of
PoliticalEconomy,1973,81(3): 637-654.
14

## Page 21

武汉大学本科毕业论文（设计）
[2] Merton R C. Theory of rational option pricing[J]. The Bell Journal of Economics
andManagementScience,1973,4(1): 141-183.
[3]MetropolisN,RosenbluthAW,RosenbluthMN,etal. Equationofstatecalculations
byfastcomputingmachines[J].TheJournalofChemicalPhysics,1953,21(6): 1087-1092.
[4] Hastings W K. Monte Carlo sampling methods using Markov chains and their ap-
plications[J].Biometrika,1970,57(1): 97-109.
[5] Liu J S. Monte Carlo Strategies in Scientific Computing[M]. New York: Springer,
2004.
[6] Glasserman P. Monte Carlo Methods in Financial Engineering[M]. New York:
Springer,2003.
[7] Robert C P, Casella G. Monte Carlo Statistical Methods[M]. 2nd ed. New York:
Springer,2004.
[8]PozzaF,ZanellaG.Onthefundamentallimitationsofmulti-proposalMarkovchain
MonteCarloalgorithms[J].Biometrika,2025,112(1): 1-20.
[9] Neal R M. MCMC using Hamiltonian dynamics[M]//Brooks S, Gelman A, Jones
G, Meng X L. Handbook of Markov Chain Monte Carlo. Boca Raton: CRC Press, 2011:
113-162.
致谢
在本论文的选题、实现与写作过程中，指导教师在研究方向、方法论与论文结构
方面给予了持续、细致的指导与帮助；在实验复现与结论论证阶段，老师对关键问题
的纠偏与建议对论文质量提升起到了决定性作用。在此谨致诚挚感谢。
同时，感谢学院与任课教师在本科阶段提供的系统训练，感谢同学在代码测试、
文稿校对与学术交流中的支持与建议。本文仍存在不足，恳请各位老师批评指正。
附录
附录 A 复现实验环境与命令
• 分支：master（当前同步后的主分支）
• 关键脚本：
– src/mcmc_option_pricing.py
– src/mcmc_optimized.py
15

## Page 22

武汉大学本科毕业论文（设计）
– src/mcmc_advanced.py
– src/visualization_optimized.py
• 典型命令：
python src/mcmc_optimized.py
python src/mcmc_advanced.py
python src/visualization_optimized.py
• 关键参数：
– 主比较：S0=100, K=100, T=1, r=0.05, sigma=0.2, n_samples=20000,
burn_in=n_samples//4, proposal_std=0.3
– 基准比较：n_samples=50000, burn_in=n_samples//4
– 重复实验：seed=42,43,44,45,46
• 随机种子：numpy.random.seed(42)（主实验），重复实验见上。
附录 B 冲突处理与证据追溯规则
1. 一级事实为src/*.py的实现逻辑与可执行流程；
2. 二级事实为README的历史记录；
3. 若数值存在差异，正文优先采用一级事实并在分析中说明原因；
4. 关键结论首次出现时给出来源标注（path+config+seed）。
附录 C 关键函数说明
模块 函数/类 作用
src/mcmc_option_pricing.py BlackScholesModel.call_price_analytical 计算欧式看涨期权解析价格
src/mcmc_option_pricing.py RandomWalkMetropolis.sample 单提案MCMC采样
src/mcmc_option_pricing.py MultipleTryMetropolis.sample 多提案MCMC采样
src/mcmc_optimized.py run_baseline_comparison MC与MCMC基准比较
src/mcmc_optimized.py run_comparison RWMH/MTM核心性能比较
src/mcmc_optimized.py run_speedup_analysis 不同K的速度与IAT分析
16

## Page 23

武汉大学本科毕业论文（设计）
模块 函数/类 作用
src/mcmc_advanced.py LocallyBalancedMTM.sample 局部平衡多提案采样
src/mcmc_advanced.py run_advanced_comparison 高级算法对比与Geweke诊断
17

