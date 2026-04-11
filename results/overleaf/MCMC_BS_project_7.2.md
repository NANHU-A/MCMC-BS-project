# MCMC_BS_project_7.2

## Page 1

本科毕业论文（设计）
多提案 MCMC 算法在 Black-Scholes 期权定
价中的效率研究
姓 名 ： 周 文 熙
学 号 ： 2022302012004
专 业 ： 数学与应用数学
学 院 ： 数学与统计学院
指导教师 ： 高付清
二〇二六年四月

## Page 2

原创性声明
本人郑重声明：所呈交的论文（设计），是本人在指导教师的指导下，严格
按照学校和学院有关规定完成的。除文中已经标明引用的内容外，本论文（设计）
不包含任何其他个人或集体已发表及撰写的研究成果。对本论文（设计）做出贡
献的个人和集体，均已在文中以明确方式标明。本人承诺在论文（设计）工作过
程中没有伪造数据等行为。若在本论文（设计）中有侵犯任何方面知识产权的行
为，由本人承担相应的法律责任。
作者签名： 指导教师签名：
日 期： 年 月 日
版权使用授权书
本人完全了解武汉大学有权保留并向有关部门或机构送交本论文（设计）的
复印件和电子版，允许本论文（设计）被查阅和借阅。本人授权武汉大学将本论
文的全部或部分内容编入有关数据进行检索和传播，可以采用影印、缩印或扫描
等复制手段保存和汇编本论文（设计）。
作者签名： 指导教师签名：
日 期： 年 月 日

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
1.2 1.2国内外研究现状.................................................. 2
1.3 1.3研究问题与本文贡献............................................. 2
1.4 1.4本章小结 ......................................................... 3
2 第 2 章理论基础 3
2.1 2.1Black-Scholes模型与欧式看涨期权解析解 ...................... 3
2.2 2.2MonteCarlo与MCMC 估计框架 ................................ 4
2.3 2.3RWMH与MTM 机制............................................ 5
2.4 2.4统计诊断指标 .................................................... 6
2.5 2.5本章小结 ......................................................... 7
3 第 3 章方法与实现 7
3.1 3.1项目结构与模块职责............................................. 7
3.2 3.2扩展算法方案说明 ............................................... 8
3.3 3.3参数设置与可复现策略 .......................................... 9
3.4 3.4本章小结 ......................................................... 9
4 第 4 章实验结果与分析 10
4.1 4.1实验设计与评价指标............................................. 10
4.2 4.2基础结果对比 .................................................... 10
4.3 4.3速度与效率的权衡分析 .......................................... 11
4.4 4.4与MonteCarlo基线比较......................................... 12
4.5 4.5图示证据与可视化说明 .......................................... 12
4.6 4.6差异来源与有效性讨论 .......................................... 14
III

## Page 6

武汉大学本科毕业论文（设计）
4.7 4.7本章小结 ......................................................... 15
5 第 5 章结论与展望 15
5.1 5.1主要结论 ......................................................... 15
5.2 5.2研究局限 ......................................................... 15
5.3 5.3未来工作 ......................................................... 15
5.4 5.4本章小结 ......................................................... 16
6 参考文献 17
7 附录 19
7.1 附录A 复现实验环境与命令 ........................................ 19
7.2 附录B 冲突处理与证据追溯规则.................................... 19
7.3 附录C 关键函数说明 ................................................ 20
7.4 附录D 伪代码汇总 .................................................. 20
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
但在复杂目标分布下效率受限[5][6]。马尔可夫链蒙特卡洛（MCMC）通过构造平稳
分布为目标分布的马尔可夫链完成抽样，避免直接采样困难[3][4][7]。单提案RWMH
实现简单，但样本相关性较高时会降低有效样本产出。多提案MTM在一次迭代中产
生多个候选点并进行加权选择，在既有文献与本项目实验中均表现出更强的混合能力
[8]。
从本科毕业论文角度，本研究价值在于：一方面，展示概率模型、数值算法与统
计诊断指标的系统衔接；另一方面，给出 “统计效率与计算成本” 共同衡量的实验分
析路径，体现应用统计问题中的方法选择逻辑。
图1-1展示本研究的总体技术路线：模型定义、采样算法设计、指标评估与结果
解释。
图1-1: 研究技术路线示意图
1

