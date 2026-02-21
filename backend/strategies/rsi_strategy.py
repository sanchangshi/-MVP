"""
RSI策略模块
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class RSIStrategy:
    """
    RSI相对强弱指标策略
    RSI < 30 超卖区买入
    RSI > 70 超买区卖出
    """
    
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        """
        初始化RSI策略
        
        Args:
            period: RSI计算周期，默认14
            oversold: 超卖阈值，默认30
            overbought: 超买阈值，默认70
        """
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.name = f"RSI_{period}"
        self.display_name = f"RSI策略({period})"
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算RSI指标
        
        Args:
            df: 包含收盘价的DataFrame
            
        Returns:
            添加了RSI列的DataFrame
        """
        df = df.copy()
        
        # 计算价格变化
        delta = df['close'].diff()
        
        # 分离上涨和下跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 计算平均上涨和下跌
        avg_gain = gain.rolling(window=self.period, min_periods=1).mean()
        avg_loss = loss.rolling(window=self.period, min_periods=1).mean()
        
        # 计算RS和RSI
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
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
        # RSI从超卖区回升买入
        df.loc[(df['RSI'] < self.oversold) & (df['RSI'].shift(1) >= self.oversold), 'signal'] = 1
        # RSI进入超买区卖出
        df.loc[(df['RSI'] > self.overbought) & (df['RSI'].shift(1) <= self.overbought), 'signal'] = -1
        
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
                    'rsi': float(row['RSI']) if not pd.isna(row['RSI']) else None
                })
            elif row['signal'] == -1:
                sell_points.append({
                    'date': row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], pd.Timestamp) else str(row['date']),
                    'price': float(row['close']),
                    'type': 'sell',
                    'rsi': float(row['RSI']) if not pd.isna(row['RSI']) else None
                })
        
        return buy_points, sell_points
    
    def get_indicator_data(self, df: pd.DataFrame) -> Dict:
        """
        获取指标数据用于前端展示
        
        Returns:
            包含RSI数据的字典
        """
        df = self.calculate_indicators(df)
        
        dates = [d.strftime('%Y-%m-%d') if isinstance(d, pd.Timestamp) else str(d) 
                 for d in df['date']]
        
        return {
            'dates': dates,
            'RSI': df['RSI'].fillna('').tolist()
        }
    
    def to_dict(self) -> Dict:
        """
        转换为字典格式，用于前端展示
        """
        return {
            'name': self.name,
            'display_name': self.display_name,
            'type': 'rsi',
            'params': {
                'period': {
                    'label': 'RSI周期',
                    'value': self.period,
                    'min': 5,
                    'max': 30,
                    'default': 14
                },
                'oversold': {
                    'label': '超卖阈值',
                    'value': self.oversold,
                    'min': 10,
                    'max': 40,
                    'default': 30
                },
                'overbought': {
                    'label': '超买阈值',
                    'value': self.overbought,
                    'min': 60,
                    'max': 90,
                    'default': 70
                }
            }
        }