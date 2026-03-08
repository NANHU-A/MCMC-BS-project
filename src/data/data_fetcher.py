"""
金融数据获取与处理模块
支持从多种数据源获取数据，用于量化分析和模型校准
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings("ignore")


class FinancialData:
    """金融数据获取与处理类"""

    def __init__(self, cache_dir=None):
        """
        初始化数据处理器

        Args:
            cache_dir: 缓存目录 (可选)
        """
        self.cache_dir = cache_dir

    def get_stock_data(self, symbol, start_date, end_date, interval="1d"):
        """
        获取股票历史数据

        Args:
            symbol: 股票代码 (如 'AAPL', '000001.SS' 上证指数)
            start_date: 开始日期 (YYYY-MM-DD 或 datetime)
            end_date: 结束日期 (YYYY-MM-DD 或 datetime)
            interval: 数据频率 ('1d', '1h', '1m'等)

        Returns:
            df: 包含OHLCV数据的DataFrame
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval=interval)

            if df.empty:
                raise ValueError(f"未找到 {symbol} 的数据")

            # 计算对数收益率和波动率
            df["log_return"] = np.log(df["Close"] / df["Close"].shift(1))
            df["realized_volatility"] = df["log_return"].rolling(
                window=20
            ).std() * np.sqrt(252)

            print(f"获取 {symbol} 数据成功: {len(df)} 条记录")
            return df

        except Exception as e:
            print(f"获取数据失败: {e}")
            # 返回模拟数据供测试
            return self._generate_mock_data(start_date, end_date)

    def get_option_chain(self, symbol, expiration_date=None):
        """
        获取期权链数据

        Args:
            symbol: 标的资产代码
            expiration_date: 到期日 (可选)

        Returns:
            calls_df: 看涨期权数据
            puts_df: 看跌期权数据
        """
        try:
            ticker = yf.Ticker(symbol)
            options_dates = ticker.options

            if not options_dates:
                print(f"{symbol} 无期权数据")
                return None, None

            if expiration_date is None:
                expiration_date = options_dates[0]  # 选择最近的到期日

            option_chain = ticker.option_chain(expiration_date)

            print(f"获取 {symbol} 期权数据成功: {expiration_date}")
            return option_chain.calls, option_chain.puts

        except Exception as e:
            print(f"获取期权数据失败: {e}")
            return None, None

    def get_risk_free_rate(self, country="US"):
        """
        获取无风险利率

        Args:
            country: 国家 ('US', 'CN'等)

        Returns:
            rate: 年化无风险利率
        """
        # 简化版本 - 实际应从权威数据源获取
        risk_free_rates = {
            "US": 0.05,  # 5%
            "CN": 0.03,  # 3%
            "EU": 0.04,  # 4%
            "JP": 0.01,  # 1%
        }

        rate = risk_free_rates.get(country, 0.03)
        print(f"{country} 无风险利率: {rate * 100:.2f}%")

        return rate

    def calculate_implied_volatility(
        self, market_price, S, K, T, r, option_type="call", method="bisection"
    ):
        """
        计算隐含波动率

        Args:
            market_price: 期权市场价格
            S: 标的资产现价
            K: 行权价
            T: 到期时间 (年)
            r: 无风险利率
            option_type: 期权类型 ('call' 或 'put')
            method: 计算方法 ('bisection' 或 'newton')

        Returns:
            implied_vol: 隐含波动率
        """
        from scipy.stats import norm

        def black_scholes_price(sigma, option_type="call"):
            d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)

            if option_type == "call":
                return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
            else:  # put
                return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

        # 二分法
        if method == "bisection":
            low, high = 0.001, 5.0
            tol = 1e-6
            max_iter = 100

            for i in range(max_iter):
                mid = (low + high) / 2
                price_mid = black_scholes_price(mid, option_type)

                if abs(price_mid - market_price) < tol:
                    return mid

                if price_mid < market_price:
                    low = mid
                else:
                    high = mid

            return (low + high) / 2

        # Newton法
        elif method == "newton":
            sigma = 0.3  # 初始猜测
            tol = 1e-6
            max_iter = 50

            for i in range(max_iter):
                # Black-Scholes价格
                d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
                price = black_scholes_price(sigma, option_type)

                # Vega (波动率导数)
                vega = S * norm.pdf(d1) * np.sqrt(T)

                if abs(vega) < 1e-10:
                    break

                # Newton更新
                sigma_new = sigma - (price - market_price) / vega

                if abs(sigma_new - sigma) < tol:
                    return sigma_new

                sigma = max(sigma_new, 0.001)  # 保持正数

            return sigma

        else:
            raise ValueError(f"未知方法: {method}")

    def calculate_historical_volatility(self, prices, window=20, annualize=True):
        """
        计算历史波动率

        Args:
            prices: 价格序列
            window: 滚动窗口大小
            annualize: 是否年化

        Returns:
            historical_vol: 历史波动率序列
        """
        returns = np.log(prices / prices.shift(1))
        historical_vol = returns.rolling(window=window).std()

        if annualize:
            # 年化因子: 假设252个交易日
            historical_vol = historical_vol * np.sqrt(252)

        return historical_vol

    def prepare_training_data(
        self, symbol, start_date, end_date, lookback_window=252, test_size=0.2
    ):
        """
        准备训练和测试数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            lookback_window: 回看窗口大小
            test_size: 测试集比例

        Returns:
            train_data: 训练数据
            test_data: 测试数据
            features: 特征列表
        """
        # 获取数据
        df = self.get_stock_data(symbol, start_date, end_date)

        if df.empty:
            raise ValueError("无法获取数据")

        # 特征工程
        features = []

        # 价格相关特征
        df["returns"] = df["Close"].pct_change()
        df["log_returns"] = np.log(df["Close"] / df["Close"].shift(1))
        features.append("log_returns")

        # 技术指标
        df["ma_5"] = df["Close"].rolling(5).mean()
        df["ma_20"] = df["Close"].rolling(20).mean()
        df["ma_50"] = df["Close"].rolling(50).mean()
        features.extend(["ma_5", "ma_20", "ma_50"])

        df["ma_ratio_5_20"] = df["ma_5"] / df["ma_20"]
        df["ma_ratio_20_50"] = df["ma_20"] / df["ma_50"]
        features.extend(["ma_ratio_5_20", "ma_ratio_20_50"])

        # 波动率特征
        df["volatility_20"] = df["log_returns"].rolling(20).std() * np.sqrt(252)
        df["volatility_50"] = df["log_returns"].rolling(50).std() * np.sqrt(252)
        features.extend(["volatility_20", "volatility_50"])

        # 成交量特征
        df["volume_ma_5"] = df["Volume"].rolling(5).mean()
        df["volume_ma_20"] = df["Volume"].rolling(20).mean()
        df["volume_ratio"] = df["Volume"] / df["volume_ma_20"]
        features.extend(["volume_ma_5", "volume_ma_20", "volume_ratio"])

        # 价格动量
        df["momentum_5"] = df["Close"] / df["Close"].shift(5) - 1
        df["momentum_20"] = df["Close"] / df["Close"].shift(20) - 1
        features.extend(["momentum_5", "momentum_20"])

        # 目标变量: 未来N日收益率
        n_future = 5
        df["target"] = df["Close"].shift(-n_future) / df["Close"] - 1

        # 清理数据
        df = df.dropna()

        # 分割训练集和测试集
        split_idx = int(len(df) * (1 - test_size))
        train_data = df.iloc[:split_idx].copy()
        test_data = df.iloc[split_idx:].copy()

        print(f"数据准备完成: 训练集 {len(train_data)} 条, 测试集 {len(test_data)} 条")
        print(f"特征数量: {len(features)}")

        return train_data, test_data, features

    def _generate_mock_data(self, start_date, end_date, freq="B"):
        """
        生成模拟数据用于测试

        Args:
            start_date: 开始日期
            end_date: 结束日期
            freq: 频率 ('B' 工作日, 'D' 日历日)

        Returns:
            df: 模拟数据DataFrame
        """
        # 生成日期范围
        dates = pd.date_range(start=start_date, end=end_date, freq=freq)
        n_days = len(dates)

        # 生成模拟价格 (几何布朗运动)
        np.random.seed(42)
        mu = 0.0002  # 日度漂移
        sigma = 0.02  # 日度波动率
        dt = 1

        returns = np.random.normal(mu * dt, sigma * np.sqrt(dt), n_days)
        prices = 100 * np.exp(np.cumsum(returns))

        # 创建DataFrame
        df = pd.DataFrame(
            {
                "Date": dates,
                "Open": prices * 0.99,
                "High": prices * 1.02,
                "Low": prices * 0.98,
                "Close": prices,
                "Volume": np.random.lognormal(15, 1, n_days),
            }
        )
        df.set_index("Date", inplace=True)

        # 计算收益率和波动率
        df["log_return"] = np.log(df["Close"] / df["Close"].shift(1))
        df["realized_volatility"] = df["log_return"].rolling(window=20).std() * np.sqrt(
            252
        )

        print(f"生成模拟数据: {n_days} 条记录")

        return df