## Page 8

武汉大学本科毕业论文（设计）
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
构。
表1-1给出本文所依托研究脉络与项目对应关系。
研究方向 代表方法 本项目对应
解析定价 Black-Scholes公式 call_price_analytical
随机模拟 MonteCarlo run_baseline_comparison（MC基准）
MCMC单提案 RWMH RandomWalkMetropolis.sample
MCMC多提案 MTM/LB-MTM MultipleTryMetropolis.sample、LocallyBalancedMTM.sample
表1-1研究脉络与项目实现对应关系
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
进一步地，为了说明 Black-Scholes 公式的随机微分来源，可由伊藤引理对
f(S ,t) = lnS 求微分。由
t t
dS = rS dt+σS dW
t t t t
得到
( )
1
dlnS = r− σ2 dt+σdW .
t t
2
两边积分可得
( )
1
lnS = lnS + r− σ2 T +σW ,
T 0 T
2
即
[( ) ]
√
1
S = S exp r− σ2 T +σ TZ , Z ∼ N(0,1).
T 0
2
在风险中性定价下，欧式看涨期权满足
C = e −rTEQ [(S −K)+].
0 T
结合上式对数正态分布积分可得到 Black-Scholes 闭式解。本文后续数值实验以
该解析解作为精度基准。
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
4

## Page 11

武汉大学本科毕业论文（设计）
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
5

## Page 12

武汉大学本科毕业论文（设计）
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
图2-1展示ACF随滞后变化的典型对比结果。
6

## Page 13

武汉大学本科毕业论文（设计）
图2-1: ACF对比示意
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
MultipleTryMetropolis负责采样，run_*系列函数负责实验编排和结果输出。
图3-1给出“源码到论文章节”的映射关系示意。
7

## Page 14

武汉大学本科毕业论文（设计）
图3-1: 源码模块映射图
3.2 扩展算法方案说明
除基础 RWMH 与 MTM 外，项目还实现了两类扩展方案，以提升论文的方法深
度与比较维度。
1. LocallyBalancedMTM（LB-MTM）：在候选点加权阶段引入局部平衡权重，优
先选择与当前状态局部几何更匹配的候选，提高接受行为稳定性。其权重形式
见第2章公式：
( )
logπ(y)−logπ(x)
w (y|x) = exp .
LB
τ
在实现中，τ 控制了“局部平衡偏好”的强弱：当τ 较小时，算法更偏向高后验候
选；当 τ 较大时，行为更接近标准 MTM 权重。该设计的目的不是单纯提高接受率，
而是降低链在局部区域内的往返震荡，从而改善ACF与IAT。
2. ParallelMulti-ChainMTM（Parallel-MTM）：采用多链并行采样并在后处理阶
段汇总样本，用于提高单位墙钟时间下的样本产出。该方案在代码层由多链调
度与结果汇总模块实现。
Parallel-MTM的关键思想是把“样本数增长”与“单链混合”拆分处理：每条链独
立执行MTM更新，最终将各链样本拼接并统一计算统计量。其理想加速依赖多核资
源与实现开销，理论上链间可近似线性并行，但在 Python 串行/半并行环境下会受到
进程管理、内存复制与汇总阶段开销影响，因此应结合ESS/s与墙钟时间共同评价。
在收敛诊断方面，run_advanced_comparison 给出了 Geweke 检验结果：MTM-
K4、LB-MTM与Parallel-MTM均满足(|z|<1.96)的常用阈值，而RWMH在该实验中
8

## Page 15

武汉大学本科毕业论文（设计）
未通过。该现象与第 4 章 “统计效率改善但时间开销上升” 的主结论方向一致，表明
扩展方案在收敛稳定性上具备可验证优势。
说明：为避免正文冗长，RWMH、MTM与实验流程伪代码统一移动至附录D。
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
参数类别 参数名 取值 来源
模型参数 S ,K,T,r,σ 100,100,1,0.05,0.2 run_*默认参数
0
采样设置 n_samples 20000/50000 run_comparison,run_baseline_comparison
提案设置 proposal_std,k_proposals 0.3,2/4/8 RandomWalkMetropolis,MultipleTryMetropolis
随机性控制 seed 42 主程序入口
表3-2实验参数清单
3.4 本章小结
本章从实现层面给出了算法到代码的对应关系与实验流程。下一章将对结果进行
定量整理，并讨论统计效率提升与计算时间成本之间的权衡关系。
9

