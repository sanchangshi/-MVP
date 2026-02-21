"""
均线策略模块
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class MAStrategy:
    """
    均线策略
    金叉买入：短期均线上穿长期均线
    死叉卖出：短期均线下穿长期均线
    """
    
    def __init__(self, short_period: int = 5, long_period: int = 20):
        """
        初始化均线策略
        
        Args:
            short_period: 短期均线周期，默认5
            long_period: 长期均线周期，默认20
        """
        self.short_period = short_period
        self.long_period = long_period
        self.name = f"MA_{short_period}_{long_period}"
        self.display_name = f"均线策略(MA{short_period}/MA{long_period})"
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算均线指标
        
        Args:
            df: 包含收盘价的DataFrame
            
        Returns:
            添加了均线列的DataFrame
        """
        df = df.copy()
        df[f'MA{self.short_period}'] = df['close'].rolling(window=self.short_period).mean()
        df[f'MA{self.long_period}'] = df['close'].rolling(window=self.long_period).mean()
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
        
        # 计算均线差值
        df['ma_diff'] = df[f'MA{self.short_period}'] - df[f'MA{self.long_period}']
        
        # 生成信号
        df['signal'] = 0
        # 金叉：短期均线上穿长期均线
        df.loc[(df['ma_diff'] > 0) & (df['ma_diff'].shift(1) <= 0), 'signal'] = 1
        # 死叉：短期均线下穿长期均线
        df.loc[(df['ma_diff'] < 0) & (df['ma_diff'].shift(1) >= 0), 'signal'] = -1
        
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
                    'type': 'buy'
                })
            elif row['signal'] == -1:
                sell_points.append({
                    'date': row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], pd.Timestamp) else str(row['date']),
                    'price': float(row['close']),
                    'type': 'sell'
                })
        
        return buy_points, sell_points
    
    def get_indicator_data(self, df: pd.DataFrame) -> Dict:
        """
        获取指标数据用于前端展示
        
        Returns:
            包含均线数据的字典
        """
        df = self.calculate_indicators(df)
        
        dates = [d.strftime('%Y-%m-%d') if isinstance(d, pd.Timestamp) else str(d) 
                 for d in df['date']]
        
        return {
            'dates': dates,
            f'MA{self.short_period}': df[f'MA{self.short_period}'].fillna('').tolist(),
            f'MA{self.long_period}': df[f'MA{self.long_period}'].fillna('').tolist()
        }
    
    def to_dict(self) -> Dict:
        """
        转换为字典格式，用于前端展示
        """
        return {
            'name': self.name,
            'display_name': self.display_name,
            'type': 'ma',
            'params': {
                'short_period': {
                    'label': '短期均线周期',
                    'value': self.short_period,
                    'min': 2,
                    'max': 60,
                    'default': 5
                },
                'long_period': {
                    'label': '长期均线周期',
                    'value': self.long_period,
                    'min': 5,
                    'max': 120,
                    'default': 20
                }
            }
        }


if __name__ == "__main__":
    # 测试
    import sys
    sys.path.append('..')
    from data_fetcher import get_stock_data
    
    df = get_stock_data("000001")
    strategy = MAStrategy(5, 20)
    buy_points, sell_points = strategy.get_buy_sell_points(df)
    
    print(f"买入点数量: {len(buy_points)}")
    print(f"卖出点数量: {len(sell_points)}")
    if buy_points:
        print(f"第一个买入点: {buy_points[0]}")
    if sell_points:
        print(f"第一个卖出点: {sell_points[0]}")