class OptionDataProcessor:
    """期权数据处理类"""

    def __init__(self):
        pass

    def calculate_iv_surface(self, calls_df, puts_df, S, r, T):
        """
        计算隐含波动率曲面

        Args:
            calls_df: 看涨期权数据
            puts_df: 看跌期权数据
            S: 标的资产价格
            r: 无风险利率
            T: 到期时间 (年)

        Returns:
            iv_surface: 隐含波动率曲面
        """
        if calls_df is None or puts_df is None:
            return None

        # 合并call和put数据
        calls_df["option_type"] = "call"
        puts_df["option_type"] = "put"
        all_options = pd.concat([calls_df, puts_df], ignore_index=True)

        # 计算隐含波动率
        iv_list = []

        for _, row in all_options.iterrows():
            K = row["strike"]
            market_price = (row["bid"] + row["ask"]) / 2

            if market_price <= 0:
                continue

            try:
                iv = FinancialData().calculate_implied_volatility(
                    market_price, S, K, T, r, option_type=row["option_type"]
                )
                iv_list.append(
                    {
                        "strike": K,
                        "moneyness": K / S,  # 虚实程度
                        "iv": iv,
                        "option_type": row["option_type"],
                    }
                )
            except:
                continue

        iv_df = pd.DataFrame(iv_list)

        return iv_df

    def detect_volatility_smile(self, iv_df):
        """
        检测波动率微笑

        Args:
            iv_df: 隐含波动率DataFrame

        Returns:
            smile_detected: 是否检测到微笑
            smile_strength: 微笑强度
        """
        if iv_df.empty or len(iv_df) < 5:
            return False, 0.0

        # 按行权价排序
        iv_df = iv_df.sort_values("moneyness")

        # 使用二次多项式拟合
        from scipy import stats

        X = iv_df["moneyness"].values
        y = iv_df["iv"].values

        try:
            # 二次多项式拟合
            coeffs = np.polyfit(X, y, 2)

            # 判断是否为凸函数 (二次项系数 > 0 表示微笑)
            a2 = coeffs[0]

            smile_detected = a2 > 0
            smile_strength = abs(a2)

            return smile_detected, smile_strength

        except:
            return False, 0.0