## Page 16

武汉大学本科毕业论文（设计）
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
4.2 基础结果对比
表 4-1 给出主比较实验（seed=42）的核心指标。为避免表格过宽，5 次重
复实验统计单列为表 4-1(b)（解析解为基准，主实验配置：n_samples=20000,
burn_in=n_samples//4, proposal_std=0.3, seed=42；重复实验种子：42~46）。
方法 价格估计 绝对误差 接受率 时间(s) IAT ESS
解析解 10.450584 - - - - -
RWMH 10.7591 0.3085 59.21% 0.88 10.0 2000
MTM-K2 10.2750 0.1756 72.15% 5.79 6.0 3333
MTM-K4 10.3573 0.0933 80.40% 9.25 5.0 4000
MTM-K8 10.5741 0.1235 84.98% 15.91 5.0 4000
表4-1(a)主比较核心指标（seed=42）
10

## Page 17

武汉大学本科毕业论文（设计）
方法 价格均值±std(5次)
RWMH 10.6913±0.3077
MTM-K2 10.5253±0.1922
MTM-K4 10.5119±0.2266
MTM-K8 10.4107±0.1678
表4-1(b)5次重复实验价格均值±标准差
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
4 9.090 5.0 0.11x 1.60x
8 15.961 5.0 0.06x 1.60x
表4-2Speedup分析结果
结果表明，在当前串行实现中，K 增大时 IAT 由 8.0 下降至 5.0，但运行时间由
1.023s上升至15.961s，因此墙钟时间不呈现加速。该现象由run_speedup_analysis
11

## Page 18

武汉大学本科毕业论文（设计）
实验日志直接支持（证据来源：src/mcmc_optimized.py；配置：n_samples=20000,
burn_in=n_samples//4, proposal_std=0.3；种子：42）。
4.4 与 Monte Carlo 基线比较
基 于 run_baseline_comparison 的 复 算 记 录 （证 据 来 源：
src/mcmc_optimized.py； 配 置：n_samples=50000, burn_in=n_samples//4；
随机种子：42），可得到表4-3所示结论。
方法 价格 误差 标准误 时间(s) IAT ESS
MonteCarlo 10.4462 0.0044 0.0657 0.0010 - -
MCMC(RWMH) 10.4643 0.0137 - 2.48 8.0 6250
表4-3MonteCarlo与MCMC基线比较
对于当前低维、目标分布可直接采样的场景，MC具有明显时间优势；MCMC的
核心价值更多体现在复杂目标分布、后验推断或高维问题中。
4.5 图示证据与可视化说明
本项目可视化脚本src/visualization_optimized.py生成如下关键图：
• 图 4-1 综合分析图：comprehensive_analysis.png（样本路径、分布、ACF、
IAT/ESS对比）；
• 图4-2加速曲线图：speedup_curves.png（时间、IAT、ESS/s随K变化）；
• 图4-3辅助比较图：mcmc_comparison.png（用于展示方法对比关系）。
12

## Page 19

武汉大学本科毕业论文（设计）
图4-1: 综合分析图
图4-2: 加速曲线图
图4-3: MCMC比较图
13

## Page 20

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
8.8；MTM-K2: 6.0；MTM-K4: 5.8；MTM-K8: 5.4）。在扩展实验中，LB-MTM与Parallel-
MTM 的 Geweke 诊断同样通过阈值，说明多提案机制在不同实现形态下具有一致的
收敛优势趋势。
表4-4给出高级扩展方法的Geweke诊断对比（阈值(|z|<1.96)）：
方法 Gewekez值 是否通过
RWMH -2.90 否
MTM-K4 -0.08 是
LB-MTM 0.43 是
Parallel-MTM -0.75 是
表4-4高级扩展方法Geweke诊断对比
基于表 4-4 可进一步作两点解释。第一，LB-MTM 与 Parallel-MTM 的 z 值绝对
值均显著低于阈值，说明链前段与后段均值差异不显著，样本均值估计更稳定；第二，
RWMH 的 z 值为 -2.90，提示该链在当前样本规模下仍存在明显阶段性偏移。综合第
4.2 与第 4.3 结果可知：扩展 MTM 方案在 “收敛稳定性” 和 “相关性控制” 方面优于
RWMH，但其工程收益仍受实现方式影响，后续应优先在真并行环境中评估ESS/s改
善幅度。
14

