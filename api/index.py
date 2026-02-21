# Vercel Serverless Function 入口
import sys
import os

# 添加项目根目录到路径
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

from flask import Flask, request, jsonify
from flask_cors import CORS

# 导入后端模块
from backend.data_fetcher import get_stock_data, get_stock_list, get_stock_pools
from backend.backtest import BacktestEngine
from backend.strategies.ma_strategy import MAStrategy
from backend.strategies.macd_strategy import MACDStrategy
from backend.strategies.rsi_strategy import RSIStrategy
from backend.strategies.bollinger_strategy import BollingerStrategy
from backend.strategies.kdj_strategy import KDJStrategy
from backend.strategies.turtle_strategy import TurtleStrategy
from backend.strategies.atr_strategy import ATRStrategy
from backend.strategies.obv_strategy import OBVStrategy

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': '股票回测系统API运行中'
    })

@app.route('/api/stock_pools', methods=['GET'])
def stock_pools():
    try:
        pools = get_stock_pools()
        return jsonify({'success': True, 'data': pools})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stocks', methods=['GET'])
def stocks():
    try:
        pool = request.args.get('pool', 'hot')
        stocks = get_stock_list(pool)
        return jsonify({'success': True, 'data': stocks})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/strategies', methods=['GET'])
def strategies():
    try:
        strategy_list = [
            MAStrategy().to_dict(),
            MACDStrategy().to_dict(),
            RSIStrategy().to_dict(),
            BollingerStrategy().to_dict(),
            KDJStrategy().to_dict(),
            TurtleStrategy().to_dict(),
            ATRStrategy().to_dict(),
            OBVStrategy().to_dict()
        ]
        return jsonify({'success': True, 'data': strategy_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stock/data', methods=['GET'])
def stock_data():
    try:
        symbol = request.args.get('symbol', '000001')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        df = get_stock_data(symbol, start_date=start_date, end_date=end_date)
        
        data = {
            'dates': [str(d) for d in df['date']],
            'prices': {
                'open': df['open'].tolist(),
                'close': df['close'].tolist(),
                'high': df['high'].tolist(),
                'low': df['low'].tolist(),
                'volume': df['volume'].tolist()
            },
            'symbol': symbol
        }
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/backtest', methods=['POST'])
def backtest():
    try:
        data = request.get_json()
        symbol = data.get('symbol', '000001')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        strategy_configs = data.get('strategies', [])
        initial_capital = data.get('initial_capital', 100000)
        price_mode = data.get('price_mode', 'close')
        
        df = get_stock_data(symbol, start_date=start_date, end_date=end_date)
        engine = BacktestEngine(initial_capital=initial_capital, price_mode=price_mode)
        result = engine.run_backtest(df, strategy_configs)
        result['symbol'] = symbol
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# Vercel 需要的入口
handler = app