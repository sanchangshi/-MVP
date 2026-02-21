"""
海龟交易策略模块
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class TurtleStrategy:
    """
    海龟交易策略
    突破N日最高价买入
    跌破M日最低价卖出
    经典的趋势跟踪系统
    """
    
    def __init__(self, entry_period: int = 20, exit_period: int = 10):
        """
        初始化海龟交易策略
        
        Args:
            entry_period: 入市突破周期，默认20
            exit_period: 离市突破周期，默认10
        """
        self.entry_period = entry_period
        self.exit_period = exit_period
        self.name = f"Turtle_{entry_period}_{exit_period}"
        self.display_name = f"海龟策略({entry_period}/{exit_period})"
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算海龟通道指标
        
        Args:
            df: 包含高低收盘价的DataFrame
            
        Returns:
            添加了通道列的DataFrame
        """
        df = df.copy()
        
        # 入市通道：N日最高价
        df['entry_high'] = df['high'].rolling(window=self.entry_period, min_periods=1).max()
        
        # 入市通道：N日最低价
        df['entry_low'] = df['low'].rolling(window=self.entry_period, min_periods=1).min()
        
        # 离市通道：M日最低价
        df['exit_low'] = df['low'].rolling(window=self.exit_period, min_periods=1).min()
        
        # 离市通道：M日最高价
        df['exit_high'] = df['high'].rolling(window=self.exit_period, min_periods=1).max()
        
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
        
        # 买入信号：收盘价突破N日最高价
        df.loc[(df['close'] > df['entry_high'].shift(1)), 'signal'] = 1
        
        # 卖出信号：收盘价跌破M日最低价
        df.loc[(df['close'] < df['exit_low'].shift(1)), 'signal'] = -1
        
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
                    'entry_high': float(row['entry_high']) if not pd.isna(row['entry_high']) else None
                })
            elif row['signal'] == -1:
                sell_points.append({
                    'date': row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], pd.Timestamp) else str(row['date']),
                    'price': float(row['close']),
                    'type': 'sell',
                    'exit_low': float(row['exit_low']) if not pd.isna(row['exit_low']) else None
                })
        
        return buy_points, sell_points
    
    def get_indicator_data(self, df: pd.DataFrame) -> Dict:
        """
        获取指标数据用于前端展示
        
        Returns:
            包含通道数据的字典
        """
        df = self.calculate_indicators(df)
        
        dates = [d.strftime('%Y-%m-%d') if isinstance(d, pd.Timestamp) else str(d) 
                 for d in df['date']]
        
        return {
            'dates': dates,
            'TURTLE_HIGH': df['entry_high'].fillna('').tolist(),
            'TURTLE_LOW': df['entry_low'].fillna('').tolist(),
            'EXIT_LOW': df['exit_low'].fillna('').tolist()
        }
    
    def to_dict(self) -> Dict:
        """
        转换为字典格式，用于前端展示
        """
        return {
            'name': self.name,
            'display_name': self.display_name,
            'type': 'turtle',
            'params': {
                'entry_period': {
                    'label': '入市周期',
                    'value': self.entry_period,
                    'min': 5,
                    'max': 60,
                    'default': 20
                },
                'exit_period': {
                    'label': '离市周期',
                    'value': self.exit_period,
                    'min': 5,
                    'max': 30,
                    'default': 10
                }
            }
        }