## Page 21

武汉大学本科毕业论文（设计）
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
15

## Page 22

武汉大学本科毕业论文（设计）
3. 引入自适应提案尺度与自适应K选择策略；
4. 完善收敛诊断体系（R-hat、多链一致性检验）。
表5-1总结本文结论、局限与展望对应关系。
维度 当前结论 后续改进
统计效率 MTM在IAT/ESS上有优势 扩展到高维任务验证稳健性
时间效率 串行环境下时间成本偏高 并行化实现与硬件加速
诊断完整性 已含ACF/IAT/ESS/Geweke 增加多链一致性指标
表5-1结论、局限与展望对应关系
5.4 本章小结
本文完成了面向本科毕业论文要求的研究闭环：问题提出、理论推导、算法实现、
实验比较与结论提炼。整体结果支持 “多提案提升统计效率但存在计算代价” 的核心
判断。
16

## Page 23

武汉大学本科毕业论文（设计）
参考文献
[1] Black F, Scholes M. The pricing of options and corporate liabilities[J]. Journal of
PoliticalEconomy,1973,81(3): 637-654.
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
17

## Page 24

武汉大学本科毕业论文（设计）
致谢
在本论文的选题、实现与写作过程中，指导教师在研究方向、方法论与论文结构
方面给予了持续、细致的指导与帮助；在实验复现与结论论证阶段，老师对关键问题
的纠偏与建议对论文质量提升起到了决定性作用。在此谨致诚挚感谢。
同时，感谢学院与任课教师在本科阶段提供的系统训练，感谢同学在代码测试、
文稿校对与学术交流中的支持与建议。本文仍存在不足，恳请各位老师批评指正。
18

## Page 25

武汉大学本科毕业论文（设计）
附录
附录 A 复现实验环境与命令
• 分支：master（当前同步后的主分支）
• 关键脚本：
– src/mcmc_option_pricing.py
– src/mcmc_optimized.py
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
19

## Page 26

武汉大学本科毕业论文（设计）
附录 C 关键函数说明
模块 函数/类 作用
mcmc_option_pricing.py call_price_analytical 欧式看涨期权解析价
mcmc_option_pricing.py RandomWalkMetropolis.sample 单提案MCMC采样
mcmc_option_pricing.py MultipleTryMetropolis.sample 多提案MCMC采样
mcmc_optimized.py run_baseline_comparison MC与MCMC基准比较
mcmc_optimized.py run_comparison RWMH/MTM核心性能比较
mcmc_optimized.py run_speedup_analysis 不同K的速度与IAT分析
mcmc_advanced.py LocallyBalancedMTM.sample 局部平衡多提案采样
mcmc_advanced.py run_advanced_comparison 高级对比与Geweke诊断
表C-1关键函数说明
附录 D 伪代码汇总
Algorithm D1: RWMH
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
Algorithm D2: MTM
Input: target log density log￿, proposal count K, proposal std s
Initialize x
20

## Page 27

武汉大学本科毕业论文（设计）
for each iteration:
generate forward set y1,...,yK from Normal(x, s^2)
compute forward weights wj = exp(log￿(yj) - max log￿(y))
sample y* from normalized forward weights
build backward set: x plus K-1 draws from Normal(y*, s^2)
compute log_accept_ratio = logsumexp(log￿(forward set)) - logsumexp(log￿(backward set))
accept or reject y*
Output: samples, acceptance rate
Algorithm D3: Experiment Workflow
Set model params (S0, K, T, r, sigma)
Run samplers (RWMH / MTM-K2 / MTM-K4 / MTM-K8 / LB-MTM / Parallel-MTM)
Transform log-price samples to discounted payoffs
Compute ACF, IAT, ESS, acceptance rate and runtime
Compare error to analytical price and summarize trade-offs
21

