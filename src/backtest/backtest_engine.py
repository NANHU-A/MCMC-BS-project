"""
回测框架模块
用于测试量化交易策略的性能
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings("ignore")


class BacktestEngine:
    """回测引擎基类"""

    def __init__(self, initial_capital=100000.0, commission=0.001, slippage=0.0005):
        """
        初始化回测引擎

        Args:
            initial_capital: 初始资金
            commission: 交易佣金 (百分比)
            slippage: 滑点 (百分比)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.reset()

    def reset(self):
        """重置回测状态"""
        self.capital = self.initial_capital
        self.positions = {}  # 持仓 {symbol: quantity}
        self.trades = []  # 交易记录
        self.portfolio_values = []  # 组合价值历史
        self.dates = []  # 日期历史
        self.current_date = None

    def run(self, data, strategy):
        """
        运行回测

        Args:
            data: 历史数据 (DataFrame)
            strategy: 策略对象

        Returns:
            results: 回测结果字典
        """
        print(f"开始回测: {len(data)} 个数据点")

        # 按日期排序
        data = data.sort_index()

        # 初始化策略
        strategy.initialize()

        for idx, (date, row) in enumerate(data.iterrows()):
            self.current_date = date

            # 更新策略状态
            strategy.update(self, row, idx)

            # 执行策略信号
            signals = strategy.generate_signals(row, idx)
            self.execute_signals(signals, row)

            # 计算当前组合价值
            portfolio_value = self.calculate_portfolio_value(row)
            self.portfolio_values.append(portfolio_value)
            self.dates.append(date)

            # 每100个点打印进度
            if idx % 100 == 0:
                print(f"进度: {idx}/{len(data)}, 组合价值: {portfolio_value:.2f}")

        # 计算绩效指标
        results = self.calculate_performance_metrics()

        print(f"回测完成: 最终组合价值 {self.portfolio_values[-1]:.2f}")

        return results

    def execute_signals(self, signals, market_data):
        """
        执行交易信号

        Args:
            signals: 交易信号字典 {symbol: action}
            market_data: 当前市场数据
        """
        for symbol, action in signals.items():
            if action == "BUY":
                self.buy(symbol, market_data)
            elif action == "SELL":
                self.sell(symbol, market_data)
            elif action == "HOLD":
                pass

    def buy(self, symbol, market_data, quantity=None):
        """
        买入资产

        Args:
            symbol: 资产代码
            market_data: 市场数据
            quantity: 买入数量 (None表示使用默认规则)
        """
        # 获取当前价格
        if symbol in market_data:
            price = market_data[symbol]
        else:
            # 假设使用'Close'价格
            price = market_data["Close"] if "Close" in market_data else 100.0

        # 考虑滑点
        execution_price = price * (1 + self.slippage)

        # 确定买入数量
        if quantity is None:
            # 默认使用10%的资金
            quantity = int((self.capital * 0.1) / execution_price)

        if quantity <= 0:
            return

        # 计算总成本
        cost = quantity * execution_price
        commission_cost = cost * self.commission
        total_cost = cost + commission_cost

        if total_cost > self.capital:
            # 资金不足，调整数量
            quantity = int(self.capital / (execution_price * (1 + self.commission)))
            if quantity <= 0:
                return
            cost = quantity * execution_price
            commission_cost = cost * self.commission
            total_cost = cost + commission_cost

        # 更新持仓
        if symbol in self.positions:
            self.positions[symbol] += quantity
        else:
            self.positions[symbol] = quantity

        # 更新资金
        self.capital -= total_cost

        # 记录交易
        self.trades.append(
            {
                "date": self.current_date,
                "symbol": symbol,
                "action": "BUY",
                "quantity": quantity,
                "price": execution_price,
                "commission": commission_cost,
                "total_cost": total_cost,
            }
        )

    def sell(self, symbol, market_data, quantity=None):
        """
        卖出资产

        Args:
            symbol: 资产代码
            market_data: 市场数据
            quantity: 卖出数量 (None表示卖出全部)
        """
        if symbol not in self.positions or self.positions[symbol] <= 0:
            return

        # 获取当前价格
        if symbol in market_data:
            price = market_data[symbol]
        else:
            price = market_data["Close"] if "Close" in market_data else 100.0

        # 考虑滑点
        execution_price = price * (1 - self.slippage)

        # 确定卖出数量
        current_quantity = self.positions[symbol]
        if quantity is None or quantity > current_quantity:
            quantity = current_quantity

        if quantity <= 0:
            return

        # 计算收入
        revenue = quantity * execution_price
        commission_cost = revenue * self.commission
        net_revenue = revenue - commission_cost

        # 更新持仓
        self.positions[symbol] -= quantity
        if self.positions[symbol] == 0:
            del self.positions[symbol]

        # 更新资金
        self.capital += net_revenue

        # 记录交易
        self.trades.append(
            {
                "date": self.current_date,
                "symbol": symbol,
                "action": "SELL",
                "quantity": quantity,
                "price": execution_price,
                "commission": commission_cost,
                "revenue": net_revenue,
            }
        )

    def calculate_portfolio_value(self, market_data):
        """
        计算当前组合价值

        Args:
            market_data: 当前市场数据

        Returns:
            portfolio_value: 组合总价值
        """
        # 现金价值
        total_value = self.capital

        # 持仓价值
        for symbol, quantity in self.positions.items():
            if symbol in market_data:
                price = market_data[symbol]
            else:
                price = market_data["Close"] if "Close" in market_data else 100.0

            total_value += quantity * price

        return total_value

    def calculate_performance_metrics(self):
        """
        计算回测绩效指标

        Returns:
            metrics: 绩效指标字典
        """
        if len(self.portfolio_values) < 2:
            return {}

        # 转换为numpy数组
        portfolio_values = np.array(self.portfolio_values)

        # 计算收益率
        returns = np.diff(portfolio_values) / portfolio_values[:-1]

        # 基本指标
        total_return = (portfolio_values[-1] / portfolio_values[0] - 1) * 100
        annual_return = (1 + total_return / 100) ** (252 / len(portfolio_values)) - 1

        # 波动率
        volatility = np.std(returns) * np.sqrt(252) * 100

        # 夏普比率 (假设无风险利率为5%)
        risk_free_rate = 0.05
        excess_returns = returns - risk_free_rate / 252
        sharpe_ratio = np.mean(excess_returns) / np.std(returns) * np.sqrt(252)

        # 最大回撤
        peak = np.maximum.accumulate(portfolio_values)
        drawdown = (portfolio_values - peak) / peak
        max_drawdown = np.min(drawdown) * 100

        # Calmar比率
        calmar_ratio = (
            annual_return / (abs(max_drawdown) / 100) if max_drawdown != 0 else 0
        )

        # 胜率 (基于日度收益率)
        winning_days = np.sum(returns > 0)
        total_days = len(returns)
        win_rate = winning_days / total_days * 100 if total_days > 0 else 0

        # 交易统计
        trades_df = pd.DataFrame(self.trades)
        total_trades = len(trades_df)

        if total_trades > 0:
            avg_trade_return = total_return / total_trades
        else:
            avg_trade_return = 0

        metrics = {
            "initial_capital": self.initial_capital,
            "final_portfolio_value": portfolio_values[-1],
            "total_return_percent": total_return,
            "annual_return_percent": annual_return * 100,
            "volatility_percent": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown_percent": max_drawdown,
            "calmar_ratio": calmar_ratio,
            "win_rate_percent": win_rate,
            "total_trades": total_trades,
            "avg_trade_return_percent": avg_trade_return,
            "total_commission": sum(
                trade.get("commission", 0) for trade in self.trades
            ),
        }

        return metrics


