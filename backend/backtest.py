"""
回测引擎模块
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from strategies.ma_strategy import MAStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.bollinger_strategy import BollingerStrategy
from strategies.kdj_strategy import KDJStrategy
from strategies.turtle_strategy import TurtleStrategy
from strategies.atr_strategy import ATRStrategy
from strategies.obv_strategy import OBVStrategy


class BacktestEngine:
    """
    回测引擎
    支持单个或多个策略组合
    """
    
    def __init__(self, initial_capital: float = 100000.0, commission_rate: float = 0.0003, price_mode: str = 'close'):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金，默认10万
            commission_rate: 手续费率，默认万分之三
            price_mode: 价格模式，'close'收盘价模式，'chase'追涨杀跌模式
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.price_mode = price_mode
        
    def create_strategy(self, strategy_config: Dict):
        """
        根据配置创建策略实例
        
        Args:
            strategy_config: 策略配置字典
            
        Returns:
            策略实例
        """
        strategy_type = strategy_config.get('type')
        params = strategy_config.get('params', {})
        
        if strategy_type == 'ma':
            short_period = params.get('short_period', {}).get('value', 5)
            long_period = params.get('long_period', {}).get('value', 20)
            return MAStrategy(short_period, long_period)
        elif strategy_type == 'macd':
            fast_period = params.get('fast_period', {}).get('value', 12)
            slow_period = params.get('slow_period', {}).get('value', 26)
            signal_period = params.get('signal_period', {}).get('value', 9)
            return MACDStrategy(fast_period, slow_period, signal_period)
        elif strategy_type == 'rsi':
            period = params.get('period', {}).get('value', 14)
            oversold = params.get('oversold', {}).get('value', 30)
            overbought = params.get('overbought', {}).get('value', 70)
            return RSIStrategy(period, oversold, overbought)
        elif strategy_type == 'bollinger':
            period = params.get('period', {}).get('value', 20)
            std_dev = params.get('std_dev', {}).get('value', 2.0)
            return BollingerStrategy(period, std_dev)
        elif strategy_type == 'kdj':
            n_period = params.get('n_period', {}).get('value', 9)
            m1_period = params.get('m1_period', {}).get('value', 3)
            m2_period = params.get('m2_period', {}).get('value', 3)
            return KDJStrategy(n_period, m1_period, m2_period)
        elif strategy_type == 'turtle':
            entry_period = params.get('entry_period', {}).get('value', 20)
            exit_period = params.get('exit_period', {}).get('value', 10)
            return TurtleStrategy(entry_period, exit_period)
        elif strategy_type == 'atr':
            period = params.get('period', {}).get('value', 14)
            multiplier = params.get('multiplier', {}).get('value', 2.0)
            return ATRStrategy(period, multiplier)
        elif strategy_type == 'obv':
            obv_period = params.get('obv_period', {}).get('value', 20)
            ma_period = params.get('ma_period', {}).get('value', 10)
            return OBVStrategy(obv_period, ma_period)
        else:
            raise ValueError(f"未知策略类型: {strategy_type}")
    
    def combine_signals(self, df: pd.DataFrame, strategies: List) -> pd.DataFrame:
        """
        组合多个策略的信号
        买入：超过半数策略发出买入信号（谨慎买入）
        卖出：任一策略发出卖出信号（果断卖出）
        
        Args:
            df: 原始数据
            strategies: 策略列表
            
        Returns:
            组合后的信号DataFrame
        """
        if not strategies:
            return df
        
        # 获取每个策略的信号
        signal_dfs = []
        for strategy in strategies:
            strategy_df = strategy.generate_signals(df.copy())
            signal_dfs.append(strategy_df['signal'])
        
        # 组合信号
        combined_signal = pd.DataFrame(signal_dfs).T
        df['signal'] = 0
        
        num_strategies = len(strategies)
        
        # 买入：超过半数策略发出买入信号（谨慎）
        buy_mask = (combined_signal == 1).sum(axis=1) > num_strategies / 2
        # 卖出：任一策略发出卖出信号（果断）
        sell_mask = (combined_signal == -1).any(axis=1)
        
        df.loc[buy_mask, 'signal'] = 1
        df.loc[sell_mask, 'signal'] = -1
        
        return df
    
    def run_backtest(self, df: pd.DataFrame, strategy_configs: List[Dict]) -> Dict[str, Any]:
        """
        执行回测
        
        Args:
            df: 股票数据
            strategy_configs: 策略配置列表
            
        Returns:
            回测结果字典
        """
        # 创建策略实例
        strategies = [self.create_strategy(config) for config in strategy_configs]
        
        # 组合信号
        if len(strategies) == 1:
            df = strategies[0].generate_signals(df.copy())
        else:
            df = self.combine_signals(df.copy(), strategies)
        
        # 模拟交易
        capital = self.initial_capital
        position = 0  # 持仓数量
        trades = []  # 交易记录
        equity_curve = []  # 资金曲线
        
        for idx, row in df.iterrows():
            date = row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], pd.Timestamp) else str(row['date'])
            
            # 根据价格模式确定买卖价格
            if self.price_mode == 'chase':
                # 追涨杀跌模式：买入用最高价，卖出用最低价
                buy_price = row['high']
                sell_price = row['low']
            else:
                # 收盘价模式：买卖都用收盘价
                buy_price = row['close']
                sell_price = row['close']
            
            # 买入
            if row['signal'] == 1 and position == 0:
                # 计算可买入数量（100股为一手）
                max_shares = int(capital / buy_price / 100) * 100
                if max_shares > 0:
                    cost = max_shares * buy_price * (1 + self.commission_rate)
                    capital -= cost
                    position = max_shares
                    trades.append({
                        'date': date,
                        'type': 'buy',
                        'price': buy_price,
                        'shares': position,
                        'capital': capital + position * buy_price
                    })
            
            # 卖出
            elif row['signal'] == -1 and position > 0:
                revenue = position * sell_price * (1 - self.commission_rate)
                capital += revenue
                trades.append({
                    'date': date,
                    'type': 'sell',
                    'price': sell_price,
                    'shares': position,
                    'capital': capital
                })
                position = 0
            
            # 记录资金曲线（使用收盘价计算当前市值）
            total_value = capital + position * row['close']
            equity_curve.append({
                'date': date,
                'value': total_value
            })
        
        # 计算统计数据
        final_value = capital + position * df.iloc[-1]['close']
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100
        
        # 计算胜率
        win_count = 0
        total_trades = len(trades) // 2  # 买卖成对
        
        for i in range(0, len(trades) - 1, 2):
            if i + 1 < len(trades):
                buy_trade = trades[i]
                sell_trade = trades[i + 1]
                if sell_trade['price'] > buy_trade['price']:
                    win_count += 1
        
        win_rate = win_count / total_trades * 100 if total_trades > 0 else 0
        
        # 获取买卖点
        buy_points = [t for t in trades if t['type'] == 'buy']
        sell_points = [t for t in trades if t['type'] == 'sell']
        
        # 获取指标数据，分类存储
        ma_indicators = {}  # 均线指标（用于K线图）
        macd_indicators = {}  # MACD指标（用于单独的指标图）
        
        for strategy in strategies:
            indicator_data = strategy.get_indicator_data(df)
            for key, value in indicator_data.items():
                if key != 'dates':
                    # 根据指标名称分类
                    if key.startswith('MA'):
                        ma_indicators[key] = value
                    elif key in ['DIF', 'DEA', 'MACD']:
                        macd_indicators[key] = value
        
        return {
            'initial_capital': self.initial_capital,
            'final_value': round(final_value, 2),
            'total_return': round(total_return, 2),
            'total_trades': total_trades,
            'win_rate': round(win_rate, 2),
            'buy_points': buy_points,
            'sell_points': sell_points,
            'equity_curve': equity_curve,
            'ma_indicators': ma_indicators,  # 均线指标
            'macd_indicators': macd_indicators,  # MACD指标
            'dates': [d.strftime('%Y-%m-%d') if isinstance(d, pd.Timestamp) else str(d) for d in df['date']],
            'prices': {
                'open': df['open'].tolist(),
                'close': df['close'].tolist(),
                'high': df['high'].tolist(),
                'low': df['low'].tolist(),
                'volume': df['volume'].tolist()
            }
        }


if __name__ == "__main__":
    # 测试
    from data_fetcher import get_stock_data
    
    df = get_stock_data("000001")
    engine = BacktestEngine()
    
    # 测试均线策略
    ma_config = {
        'type': 'ma',
        'params': {
            'short_period': {'value': 5},
            'long_period': {'value': 20}
        }
    }
    
    result = engine.run_backtest(df, [ma_config])
    print(f"总收益率: {result['total_return']}%")
    print(f"交易次数: {result['total_trades']}")
    print(f"胜率: {result['win_rate']}%")