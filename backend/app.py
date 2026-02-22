"""
Flask API 主应用
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import threading

from data_fetcher import get_stock_data, get_stock_list, get_stock_pools
from backtest import BacktestEngine
from strategies.ma_strategy import MAStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.bollinger_strategy import BollingerStrategy
from strategies.kdj_strategy import KDJStrategy
from strategies.turtle_strategy import TurtleStrategy
from strategies.atr_strategy import ATRStrategy
from strategies.obv_strategy import OBVStrategy

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 浏览器指纹调优次数限制
optimize_count_by_fingerprint = {}
FREE_OPTIMIZE_LIMIT = 10

# 浏览器指纹策略信号扫描次数限制（每天重置）
stock_scan_count_by_fingerprint = {}
FREE_STOCK_SCAN_LIMIT = 3
last_reset_date = None  # 记录上次重置日期

# 股票数据缓存（按股票池缓存）
stock_pool_data_cache = {}
CACHE_EXPIRE_HOURS = 4  # 缓存过期时间（小时）
MAX_CACHE_SIZE = 10  # 最大缓存条目数

# 线程锁 - 保护并发访问
optimize_lock = threading.Lock()
scan_lock = threading.Lock()
cache_lock = threading.Lock()
date_reset_lock = threading.Lock()


@app.route('/api/stock_pools', methods=['GET'])
def stock_pools():
    """
    获取股票池列表
    """
    try:
        pools = get_stock_pools()
        return jsonify({
            'success': True,
            'data': pools
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stocks', methods=['GET'])
def stocks():
    """
    获取股票列表
    """
    try:
        pool = request.args.get('pool', 'zz_a50')  # 默认中证A50
        stocks = get_stock_list(pool)
        return jsonify({
            'success': True,
            'data': stocks
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stock/data', methods=['GET'])
def stock_data():
    """
    获取股票历史数据
    """
    try:
        symbol = request.args.get('symbol', '000001')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        df = get_stock_data(symbol, start_date=start_date, end_date=end_date)
        
        # 转换为前端需要的格式
        data = {
            'dates': [d.strftime('%Y-%m-%d') if isinstance(d, pd.Timestamp) else str(d) for d in df['date']],
            'prices': {
                'open': df['open'].tolist(),
                'close': df['close'].tolist(),
                'high': df['high'].tolist(),
                'low': df['low'].tolist(),
                'volume': df['volume'].tolist()
            },
            'symbol': symbol
        }
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/strategies', methods=['GET'])
def strategies():
    """
    获取可用策略列表
    """
    try:
        ma_strategy = MAStrategy()
        macd_strategy = MACDStrategy()
        rsi_strategy = RSIStrategy()
        bollinger_strategy = BollingerStrategy()
        kdj_strategy = KDJStrategy()
        turtle_strategy = TurtleStrategy()
        atr_strategy = ATRStrategy()
        obv_strategy = OBVStrategy()
        
        strategy_list = [
            ma_strategy.to_dict(),
            macd_strategy.to_dict(),
            rsi_strategy.to_dict(),
            bollinger_strategy.to_dict(),
            kdj_strategy.to_dict(),
            turtle_strategy.to_dict(),
            atr_strategy.to_dict(),
            obv_strategy.to_dict()
        ]
        
        return jsonify({
            'success': True,
            'data': strategy_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/backtest', methods=['POST'])
def backtest():
    """
    执行回测
    """
    try:
        data = request.get_json()
        
        symbol = data.get('symbol', '000001')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        strategy_configs = data.get('strategies', [])
        initial_capital = data.get('initial_capital', 100000)
        price_mode = data.get('price_mode', 'close')  # 'close' 或 'chase'
        
        if not strategy_configs:
            return jsonify({
                'success': False,
                'error': '请至少选择一个策略'
            }), 400
        
        # 获取股票数据
        df = get_stock_data(symbol, start_date=start_date, end_date=end_date)
        
        # 执行回测
        engine = BacktestEngine(initial_capital=initial_capital, price_mode=price_mode)
        result = engine.run_backtest(df, strategy_configs)
        
        result['symbol'] = symbol
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/optimize', methods=['POST'])
def optimize():
    """
    自动调优策略参数
    使用网格搜索找到最优参数组合
    """
    try:
        data = request.get_json()
        
        # 获取浏览器指纹（从前端传递）
        fingerprint = data.get('fingerprint', 'unknown')
        
        # 检查调优次数限制（加锁）
        with optimize_lock:
            current_count = optimize_count_by_fingerprint.get(fingerprint, 0)
            if current_count >= FREE_OPTIMIZE_LIMIT:
                return jsonify({
                    'success': False,
                    'error': f'您的免费调优次数已用完（{current_count}/{FREE_OPTIMIZE_LIMIT}次），请升级VIP继续使用',
                    'limit_exceeded': True,
                    'current_count': current_count,
                    'limit': FREE_OPTIMIZE_LIMIT
                }), 403
        
        symbol = data.get('symbol', '000001')
        strategy_type = data.get('strategy_type')  # 'ma' 或 'macd'
        initial_capital = data.get('initial_capital', 100000)
        optimization_metric = data.get('optimization_metric', 'total_return')  # 优化目标：total_return 或 win_rate
        price_mode = data.get('price_mode', 'close')  # 'close' 或 'chase'
        start_date = data.get('start_date')  # 用户选择的开始日期
        end_date = data.get('end_date')  # 用户选择的结束日期
        
        # 获取股票数据（使用用户选择的日期范围）
        df = get_stock_data(symbol, start_date=start_date, end_date=end_date)
        
        # 根据策略类型进行参数优化
        if strategy_type == 'ma':
            results = optimize_ma_strategy(df, initial_capital, optimization_metric, price_mode)
        elif strategy_type == 'macd':
            results = optimize_macd_strategy(df, initial_capital, optimization_metric, price_mode)
        elif strategy_type == 'rsi':
            results = optimize_rsi_strategy(df, initial_capital, optimization_metric, price_mode)
        elif strategy_type == 'bollinger':
            results = optimize_bollinger_strategy(df, initial_capital, optimization_metric, price_mode)
        elif strategy_type == 'kdj':
            results = optimize_kdj_strategy(df, initial_capital, optimization_metric, price_mode)
        elif strategy_type == 'turtle':
            results = optimize_turtle_strategy(df, initial_capital, optimization_metric, price_mode)
        elif strategy_type == 'atr':
            results = optimize_atr_strategy(df, initial_capital, optimization_metric, price_mode)
        elif strategy_type == 'obv':
            results = optimize_obv_strategy(df, initial_capital, optimization_metric, price_mode)
        else:
            return jsonify({
                'success': False,
                'error': '不支持的策略类型'
            }), 400
        
        # 调优成功，增加该指纹的计数（加锁）
        with optimize_lock:
            optimize_count_by_fingerprint[fingerprint] = current_count + 1
            remaining_count = FREE_OPTIMIZE_LIMIT - optimize_count_by_fingerprint[fingerprint]
        
        return jsonify({
            'success': True,
            'data': {
                'strategy_type': strategy_type,
                'optimization_metric': optimization_metric,
                'best_params': results['best_params'],
                'best_result': results['best_result'],
                'all_results': results['all_results'][:20],  # 只返回前20个结果
                'remaining_count': remaining_count  # 返回剩余次数
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def optimize_ma_strategy(df, initial_capital, metric='total_return', price_mode='close'):
    """
    优化均线策略参数
    """
    best_result = None
    best_params = None
    all_results = []
    
    # 参数范围
    short_range = range(3, 31, 2)  # 3, 5, 7, ..., 29
    long_range = range(10, 121, 10)  # 10, 20, 30, ..., 120
    
    for short in short_range:
        for long in long_range:
            if short >= long:
                continue
            
            strategy_config = {
                'type': 'ma',
                'params': {
                    'short_period': {'value': short},
                    'long_period': {'value': long}
                }
            }
            
            try:
                engine = BacktestEngine(initial_capital=initial_capital, price_mode=price_mode)
                result = engine.run_backtest(df, [strategy_config])
                
                score = result.get(metric, 0)
                
                result_info = {
                    'params': {'short_period': short, 'long_period': long},
                    'total_return': result.get('total_return', 0),
                    'win_rate': result.get('win_rate', 0),
                    'total_trades': result.get('total_trades', 0),
                    'final_value': result.get('final_value', 0),
                    'score': score
                }
                all_results.append(result_info)
                
                if best_result is None or score > best_result:
                    best_result = score
                    best_params = {'short_period': short, 'long_period': long}
                    
            except Exception as e:
                continue
    
    # 按分数排序
    all_results.sort(key=lambda x: x['score'], reverse=True)
    
    return {
        'best_params': best_params,
        'best_result': all_results[0] if all_results else None,
        'all_results': all_results
    }


def optimize_macd_strategy(df, initial_capital, metric='total_return', price_mode='close'):
    """
    优化MACD策略参数
    """
    best_result = None
    best_params = None
    all_results = []
    
    # 参数范围（减少组合数量以提高速度）
    fast_range = range(8, 18, 2)  # 8, 10, 12, 14, 16
    slow_range = range(20, 35, 3)  # 20, 23, 26, 29, 32
    signal_range = range(6, 13, 2)  # 6, 8, 10, 12
    
    for fast in fast_range:
        for slow in slow_range:
            if fast >= slow:
                continue
            for signal in signal_range:
                
                strategy_config = {
                    'type': 'macd',
                    'params': {
                        'fast_period': {'value': fast},
                        'slow_period': {'value': slow},
                        'signal_period': {'value': signal}
                    }
                }
                
                try:
                    engine = BacktestEngine(initial_capital=initial_capital, price_mode=price_mode)
                    result = engine.run_backtest(df, [strategy_config])
                    
                    score = result.get(metric, 0)
                    
                    result_info = {
                        'params': {
                            'fast_period': fast,
                            'slow_period': slow,
                            'signal_period': signal
                        },
                        'total_return': result.get('total_return', 0),
                        'win_rate': result.get('win_rate', 0),
                        'total_trades': result.get('total_trades', 0),
                        'final_value': result.get('final_value', 0),
                        'score': score
                    }
                    all_results.append(result_info)
                    
                    if best_result is None or score > best_result:
                        best_result = score
                        best_params = {
                            'fast_period': fast,
                            'slow_period': slow,
                            'signal_period': signal
                        }
                        
                except Exception as e:
                    continue
    
    # 按分数排序
    all_results.sort(key=lambda x: x['score'], reverse=True)
    
    return {
        'best_params': best_params,
        'best_result': all_results[0] if all_results else None,
        'all_results': all_results
    }


def optimize_rsi_strategy(df, initial_capital, metric='total_return', price_mode='close'):
    """
    优化RSI策略参数
    """
    best_result = None
    best_params = None
    all_results = []
    
    # 参数范围
    period_range = range(7, 22, 3)  # 7, 10, 13, 16, 19
    oversold_range = range(20, 35, 5)  # 20, 25, 30
    overbought_range = range(65, 80, 5)  # 65, 70, 75
    
    for period in period_range:
        for oversold in oversold_range:
            for overbought in overbought_range:
                if oversold >= overbought:
                    continue
                
                strategy_config = {
                    'type': 'rsi',
                    'params': {
                        'period': {'value': period},
                        'oversold': {'value': oversold},
                        'overbought': {'value': overbought}
                    }
                }
                
                try:
                    engine = BacktestEngine(initial_capital=initial_capital, price_mode=price_mode)
                    result = engine.run_backtest(df, [strategy_config])
                    
                    score = result.get(metric, 0)
                    
                    result_info = {
                        'params': {
                            'period': period,
                            'oversold': oversold,
                            'overbought': overbought
                        },
                        'total_return': result.get('total_return', 0),
                        'win_rate': result.get('win_rate', 0),
                        'total_trades': result.get('total_trades', 0),
                        'final_value': result.get('final_value', 0),
                        'score': score
                    }
                    all_results.append(result_info)
                    
                    if best_result is None or score > best_result:
                        best_result = score
                        best_params = {
                            'period': period,
                            'oversold': oversold,
                            'overbought': overbought
                        }
                        
                except Exception as e:
                    continue
    
    # 按分数排序
    all_results.sort(key=lambda x: x['score'], reverse=True)
    
    return {
        'best_params': best_params,
        'best_result': all_results[0] if all_results else None,
        'all_results': all_results
    }


def optimize_bollinger_strategy(df, initial_capital, metric='total_return', price_mode='close'):
    """
    优化布林带策略参数
    """
    best_result = None
    best_params = None
    all_results = []
    
    # 参数范围
    period_range = range(10, 31, 5)  # 10, 15, 20, 25, 30
    std_dev_range = [1.5, 2.0, 2.5, 3.0]
    
    for period in period_range:
        for std_dev in std_dev_range:
            
            strategy_config = {
                'type': 'bollinger',
                'params': {
                    'period': {'value': period},
                    'std_dev': {'value': std_dev}
                }
            }
            
            try:
                engine = BacktestEngine(initial_capital=initial_capital, price_mode=price_mode)
                result = engine.run_backtest(df, [strategy_config])
                
                score = result.get(metric, 0)
                
                result_info = {
                    'params': {
                        'period': period,
                        'std_dev': std_dev
                    },
                    'total_return': result.get('total_return', 0),
                    'win_rate': result.get('win_rate', 0),
                    'total_trades': result.get('total_trades', 0),
                    'final_value': result.get('final_value', 0),
                    'score': score
                }
                all_results.append(result_info)
                
                if best_result is None or score > best_result:
                    best_result = score
                    best_params = {
                        'period': period,
                        'std_dev': std_dev
                    }
                    
            except Exception as e:
                continue
    
    # 按分数排序
    all_results.sort(key=lambda x: x['score'], reverse=True)
    
    return {
        'best_params': best_params,
        'best_result': all_results[0] if all_results else None,
        'all_results': all_results
    }


def optimize_kdj_strategy(df, initial_capital, metric='total_return', price_mode='close'):
    """
    优化KDJ策略参数
    """
    best_result = None
    best_params = None
    all_results = []
    
    # 参数范围
    n_range = [7, 9, 11, 14]
    m1_range = [2, 3, 4]
    m2_range = [2, 3, 4]
    
    for n in n_range:
        for m1 in m1_range:
            for m2 in m2_range:
                strategy_config = {
                    'type': 'kdj',
                    'params': {
                        'n_period': {'value': n},
                        'm1_period': {'value': m1},
                        'm2_period': {'value': m2}
                    }
                }
                
                try:
                    engine = BacktestEngine(initial_capital=initial_capital, price_mode=price_mode)
                    result = engine.run_backtest(df, [strategy_config])
                    
                    score = result.get(metric, 0)
                    
                    result_info = {
                        'params': {'n_period': n, 'm1_period': m1, 'm2_period': m2},
                        'total_return': result.get('total_return', 0),
                        'win_rate': result.get('win_rate', 0),
                        'total_trades': result.get('total_trades', 0),
                        'final_value': result.get('final_value', 0),
                        'score': score
                    }
                    all_results.append(result_info)
                    
                    if best_result is None or score > best_result:
                        best_result = score
                        best_params = {'n_period': n, 'm1_period': m1, 'm2_period': m2}
                        
                except Exception as e:
                    continue
    
    all_results.sort(key=lambda x: x['score'], reverse=True)
    
    return {
        'best_params': best_params,
        'best_result': all_results[0] if all_results else None,
        'all_results': all_results
    }


def optimize_turtle_strategy(df, initial_capital, metric='total_return', price_mode='close'):
    """
    优化海龟交易策略参数
    """
    best_result = None
    best_params = None
    all_results = []
    
    # 参数范围
    entry_range = [10, 15, 20, 25, 30]
    exit_range = [5, 10, 15, 20]
    
    for entry in entry_range:
        for exit_p in exit_range:
            if entry <= exit_p:
                continue
            
            strategy_config = {
                'type': 'turtle',
                'params': {
                    'entry_period': {'value': entry},
                    'exit_period': {'value': exit_p}
                }
            }
            
            try:
                engine = BacktestEngine(initial_capital=initial_capital, price_mode=price_mode)
                result = engine.run_backtest(df, [strategy_config])
                
                score = result.get(metric, 0)
                
                result_info = {
                    'params': {'entry_period': entry, 'exit_period': exit_p},
                    'total_return': result.get('total_return', 0),
                    'win_rate': result.get('win_rate', 0),
                    'total_trades': result.get('total_trades', 0),
                    'final_value': result.get('final_value', 0),
                    'score': score
                }
                all_results.append(result_info)
                
                if best_result is None or score > best_result:
                    best_result = score
                    best_params = {'entry_period': entry, 'exit_period': exit_p}
                    
            except Exception as e:
                continue
    
    all_results.sort(key=lambda x: x['score'], reverse=True)
    
    return {
        'best_params': best_params,
        'best_result': all_results[0] if all_results else None,
        'all_results': all_results
    }


def optimize_atr_strategy(df, initial_capital, metric='total_return', price_mode='close'):
    """
    优化ATR止损策略参数
    """
    best_result = None
    best_params = None
    all_results = []
    
    # 参数范围
    period_range = [10, 14, 20]
    multiplier_range = [1.5, 2.0, 2.5, 3.0]
    
    for period in period_range:
        for multiplier in multiplier_range:
            strategy_config = {
                'type': 'atr',
                'params': {
                    'period': {'value': period},
                    'multiplier': {'value': multiplier}
                }
            }
            
            try:
                engine = BacktestEngine(initial_capital=initial_capital, price_mode=price_mode)
                result = engine.run_backtest(df, [strategy_config])
                
                score = result.get(metric, 0)
                
                result_info = {
                    'params': {'period': period, 'multiplier': multiplier},
                    'total_return': result.get('total_return', 0),
                    'win_rate': result.get('win_rate', 0),
                    'total_trades': result.get('total_trades', 0),
                    'final_value': result.get('final_value', 0),
                    'score': score
                }
                all_results.append(result_info)
                
                if best_result is None or score > best_result:
                    best_result = score
                    best_params = {'period': period, 'multiplier': multiplier}
                    
            except Exception as e:
                continue
    
    all_results.sort(key=lambda x: x['score'], reverse=True)
    
    return {
        'best_params': best_params,
        'best_result': all_results[0] if all_results else None,
        'all_results': all_results
    }


def optimize_obv_strategy(df, initial_capital, metric='total_return', price_mode='close'):
    """
    优化OBV能量潮策略参数
    """
    best_result = None
    best_params = None
    all_results = []
    
    # 参数范围
    obv_period_range = [15, 20, 30]
    ma_period_range = [5, 10, 15, 20]
    
    for obv_period in obv_period_range:
        for ma_period in ma_period_range:
            strategy_config = {
                'type': 'obv',
                'params': {
                    'obv_period': {'value': obv_period},
                    'ma_period': {'value': ma_period}
                }
            }
            
            try:
                engine = BacktestEngine(initial_capital=initial_capital, price_mode=price_mode)
                result = engine.run_backtest(df, [strategy_config])
                
                score = result.get(metric, 0)
                
                result_info = {
                    'params': {'obv_period': obv_period, 'ma_period': ma_period},
                    'total_return': result.get('total_return', 0),
                    'win_rate': result.get('win_rate', 0),
                    'total_trades': result.get('total_trades', 0),
                    'final_value': result.get('final_value', 0),
                    'score': score
                }
                all_results.append(result_info)
                
                if best_result is None or score > best_result:
                    best_result = score
                    best_params = {'obv_period': obv_period, 'ma_period': ma_period}
                    
            except Exception as e:
                continue
    
    all_results.sort(key=lambda x: x['score'], reverse=True)
    
    return {
        'best_params': best_params,
        'best_result': all_results[0] if all_results else None,
        'all_results': all_results
    }


# 选股数据天数（覆盖所有策略调优需求）
SCAN_DATA_DAYS = 160


@app.route('/api/stock_scan_stream', methods=['POST'])
def stock_scan_stream():
    """
    策略信号扫描 - SSE 流式返回进度
    扫描股票池，找出当前有买入信号的股票
    自动获取最近160天数据（覆盖所有策略调优需求）
    """
    global last_reset_date, stock_scan_count_by_fingerprint
    
    from datetime import datetime, timedelta
    import json
    
    # 在请求上下文中获取这些值
    data = request.get_json()
    fingerprint = data.get('fingerprint', 'unknown')
    
    # 检查是否需要重置每日计数（加锁）
    today = datetime.now().strftime('%Y-%m-%d')
    with date_reset_lock:
        if last_reset_date != today:
            stock_scan_count_by_fingerprint = {}
            last_reset_date = today
    
    # 检查扫描次数限制（加锁）
    with scan_lock:
        current_count = stock_scan_count_by_fingerprint.get(fingerprint, 0)
    
    def generate():
        try:
            nonlocal current_count, fingerprint, data
            
            if current_count >= FREE_STOCK_SCAN_LIMIT:
                yield f"data: {json.dumps({'type': 'error', 'error': f'您今天的扫描次数已用完（{current_count}/{FREE_STOCK_SCAN_LIMIT}次），请明天再试或升级VIP', 'limit_exceeded': True}, ensure_ascii=False)}\n\n"
                return
            
            pool = data.get('pool', 'hot')
            strategies = data.get('strategies', [])
            
            # 自动计算日期范围：最近160天
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=SCAN_DATA_DAYS)).strftime('%Y%m%d')
            
            if not strategies:
                yield f"data: {json.dumps({'type': 'error', 'error': '请先添加策略到策略组合区'}, ensure_ascii=False)}\n\n"
                return
            
            # 发送开始信号
            yield f"data: {json.dumps({'type': 'start', 'message': '正在获取股票列表...'}, ensure_ascii=False)}\n\n"
            
            # 获取股票列表
            stocks = get_stock_list(pool)
            total_stocks = len(stocks)
            
            # 清理过期缓存（加锁）
            with cache_lock:
                clean_expired_cache()
            
            # 检查缓存（加锁）
            cache_key = f"{pool}_{start_date}_{end_date}"
            with cache_lock:
                if cache_key in stock_pool_data_cache:
                    cache_entry = stock_pool_data_cache[cache_key]
                    if is_cache_valid(cache_entry):
                        print(f"使用缓存数据: {cache_key}")
                        cached_data = cache_entry['data']
                    else:
                        print(f"缓存已过期: {cache_key}")
                        del stock_pool_data_cache[cache_key]
                        cached_data = None
                else:
                    cached_data = None
            
            if cached_data is None:
                yield f"data: {json.dumps({'type': 'progress', 'message': '正在批量获取股票数据...', 'current': 0, 'total': total_stocks, 'percent': 0}, ensure_ascii=False)}\n\n"
                
                print(f"批量获取股票数据: {cache_key}")
                cached_data = {}
                for i, stock in enumerate(stocks):
                    try:
                        df = get_stock_data(stock['code'], start_date=start_date, end_date=end_date)
                        cached_data[stock['code']] = {
                            'df': df,
                            'name': stock['name']
                        }
                    except Exception as e:
                        print(f"获取 {stock['code']} 数据失败: {e}")
                    
                    # 发送数据获取进度
                    percent = int((i + 1) / total_stocks * 100)
                    stock_msg = f'获取数据中: {stock["code"]} {stock["name"]}'
                    yield f"data: {json.dumps({'type': 'fetch_progress', 'message': stock_msg, 'current': i + 1, 'total': total_stocks, 'percent': percent}, ensure_ascii=False)}\n\n"
                
                # 存入缓存（加锁）
                with cache_lock:
                    # 检查缓存大小，如果超过限制则删除最旧的
                    if len(stock_pool_data_cache) >= MAX_CACHE_SIZE:
                        oldest_key = next(iter(stock_pool_data_cache))
                        del stock_pool_data_cache[oldest_key]
                        print(f"缓存已满，删除最旧条目: {oldest_key}")
                    
                    stock_pool_data_cache[cache_key] = {
                        'data': cached_data,
                        'timestamp': datetime.now()
                    }
            
            # 发送扫描开始信号
            actual_stocks = len(cached_data)
            yield f"data: {json.dumps({'type': 'scan_start', 'message': f'开始扫描 {actual_stocks} 只股票...', 'total': actual_stocks}, ensure_ascii=False)}\n\n"
            
            # 扫描每只股票的信号
            scan_results = []
            scanned_count = 0
            last_heartbeat = datetime.now()
            
            for stock_code, stock_data in cached_data.items():
                try:
                    df = stock_data['df']
                    stock_name = stock_data['name']
                    scanned_count += 1
                    
                    # 发送扫描进度
                    percent = int(scanned_count / actual_stocks * 100)
                    yield f"data: {json.dumps({'type': 'scan_progress', 'message': f'扫描中: {stock_code} {stock_name}', 'current': scanned_count, 'total': actual_stocks, 'percent': percent}, ensure_ascii=False)}\n\n"
                    
                    # 每10秒发送心跳，保持连接活跃
                    now = datetime.now()
                    if (now - last_heartbeat).total_seconds() > 10:
                        yield f"data: {json.dumps({'type': 'heartbeat'}, ensure_ascii=False)}\n\n"
                        last_heartbeat = now
                    
                    # 检查每个策略是否有买入信号
                    buy_signals = []
                    
                    for strategy_config in strategies:
                        strategy_type = strategy_config.get('type')
                        params = strategy_config.get('params', {})
                        
                        try:
                            signal = check_buy_signal(df, strategy_type, params)
                            if signal:
                                buy_signals.append({
                                    'strategy': strategy_type,
                                    'signal': signal
                                })
                        except Exception as e:
                            print(f"检查 {stock_code} {strategy_type} 信号失败: {e}")
                            continue
                    
                    # 如果有买入信号，发送实时结果
                    if buy_signals:
                        try:
                            latest_price = float(df.iloc[-1]['close'])
                            latest_date = df.iloc[-1]['date']
                            if isinstance(latest_date, pd.Timestamp):
                                latest_date = latest_date.strftime('%Y-%m-%d')
                            
                            result_item = {
                                'code': stock_code,
                                'name': stock_name,
                                'price': latest_price,
                                'date': latest_date,
                                'signals': buy_signals,
                                'signal_count': len(buy_signals)
                            }
                            scan_results.append(result_item)
                            
                            # 发现实时信号
                            yield f"data: {json.dumps({'type': 'signal_found', 'data': result_item}, ensure_ascii=False)}\n\n"
                        except Exception as e:
                            print(f"处理 {stock_code} 信号结果失败: {e}")
                except Exception as e:
                    print(f"扫描 {stock_code} 失败: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            # 按信号数量排序
            scan_results.sort(key=lambda x: x['signal_count'], reverse=True)
            
            # 增加计数（加锁）
            with scan_lock:
                stock_scan_count_by_fingerprint[fingerprint] = current_count + 1
                remaining_count = FREE_STOCK_SCAN_LIMIT - stock_scan_count_by_fingerprint[fingerprint]
            
            # 发送完成信号
            yield f"data: {json.dumps({'type': 'complete', 'data': {'results': scan_results, 'total_stocks': actual_stocks, 'signal_stocks': len(scan_results), 'remaining_count': remaining_count}}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"
    
    return app.response_class(generate(), mimetype='text/event-stream')


@app.route('/api/stock_scan', methods=['POST'])
def stock_scan():
    """
    策略信号扫描
    扫描股票池，找出当前有买入信号的股票
    自动获取最近160天数据（覆盖所有策略调优需求）
    """
    global last_reset_date, stock_scan_count_by_ip
    
    try:
        from datetime import datetime, timedelta
        
        # 检查是否需要重置每日计数
        today = datetime.now().strftime('%Y-%m-%d')
        if last_reset_date != today:
            stock_scan_count_by_ip = {}
            last_reset_date = today
        
        # 获取用户 IP 地址
        user_ip = request.remote_addr
        
        # 检查扫描次数限制
        current_count = stock_scan_count_by_ip.get(user_ip, 0)
        if current_count >= FREE_STOCK_SCAN_LIMIT:
            return jsonify({
                'success': False,
                'error': f'您今天的扫描次数已用完（{current_count}/{FREE_STOCK_SCAN_LIMIT}次），请明天再试或升级VIP',
                'limit_exceeded': True,
                'current_count': current_count,
                'limit': FREE_STOCK_SCAN_LIMIT
            }), 403
        
        data = request.get_json()
        
        pool = data.get('pool', 'hot')  # 股票池
        strategies = data.get('strategies', [])  # 策略配置列表
        
        # 自动计算日期范围：最近160天
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=SCAN_DATA_DAYS)).strftime('%Y%m%d')
        
        if not strategies:
            return jsonify({
                'success': False,
                'error': '请先添加策略到策略组合区'
            }), 400
        
        # 获取股票列表
        stocks = get_stock_list(pool)
        
        # 清理过期缓存
        clean_expired_cache()
        
        # 检查缓存
        cache_key = f"{pool}_{start_date}_{end_date}"
        if cache_key in stock_pool_data_cache:
            cache_entry = stock_pool_data_cache[cache_key]
            # 检查缓存是否过期
            if is_cache_valid(cache_entry):
                print(f"使用缓存数据: {cache_key}")
                cached_data = cache_entry['data']
            else:
                print(f"缓存已过期: {cache_key}")
                del stock_pool_data_cache[cache_key]
                cached_data = None
        else:
            cached_data = None
        
        if cached_data is None:
            print(f"批量获取股票数据: {cache_key}")
            cached_data = {}
            for stock in stocks:
                try:
                    df = get_stock_data(stock['code'], start_date=start_date, end_date=end_date)
                    cached_data[stock['code']] = {
                        'df': df,
                        'name': stock['name']
                    }
                except Exception as e:
                    print(f"获取 {stock['code']} 数据失败: {e}")
                    continue
            
            # 检查缓存大小，如果超过限制则删除最旧的
            if len(stock_pool_data_cache) >= MAX_CACHE_SIZE:
                oldest_key = next(iter(stock_pool_data_cache))
                del stock_pool_data_cache[oldest_key]
                print(f"缓存已满，删除最旧条目: {oldest_key}")
            
            # 存入缓存（带时间戳）
            stock_pool_data_cache[cache_key] = {
                'data': cached_data,
                'timestamp': datetime.now()
            }
        
        # 扫描每只股票的信号
        scan_results = []
        
        for stock_code, stock_data in cached_data.items():
            df = stock_data['df']
            stock_name = stock_data['name']
            
            # 检查每个策略是否有买入信号
            buy_signals = []
            
            for strategy_config in strategies:
                strategy_type = strategy_config.get('type')
                params = strategy_config.get('params', {})
                
                try:
                    signal = check_buy_signal(df, strategy_type, params)
                    if signal:
                        buy_signals.append({
                            'strategy': strategy_type,
                            'signal': signal
                        })
                except Exception as e:
                    print(f"检查 {stock_code} {strategy_type} 信号失败: {e}")
                    continue
            
            # 如果有买入信号，添加到结果
            if buy_signals:
                latest_price = float(df.iloc[-1]['close'])
                latest_date = df.iloc[-1]['date']
                if isinstance(latest_date, pd.Timestamp):
                    latest_date = latest_date.strftime('%Y-%m-%d')
                
                scan_results.append({
                    'code': stock_code,
                    'name': stock_name,
                    'price': latest_price,
                    'date': latest_date,
                    'signals': buy_signals,
                    'signal_count': len(buy_signals)
                })
        
        # 按信号数量排序
        scan_results.sort(key=lambda x: x['signal_count'], reverse=True)
        
        # 增加计数
        stock_scan_count_by_ip[user_ip] = current_count + 1
        remaining_count = FREE_STOCK_SCAN_LIMIT - stock_scan_count_by_ip[user_ip]
        
        return jsonify({
            'success': True,
            'data': {
                'results': scan_results,
                'total_stocks': len(cached_data),
                'signal_stocks': len(scan_results),
                'remaining_count': remaining_count
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def clean_expired_cache():
    """
    清理过期的缓存
    """
    from datetime import datetime, timedelta
    
    global stock_pool_data_cache
    
    expired_keys = []
    for key, entry in stock_pool_data_cache.items():
        if not isinstance(entry, dict) or 'timestamp' not in entry:
            # 旧格式缓存，直接删除
            expired_keys.append(key)
            continue
        
        timestamp = entry.get('timestamp')
        if timestamp and (datetime.now() - timestamp) > timedelta(hours=CACHE_EXPIRE_HOURS):
            expired_keys.append(key)
    
    for key in expired_keys:
        del stock_pool_data_cache[key]
        print(f"清理过期缓存: {key}")


def is_cache_valid(cache_entry):
    """
    检查缓存是否有效
    """
    from datetime import datetime, timedelta
    
    if not isinstance(cache_entry, dict) or 'timestamp' not in cache_entry:
        return False
    
    timestamp = cache_entry.get('timestamp')
    if not timestamp:
        return False
    
    return (datetime.now() - timestamp) <= timedelta(hours=CACHE_EXPIRE_HOURS)


def check_buy_signal(df, strategy_type, params):
    """
    检查是否有买入信号
    返回: None 或 信号描述
    """
    # 数据检查
    if df is None or len(df) < 30:
        return None
    
    # 检查必要列是否存在
    required_cols = ['open', 'close', 'high', 'low', 'volume']
    for col in required_cols:
        if col not in df.columns:
            return None
    
    # 检查是否有 NaN 值
    if df[required_cols].isnull().any().any():
        return None
    
    # 获取参数值
    def get_param(key, default):
        if isinstance(params, dict):
            p = params.get(key, {})
            if isinstance(p, dict):
                return p.get('value', default)
            return p if p is not None else default
        return default
    
    try:
        if strategy_type == 'ma':
            short = get_param('short_period', 5)
            long = get_param('long_period', 20)
            strategy = MAStrategy(short_period=short, long_period=long)
            df_signals = strategy.generate_signals(df)
            last_signal = df_signals.iloc[-1]['signal']
            if last_signal == 1:
                return f"MA金叉({short}/{long})"
            # 检查前一天是否有信号
            if len(df_signals) > 1 and df_signals.iloc[-2]['signal'] == 1:
                return f"MA金叉({short}/{long})"
                
        elif strategy_type == 'macd':
            fast = get_param('fast_period', 12)
            slow = get_param('slow_period', 26)
            signal_period = get_param('signal_period', 9)
            strategy = MACDStrategy(fast_period=fast, slow_period=slow, signal_period=signal_period)
            df_signals = strategy.generate_signals(df)
            last_signal = df_signals.iloc[-1]['signal']
            if last_signal == 1:
                return f"MACD金叉"
            if len(df_signals) > 1 and df_signals.iloc[-2]['signal'] == 1:
                return f"MACD金叉"
                
        elif strategy_type == 'rsi':
            period = get_param('period', 14)
            oversold = get_param('oversold', 30)
            overbought = get_param('overbought', 70)
            strategy = RSIStrategy(period=period, oversold=oversold, overbought=overbought)
            df_signals = strategy.generate_signals(df)
            last_signal = df_signals.iloc[-1]['signal']
            if last_signal == 1:
                return f"RSI超卖回升"
            if len(df_signals) > 1 and df_signals.iloc[-2]['signal'] == 1:
                return f"RSI超卖回升"
                
        elif strategy_type == 'bollinger':
            period = get_param('period', 20)
            std_dev = get_param('std_dev', 2.0)
            strategy = BollingerStrategy(period=period, std_dev=std_dev)
            df_signals = strategy.generate_signals(df)
            last_signal = df_signals.iloc[-1]['signal']
            if last_signal == 1:
                return f"布林带下轨反弹"
            if len(df_signals) > 1 and df_signals.iloc[-2]['signal'] == 1:
                return f"布林带下轨反弹"
                
        elif strategy_type == 'kdj':
            n = get_param('n_period', 9)
            m1 = get_param('m1_period', 3)
            m2 = get_param('m2_period', 3)
            strategy = KDJStrategy(n_period=n, m1_period=m1, m2_period=m2)
            df_signals = strategy.generate_signals(df)
            last_signal = df_signals.iloc[-1]['signal']
            if last_signal == 1:
                return f"KDJ金叉"
            if len(df_signals) > 1 and df_signals.iloc[-2]['signal'] == 1:
                return f"KDJ金叉"
                
        elif strategy_type == 'turtle':
            entry = get_param('entry_period', 20)
            exit_p = get_param('exit_period', 10)
            strategy = TurtleStrategy(entry_period=entry, exit_period=exit_p)
            df_signals = strategy.generate_signals(df)
            last_signal = df_signals.iloc[-1]['signal']
            if last_signal == 1:
                return f"突破{entry}日高点"
            if len(df_signals) > 1 and df_signals.iloc[-2]['signal'] == 1:
                return f"突破{entry}日高点"
                
        elif strategy_type == 'atr':
            period = get_param('period', 14)
            multiplier = get_param('multiplier', 2.0)
            strategy = ATRStrategy(period=period, multiplier=multiplier)
            df_signals = strategy.generate_signals(df)
            last_signal = df_signals.iloc[-1]['signal']
            if last_signal == 1:
                return f"ATR突破买入"
            if len(df_signals) > 1 and df_signals.iloc[-2]['signal'] == 1:
                return f"ATR突破买入"
                
        elif strategy_type == 'obv':
            obv_period = get_param('obv_period', 20)
            ma_period = get_param('ma_period', 10)
            strategy = OBVStrategy(obv_period=obv_period, ma_period=ma_period)
            df_signals = strategy.generate_signals(df)
            last_signal = df_signals.iloc[-1]['signal']
            if last_signal == 1:
                return f"OBV金叉"
            if len(df_signals) > 1 and df_signals.iloc[-2]['signal'] == 1:
                return f"OBV金叉"
        
        return None
        
    except Exception as e:
        print(f"检查信号失败: {e}")
        return None


@app.route('/', methods=['GET'])
def index():
    """
    健康检查
    """
    return jsonify({
        'status': 'ok',
        'message': '股票回测系统API运行中'
    })


import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    print(f"启动股票回测系统API服务...")
    print(f"API地址: http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
