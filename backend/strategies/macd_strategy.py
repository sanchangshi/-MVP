"""
MACD策略模块
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class MACDStrategy:
    """
    MACD策略
    金叉买入：DIF上穿DEA
    死叉卖出：DIF下穿DEA
    """
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        """
        初始化MACD策略
        
        Args:
            fast_period: 快线周期，默认12
            slow_period: 慢线周期，默认26
            signal_period: 信号线周期，默认9
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.name = f"MACD_{fast_period}_{slow_period}_{signal_period}"
        self.display_name = f"MACD策略({fast_period},{slow_period},{signal_period})"
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算MACD指标
        
        Args:
            df: 包含收盘价的DataFrame
            
        Returns:
            添加了MACD列的DataFrame
        """
        df = df.copy()
        
        # 计算EMA
        ema_fast = df['close'].ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = df['close'].ewm(span=self.slow_period, adjust=False).mean()
        
        # 计算DIF
        df['DIF'] = ema_fast - ema_slow
        
        # 计算DEA（信号线）
        df['DEA'] = df['DIF'].ewm(span=self.signal_period, adjust=False).mean()
        
        # 计算MACD柱
        df['MACD'] = (df['DIF'] - df['DEA']) * 2
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成买卖信号
        
        Args:
            df: 包含收盘价的DataFrame
            
        Returns:
            添加了信号列的DataFrame
        """
        df = self.calculate_indicators(df)
        
        # 计算DIF-DEA差值
        df['macd_diff'] = df['DIF'] - df['DEA']
        
        # 生成信号
        df['signal'] = 0
        # 金叉：DIF上穿DEA
        df.loc[(df['macd_diff'] > 0) & (df['macd_diff'].shift(1) <= 0), 'signal'] = 1
        # 死叉：DIF下穿DEA
        df.loc[(df['macd_diff'] < 0) & (df['macd_diff'].shift(1) >= 0), 'signal'] = -1
        
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
                    'dif': float(row['DIF']) if not pd.isna(row['DIF']) else None,
                    'dea': float(row['DEA']) if not pd.isna(row['DEA']) else None
                })
            elif row['signal'] == -1:
                sell_points.append({
                    'date': row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], pd.Timestamp) else str(row['date']),
                    'price': float(row['close']),
                    'type': 'sell',
                    'dif': float(row['DIF']) if not pd.isna(row['DIF']) else None,
                    'dea': float(row['DEA']) if not pd.isna(row['DEA']) else None
                })
        
        return buy_points, sell_points
    
    def get_indicator_data(self, df: pd.DataFrame) -> Dict:
        """
        获取指标数据用于前端展示
        
        Returns:
            包含MACD数据的字典
        """
        df = self.calculate_indicators(df)
        
        dates = [d.strftime('%Y-%m-%d') if isinstance(d, pd.Timestamp) else str(d) 
                 for d in df['date']]
        
        return {
            'dates': dates,
            'DIF': df['DIF'].fillna('').tolist(),
            'DEA': df['DEA'].fillna('').tolist(),
            'MACD': df['MACD'].fillna('').tolist()
        }
    
    def to_dict(self) -> Dict:
        """
        转换为字典格式，用于前端展示
        """
        return {
            'name': self.name,
            'display_name': self.display_name,
            'type': 'macd',
            'params': {
                'fast_period': {
                    'label': '快线周期',
                    'value': self.fast_period,
                    'min': 5,
                    'max': 30,
                    'default': 12
                },
                'slow_period': {
                    'label': '慢线周期',
                    'value': self.slow_period,
                    'min': 10,
                    'max': 60,
                    'default': 26
                },
                'signal_period': {
                    'label': '信号线周期',
                    'value': self.signal_period,
                    'min': 5,
                    'max': 20,
                    'default': 9
                }
            }
        }


if __name__ == "__main__":
    # 测试
    import sys
    sys.path.append('..')
    from data_fetcher import get_stock_data
    
    df = get_stock_data("000001")
    strategy = MACDStrategy()
    buy_points, sell_points = strategy.get_buy_sell_points(df)
    
    print(f"买入点数量: {len(buy_points)}")
    print(f"卖出点数量: {len(sell_points)}")
    if buy_points:
        print(f"第一个买入点: {buy_points[0]}")
    if sell_points:
        print(f"第一个卖出点: {sell_points[0]}")