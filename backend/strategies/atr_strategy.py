"""
ATR止损策略模块
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class ATRStrategy:
    """
    ATR止损策略
    使用ATR倍数作为跟踪止损
    价格上涨时跟踪最高价，跌破止损线卖出
    """
    
    def __init__(self, period: int = 14, multiplier: float = 2.0):
        """
        初始化ATR止损策略
        
        Args:
            period: ATR计算周期，默认14
            multiplier: ATR止损倍数，默认2.0
        """
        self.period = period
        self.multiplier = multiplier
        self.name = f"ATR_{period}_{multiplier}"
        self.display_name = f"ATR止损({period},{multiplier})"
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算ATR指标和止损线
        
        Args:
            df: 包含高低收盘价的DataFrame
            
        Returns:
            添加了ATR和止损线列的DataFrame
        """
        df = df.copy()
        
        # 计算真实波幅 TR (True Range)
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift(1))
        low_close = abs(df['low'] - df['close'].shift(1))
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # 计算ATR (Average True Range)
        df['ATR'] = tr.rolling(window=self.period, min_periods=1).mean()
        
        # 计算止损线
        # 跟踪止损：记录持仓期间的最高价，止损线 = 最高价 - ATR * 倍数
        df['highest_since_entry'] = df['high'].expanding().max()  # 简化处理
        df['stop_loss'] = df['highest_since_entry'] - df['ATR'] * self.multiplier
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成买卖信号
        
        Args:
            df: 包含高低收盘价的DataFrame
            
        Returns:
            添加了信号列的DataFrame
        """
        df = self.calculate_indicators(df)
        
        # 生成信号
        df['signal'] = 0
        
        # 简化策略：
        # 买入信号：收盘价上穿ATR止损线（趋势启动）
        # 卖出信号：收盘价跌破ATR止损线（止损离场）
        
        # 计算动态止损线（使用前一日数据避免未来函数）
        df['dynamic_stop'] = df['high'].shift(1).rolling(window=self.period, min_periods=1).max() - df['ATR'].shift(1) * self.multiplier
        
        # 买入：价格突破前N日高点
        df['prev_high'] = df['high'].shift(1).rolling(window=self.period, min_periods=1).max()
        df.loc[(df['close'] > df['prev_high']), 'signal'] = 1
        
        # 卖出：价格跌破止损线
        df.loc[(df['close'] < df['dynamic_stop']) & (df['close'].shift(1) >= df['dynamic_stop'].shift(1)), 'signal'] = -1
        
        return df
    
    def get_buy_sell_points(self, df: pd.DataFrame) -> Tuple[List[Dict], List[Dict]]:
        """
        获取买卖点
        
        Returns:
            (买入点列表, 卖出点列表)
        """
        df = self.generate_signals(df)
        
        buy_points = []
        sell_points = []
        
        for idx, row in df.iterrows():
            if row['signal'] == 1:
                buy_points.append({
                    'date': row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], pd.Timestamp) else str(row['date']),
                    'price': float(row['close']),
                    'type': 'buy',
                    'atr': float(row['ATR']) if not pd.isna(row['ATR']) else None
                })
            elif row['signal'] == -1:
                sell_points.append({
                    'date': row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], pd.Timestamp) else str(row['date']),
                    'price': float(row['close']),
                    'type': 'sell',
                    'stop_loss': float(row['dynamic_stop']) if not pd.isna(row['dynamic_stop']) else None
                })
        
        return buy_points, sell_points
    
    def get_indicator_data(self, df: pd.DataFrame) -> Dict:
        """
        获取指标数据用于前端展示
        
        Returns:
            包含ATR数据的字典
        """
        df = self.calculate_indicators(df)
        
        dates = [d.strftime('%Y-%m-%d') if isinstance(d, pd.Timestamp) else str(d) 
                 for d in df['date']]
        
        return {
            'dates': dates,
            'ATR': df['ATR'].fillna('').tolist(),
            'STOP_LOSS': df['stop_loss'].fillna('').tolist()
        }
    
    def to_dict(self) -> Dict:
        """
        转换为字典格式，用于前端展示
        """
        return {
            'name': self.name,
            'display_name': self.display_name,
            'type': 'atr',
            'params': {
                'period': {
                    'label': 'ATR周期',
                    'value': self.period,
                    'min': 5,
                    'max': 30,
                    'default': 14
                },
                'multiplier': {
                    'label': '止损倍数',
                    'value': self.multiplier,
                    'min': 1.0,
                    'max': 5.0,
                    'default': 2.0
                }
            }
        }