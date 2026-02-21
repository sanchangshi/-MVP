"""
OBV能量潮策略模块
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class OBVStrategy:
    """
    OBV能量潮策略
    OBV上穿其均线买入
    OBV下穿其均线卖出
    量价配合判断趋势
    """
    
    def __init__(self, obv_period: int = 20, ma_period: int = 10):
        """
        初始化OBV策略
        
        Args:
            obv_period: OBV计算周期（用于信号确认），默认20
            ma_period: OBV均线周期，默认10
        """
        self.obv_period = obv_period
        self.ma_period = ma_period
        self.name = f"OBV_{obv_period}_{ma_period}"
        self.display_name = f"OBV策略({obv_period}/{ma_period})"
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算OBV指标
        
        Args:
            df: 包含收盘价和成交量的DataFrame
            
        Returns:
            添加了OBV列的DataFrame
        """
        df = df.copy()
        
        # 计算价格变化方向
        price_change = df['close'].diff()
        
        # 计算OBV
        # 价格上涨：+成交量，价格下跌：-成交量，价格不变：0
        obv = pd.Series(0.0, index=df.index)
        
        for i in range(1, len(df)):
            if price_change.iloc[i] > 0:
                obv.iloc[i] = obv.iloc[i-1] + df['volume'].iloc[i]
            elif price_change.iloc[i] < 0:
                obv.iloc[i] = obv.iloc[i-1] - df['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        df['OBV'] = obv
        
        # 计算OBV的移动平均
        df['OBV_MA'] = df['OBV'].rolling(window=self.ma_period, min_periods=1).mean()
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成买卖信号
        
        Args:
            df: 包含收盘价和成交量的DataFrame
            
        Returns:
            添加了信号列的DataFrame
        """
        df = self.calculate_indicators(df)
        
        # 计算OBV与均线的差值
        df['obv_diff'] = df['OBV'] - df['OBV_MA']
        
        # 生成信号
        df['signal'] = 0
        
        # 买入信号：OBV上穿其均线
        df.loc[(df['obv_diff'] > 0) & (df['obv_diff'].shift(1) <= 0), 'signal'] = 1
        
        # 卖出信号：OBV下穿其均线
        df.loc[(df['obv_diff'] < 0) & (df['obv_diff'].shift(1) >= 0), 'signal'] = -1
        
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
                    'obv': float(row['OBV']) if not pd.isna(row['OBV']) else None,
                    'obv_ma': float(row['OBV_MA']) if not pd.isna(row['OBV_MA']) else None
                })
            elif row['signal'] == -1:
                sell_points.append({
                    'date': row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], pd.Timestamp) else str(row['date']),
                    'price': float(row['close']),
                    'type': 'sell',
                    'obv': float(row['OBV']) if not pd.isna(row['OBV']) else None,
                    'obv_ma': float(row['OBV_MA']) if not pd.isna(row['OBV_MA']) else None
                })
        
        return buy_points, sell_points
    
    def get_indicator_data(self, df: pd.DataFrame) -> Dict:
        """
        获取指标数据用于前端展示
        
        Returns:
            包含OBV数据的字典
        """
        df = self.calculate_indicators(df)
        
        dates = [d.strftime('%Y-%m-%d') if isinstance(d, pd.Timestamp) else str(d) 
                 for d in df['date']]
        
        return {
            'dates': dates,
            'OBV': df['OBV'].fillna('').tolist(),
            'OBV_MA': df['OBV_MA'].fillna('').tolist()
        }
    
    def to_dict(self) -> Dict:
        """
        转换为字典格式，用于前端展示
        """
        return {
            'name': self.name,
            'display_name': self.display_name,
            'type': 'obv',
            'params': {
                'obv_period': {
                    'label': 'OBV周期',
                    'value': self.obv_period,
                    'min': 10,
                    'max': 60,
                    'default': 20
                },
                'ma_period': {
                    'label': '均线周期',
                    'value': self.ma_period,
                    'min': 5,
                    'max': 30,
                    'default': 10
                }
            }
        }