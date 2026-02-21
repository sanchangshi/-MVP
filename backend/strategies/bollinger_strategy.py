"""
布林带策略模块
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class BollingerStrategy:
    """
    布林带策略
    价格跌破下轨买入
    价格突破上轨卖出
    """
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        """
        初始化布林带策略
        
        Args:
            period: 移动平均周期，默认20
            std_dev: 标准差倍数，默认2
        """
        self.period = period
        self.std_dev = std_dev
        self.name = f"BOLL_{period}_{std_dev}"
        self.display_name = f"布林带策略({period},{std_dev})"
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算布林带指标
        
        Args:
            df: 包含收盘价的DataFrame
            
        Returns:
            添加了布林带列的DataFrame
        """
        df = df.copy()
        
        # 计算中轨（移动平均）
        df['BOLL_MID'] = df['close'].rolling(window=self.period).mean()
        
        # 计算标准差
        df['BOLL_STD'] = df['close'].rolling(window=self.period).std()
        
        # 计算上轨和下轨
        df['BOLL_UPPER'] = df['BOLL_MID'] + self.std_dev * df['BOLL_STD']
        df['BOLL_LOWER'] = df['BOLL_MID'] - self.std_dev * df['BOLL_STD']
        
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
        
        # 生成信号
        df['signal'] = 0
        # 价格跌破下轨后回升买入
        df.loc[(df['close'] > df['BOLL_LOWER']) & (df['close'].shift(1) <= df['BOLL_LOWER'].shift(1)), 'signal'] = 1
        # 价格突破上轨后回落卖出
        df.loc[(df['close'] < df['BOLL_UPPER']) & (df['close'].shift(1) >= df['BOLL_UPPER'].shift(1)), 'signal'] = -1
        
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
                    'boll_lower': float(row['BOLL_LOWER']) if not pd.isna(row['BOLL_LOWER']) else None,
                    'boll_mid': float(row['BOLL_MID']) if not pd.isna(row['BOLL_MID']) else None
                })
            elif row['signal'] == -1:
                sell_points.append({
                    'date': row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], pd.Timestamp) else str(row['date']),
                    'price': float(row['close']),
                    'type': 'sell',
                    'boll_upper': float(row['BOLL_UPPER']) if not pd.isna(row['BOLL_UPPER']) else None,
                    'boll_mid': float(row['BOLL_MID']) if not pd.isna(row['BOLL_MID']) else None
                })
        
        return buy_points, sell_points
    
    def get_indicator_data(self, df: pd.DataFrame) -> Dict:
        """
        获取指标数据用于前端展示
        
        Returns:
            包含布林带数据的字典
        """
        df = self.calculate_indicators(df)
        
        dates = [d.strftime('%Y-%m-%d') if isinstance(d, pd.Timestamp) else str(d) 
                 for d in df['date']]
        
        return {
            'dates': dates,
            'BOLL_UPPER': df['BOLL_UPPER'].fillna('').tolist(),
            'BOLL_MID': df['BOLL_MID'].fillna('').tolist(),
            'BOLL_LOWER': df['BOLL_LOWER'].fillna('').tolist()
        }
    
    def to_dict(self) -> Dict:
        """
        转换为字典格式，用于前端展示
        """
        return {
            'name': self.name,
            'display_name': self.display_name,
            'type': 'bollinger',
            'params': {
                'period': {
                    'label': '计算周期',
                    'value': self.period,
                    'min': 5,
                    'max': 60,
                    'default': 20
                },
                'std_dev': {
                    'label': '标准差倍数',
                    'value': self.std_dev,
                    'min': 1.0,
                    'max': 3.0,
                    'default': 2.0
                }
            }
        }