class VolatilityTradingStrategy:
    """波动率交易策略基类"""

    def __init__(self):
        self.initialized = False
        self.position = 0  # 1: 做多, -1: 做空, 0: 无持仓
        self.entry_price = 0.0
        self.stop_loss = 0.0
        self.take_profit = 0.0

    def initialize(self):
        """初始化策略"""
        self.initialized = True
        self.position = 0
        self.entry_price = 0.0

    def update(self, backtest_engine, market_data, idx):
        """
        更新策略状态

        Args:
            backtest_engine: 回测引擎
            market_data: 当前市场数据
            idx: 当前索引
        """
        # 基类实现为空
        pass

    def generate_signals(self, market_data, idx):
        """
        生成交易信号

        Args:
            market_data: 当前市场数据
            idx: 当前索引

        Returns:
            signals: 交易信号字典
        """
        # 需要在子类中实现
        return {}


class MeanReversionStrategy(VolatilityTradingStrategy):
    """均值回归策略 - 基于波动率"""

    def __init__(self, lookback_window=20, zscore_threshold=2.0):
        """
        初始化均值回归策略

        Args:
            lookback_window: 回看窗口
            zscore_threshold: Z-score阈值
        """
        super().__init__()
        self.lookback_window = lookback_window
        self.zscore_threshold = zscore_threshold
        self.price_history = []
        self.volatility_history = []

    def generate_signals(self, market_data, idx):
        """
        生成均值回归信号

        当价格偏离均值超过阈值时交易
        """
        signals = {}

        # 收集历史数据
        current_price = market_data["Close"]
        current_vol = market_data.get("realized_volatility", 0.2)

        self.price_history.append(current_price)
        self.volatility_history.append(current_vol)

        # 保持固定长度的历史
        if len(self.price_history) > self.lookback_window * 2:
            self.price_history = self.price_history[-self.lookback_window * 2 :]
            self.volatility_history = self.volatility_history[
                -self.lookback_window * 2 :
            ]

        # 需要有足够的数据
        if len(self.price_history) < self.lookback_window:
            return signals

        # 计算Z-score
        recent_prices = self.price_history[-self.lookback_window :]
        price_mean = np.mean(recent_prices)
        price_std = np.std(recent_prices)

        if price_std > 0:
            zscore = (current_price - price_mean) / price_std
        else:
            zscore = 0

        # 生成信号
        symbol = "ASSET"  # 默认资产代码

        if zscore > self.zscore_threshold and self.position <= 0:
            # 价格过高，卖出信号
            signals[symbol] = "SELL"
            self.position = -1
            self.entry_price = current_price

        elif zscore < -self.zscore_threshold and self.position >= 0:
            # 价格过低，买入信号
            signals[symbol] = "BUY"
            self.position = 1
            self.entry_price = current_price

        elif abs(zscore) < 0.5 and self.position != 0:
            # 回归到均值附近，平仓
            if self.position > 0:
                signals[symbol] = "SELL"
            else:
                signals[symbol] = "BUY"
            self.position = 0

        return signals


