"""
KDJ随机指标策略模块
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class KDJStrategy:
    """
    KDJ随机指标策略
    K线上穿D线买入（金叉）
    K线下穿D线卖出（死叉）
    """
    
    def __init__(self, n_period: int = 9, m1_period: int = 3, m2_period: int = 3):
        """
        初始化KDJ策略
        
        Args:
            n_period: RSV计算周期，默认9
            m1_period: K值平滑周期，默认3
            m2_period: D值平滑周期，默认3
        """
        self.n_period = n_period
        self.m1_period = m1_period
        self.m2_period = m2_period
        self.name = f"KDJ_{n_period}_{m1_period}_{m2_period}"
        self.display_name = f"KDJ策略({n_period},{m1_period},{m2_period})"
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算KDJ指标
        
        Args:
            df: 包含高低收盘价的DataFrame
            
        Returns:
            添加了KDJ列的DataFrame
        """
        df = df.copy()
        
        # 计算RSV (Raw Stochastic Value)
        low_n = df['low'].rolling(window=self.n_period, min_periods=1).min()
        high_n = df['high'].rolling(window=self.n_period, min_periods=1).max()
        
        rsv = (df['close'] - low_n) / (high_n - low_n) * 100
        rsv = rsv.fillna(50)  # 处理除零情况
        
        # 计算K值（RSV的M1周期移动平均）
        df['K'] = rsv.ewm(span=self.m1_period, adjust=False).mean()
        
        # 计算D值（K值的M2周期移动平均）
        df['D'] = df['K'].ewm(span=self.m2_period, adjust=False).mean()
        
        # 计算J值
        df['J'] = 3 * df['K'] - 2 * df['D']
        
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
        
        # 计算K-D差值
        df['kd_diff'] = df['K'] - df['D']
        
        # 生成信号
        df['signal'] = 0
        # K线上穿D线（金叉）买入
        df.loc[(df['kd_diff'] > 0) & (df['kd_diff'].shift(1) <= 0), 'signal'] = 1
        # K线下穿D线（死叉）卖出
        df.loc[(df['kd_diff'] < 0) & (df['kd_diff'].shift(1) >= 0), 'signal'] = -1
        
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
                    'k': float(row['K']) if not pd.isna(row['K']) else None,
                    'd': float(row['D']) if not pd.isna(row['D']) else None
                })
            elif row['signal'] == -1:
                sell_points.append({
                    'date': row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], pd.Timestamp) else str(row['date']),
                    'price': float(row['close']),
                    'type': 'sell',
                    'k': float(row['K']) if not pd.isna(row['K']) else None,
                    'd': float(row['D']) if not pd.isna(row['D']) else None
                })
        
        return buy_points, sell_points
    
    def get_indicator_data(self, df: pd.DataFrame) -> Dict:
        """
        获取指标数据用于前端展示
        
        Returns:
            包含KDJ数据的字典
        """
        df = self.calculate_indicators(df)
        
        dates = [d.strftime('%Y-%m-%d') if isinstance(d, pd.Timestamp) else str(d) 
                 for d in df['date']]
        
        return {
            'dates': dates,
            'K': df['K'].fillna('').tolist(),
            'D': df['D'].fillna('').tolist(),
            'J': df['J'].fillna('').tolist()
        }
    
    def to_dict(self) -> Dict:
        """
        转换为字典格式，用于前端展示
        """
        return {
            'name': self.name,
            'display_name': self.display_name,
            'type': 'kdj',
            'params': {
                'n_period': {
                    'label': 'RSV周期',
                    'value': self.n_period,
                    'min': 5,
                    'max': 30,
                    'default': 9
                },
                'm1_period': {
                    'label': 'K值平滑',
                    'value': self.m1_period,
                    'min': 2,
                    'max': 10,
                    'default': 3
                },
                'm2_period': {
                    'label': 'D值平滑',
                    'value': self.m2_period,
                    'min': 2,
                    'max': 10,
                    'default': 3
                }
            }
        }