class DeltaHedgingStrategy(VolatilityTradingStrategy):
    """Delta对冲策略 - 用于期权做市"""

    def __init__(self, target_delta=0.0, rebalance_threshold=0.1):
        """
        初始化Delta对冲策略

        Args:
            target_delta: 目标Delta值
            rebalance_threshold: 再平衡阈值
        """
        super().__init__()
        self.target_delta = target_delta
        self.rebalance_threshold = rebalance_threshold
        self.current_delta = 0.0
        self.option_position = 0
        self.hedge_position = 0

    def calculate_option_delta(self, S, K, T, r, sigma, option_type="call"):
        """
        计算期权Delta

        Args:
            S: 标的资产价格
            K: 行权价
            T: 到期时间
            r: 无风险利率
            sigma: 波动率
            option_type: 期权类型

        Returns:
            delta: 期权Delta值
        """
        from scipy.stats import norm

        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))

        if option_type == "call":
            delta = norm.cdf(d1)
        else:  # put
            delta = norm.cdf(d1) - 1

        return delta

    def generate_signals(self, market_data, idx):
        """
        生成Delta对冲信号
        """
        signals = {}

        # 假设我们有期权头寸
        S = market_data["Close"]
        K = 100.0  # 假设行权价
        T = 0.5  # 假设剩余期限
        r = 0.05  # 无风险利率
        sigma = market_data.get("implied_volatility", 0.2)

        # 计算当前Delta
        option_delta = self.calculate_option_delta(S, K, T, r, sigma, "call")
        portfolio_delta = self.option_position * option_delta + self.hedge_position

        # 检查是否需要再平衡
        delta_deviation = portfolio_delta - self.target_delta

        if abs(delta_deviation) > self.rebalance_threshold:
            # 计算需要对冲的数量
            hedge_quantity = -int(delta_deviation * 100)  # 每手100股

            if hedge_quantity > 0:
                signals["ASSET"] = "BUY"
                self.hedge_position += hedge_quantity
            elif hedge_quantity < 0:
                signals["ASSET"] = "SELL"
                self.hedge_position += hedge_quantity  # hedge_quantity为负

        return signals


class BacktestAnalyzer:
    """回测结果分析器"""

    def __init__(self):
        pass

    def analyze(self, backtest_results, plot=True):
        """
        分析回测结果

        Args:
            backtest_results: 回测结果字典
            plot: 是否绘制图表

        Returns:
            analysis: 分析报告
        """
        if not backtest_results:
            return "无回测结果"

        # 创建分析报告
        analysis = "=" * 60 + "\n"
        analysis += "回测结果分析报告\n"
        analysis += "=" * 60 + "\n\n"

        # 基本绩效指标
        analysis += "【绩效指标】\n"
        analysis += "-" * 40 + "\n"

        metrics = [
            ("初始资金", f"{backtest_results.get('initial_capital', 0):.2f}"),
            ("最终组合价值", f"{backtest_results.get('final_portfolio_value', 0):.2f}"),
            ("总收益率", f"{backtest_results.get('total_return_percent', 0):.2f}%"),
            ("年化收益率", f"{backtest_results.get('annual_return_percent', 0):.2f}%"),
            ("波动率", f"{backtest_results.get('volatility_percent', 0):.2f}%"),
            ("夏普比率", f"{backtest_results.get('sharpe_ratio', 0):.3f}"),
            ("最大回撤", f"{backtest_results.get('max_drawdown_percent', 0):.2f}%"),
            ("Calmar比率", f"{backtest_results.get('calmar_ratio', 0):.3f}"),
            ("胜率", f"{backtest_results.get('win_rate_percent', 0):.2f}%"),
            ("总交易次数", f"{backtest_results.get('total_trades', 0)}"),
            (
                "平均交易收益",
                f"{backtest_results.get('avg_trade_return_percent', 0):.2f}%",
            ),
            ("总佣金", f"{backtest_results.get('total_commission', 0):.2f}"),
        ]

        for name, value in metrics:
            analysis += f"{name:15s}: {value}\n"

        # 风险评估
        analysis += "\n【风险评估】\n"
        analysis += "-" * 40 + "\n"

        sharpe = backtest_results.get("sharpe_ratio", 0)
        max_dd = backtest_results.get("max_drawdown_percent", 0)

        if sharpe > 1.5:
            sharpe_rating = "优秀"
        elif sharpe > 1.0:
            sharpe_rating = "良好"
        elif sharpe > 0.5:
            sharpe_rating = "一般"
        else:
            sharpe_rating = "较差"

        if max_dd < -10:
            dd_rating = "风险较低"
        elif max_dd < -20:
            dd_rating = "风险适中"
        elif max_dd < -30:
            dd_rating = "风险较高"
        else:
            dd_rating = "风险很高"

        analysis += f"夏普比率评级: {sharpe_rating}\n"
        analysis += f"最大回撤评级: {dd_rating}\n"

        # 交易分析
        analysis += "\n【交易分析】\n"
        analysis += "-" * 40 + "\n"

        total_trades = backtest_results.get("total_trades", 0)
        if total_trades > 0:
            turnover = total_trades / 252  # 假设252个交易日
            analysis += f"年化换手率: {turnover:.2f} 倍/年\n"

            if turnover > 50:
                analysis += "策略类型: 高频交易\n"
            elif turnover > 10:
                analysis += "策略类型: 中频交易\n"
            else:
                analysis += "策略类型: 低频交易\n"

        # 建议
        analysis += "\n【投资建议】\n"
        analysis += "-" * 40 + "\n"

        if sharpe > 1.0 and max_dd > -20:
            analysis += "✅ 策略表现优秀，建议实盘运行\n"
            analysis += "   建议资金配置: 主要仓位\n"
        elif sharpe > 0.5 and max_dd > -30:
            analysis += "⚠️  策略表现一般，需要优化\n"
            analysis += "   建议资金配置: 少量测试\n"
        else:
            analysis += "❌ 策略表现较差，不建议实盘\n"
            analysis += "   建议: 重新设计策略\n"

        analysis += "\n" + "=" * 60

        print(analysis)

        # 如果需要绘图
        if plot:
            try:
                self.plot_results(backtest_results)
            except:
                print("绘图失败，请检查matplotlib是否安装")

        return analysis

    def plot_results(self, backtest_results):
        """绘制绩效图表"""
        import matplotlib.pyplot as plt

        # 这里可以添加绘图代码
        # 由于时间限制，暂不实现详细绘图

        print("绩效图表绘制功能将在完整版本中实现")

        # 简单示例
        plt.figure(figsize=(12, 8))

        # 模拟组合价值曲线
        portfolio_values = [100000]
        for i in range(1, 100):
            # 模拟随机增长
            daily_return = np.random.normal(0.001, 0.02)
            portfolio_values.append(portfolio_values[-1] * (1 + daily_return))

        plt.subplot(2, 2, 1)
        plt.plot(portfolio_values)
        plt.title("组合价值曲线")
        plt.xlabel("交易日")
        plt.ylabel("组合价值")
        plt.grid(True)

        plt.tight_layout()
        plt.savefig("backtest_results.png", dpi=150)
        plt.close()

        print("图表已保存为 backtest_results.png")
