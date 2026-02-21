"""
数据获取模块 - 使用tushare获取股票历史数据
"""
import os
import tushare as ts
import pandas as pd
from datetime import datetime, timedelta

# 设置tushare token（优先从环境变量读取）
TUSHARE_TOKEN = os.environ.get('TUSHARE_TOKEN', '289d3549685548f739cb8865e55b79c9fb7f8c5af173e4c5178786a4')
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()

# 全局数据缓存
_data_cache = {}


def get_stock_data(symbol: str, start_date: str = None, end_date: str = None, years: int = None) -> pd.DataFrame:
    """
    获取股票历史数据（带缓存）
    
    Args:
        symbol: 股票代码，如 '000001' 或 'sh000001'
        start_date: 开始日期，格式 'YYYYMMDD'
        end_date: 结束日期，格式 'YYYYMMDD'
        years: 回测年数，如果指定则忽略start_date
    
    Returns:
        DataFrame: 包含日期、开盘价、最高价、最低价、收盘价、成交量等
    """
    global _data_cache
    
    try:
        # 处理股票代码格式 - tushare使用 000001.SZ 格式
        if symbol.startswith('sh') or symbol.startswith('sz'):
            code = symbol[2:]
        else:
            code = symbol
        
        # 根据代码判断市场
        if code.startswith('6'):
            ts_code = f"{code}.SH"
        else:
            ts_code = f"{code}.SZ"
        
        # 设置默认日期范围
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        
        # 如果指定了年数，使用年数计算开始日期
        if years is not None:
            start_date = (datetime.now() - timedelta(days=years * 365)).strftime('%Y%m%d')
        elif start_date is None:
            # 默认2年
            start_date = (datetime.now() - timedelta(days=2 * 365)).strftime('%Y%m%d')
        
        # 检查缓存
        cache_key = f"{code}_{start_date}_{end_date}"
        if cache_key in _data_cache:
            print(f"使用缓存数据: {code}, 开始日期: {start_date}, 结束日期: {end_date}")
            return _data_cache[cache_key].copy()
        
        print(f"获取数据: {ts_code}, 开始日期: {start_date}, 结束日期: {end_date}")
        
        # 使用tushare获取数据
        df = pro.daily(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date
        )
        
        if df is None or len(df) == 0:
            raise Exception(f"未获取到数据: {ts_code}")
        
        # 重命名列以匹配原有格式
        df = df.rename(columns={
            'trade_date': 'date',
            'vol': 'volume',
            'amount': 'amount'
        })
        
        # 确保日期格式
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
        df = df.sort_values('date').reset_index(drop=True)
        
        # 选择需要的列
        columns_needed = ['date', 'open', 'high', 'low', 'close', 'volume']
        df = df[columns_needed]
        
        # 存入缓存
        _data_cache[cache_key] = df.copy()
        print(f"数据已缓存: {cache_key}")
        
        return df
        
    except Exception as e:
        print(f"获取股票数据失败: {e}")
        raise


# 中证A50成分股（50只）
ZZ_A50 = [
    {"code": "000001", "name": "平安银行"},
    {"code": "000002", "name": "万科A"},
    {"code": "000333", "name": "美的集团"},
    {"code": "000568", "name": "泸州老窖"},
    {"code": "000625", "name": "长安汽车"},
    {"code": "000651", "name": "格力电器"},
    {"code": "000703", "name": "恒逸石化"},
    {"code": "000725", "name": "京东方A"},
    {"code": "000768", "name": "中航西飞"},
    {"code": "000776", "name": "广发证券"},
    {"code": "000786", "name": "北新建材"},
    {"code": "000858", "name": "五粮液"},
    {"code": "000895", "name": "双汇发展"},
    {"code": "000988", "name": "华工科技"},
    {"code": "002007", "name": "华兰生物"},
    {"code": "002027", "name": "分众传媒"},
    {"code": "002050", "name": "三花智控"},
    {"code": "002120", "name": "韵达股份"},
    {"code": "002129", "name": "中环股份"},
    {"code": "002142", "name": "宁波银行"},
    {"code": "002241", "name": "歌尔股份"},
    {"code": "002271", "name": "东方雨虹"},
    {"code": "002352", "name": "顺丰控股"},
    {"code": "002371", "name": "北方华创"},
    {"code": "002415", "name": "海康威视"},
    {"code": "002475", "name": "立讯精密"},
    {"code": "002594", "name": "比亚迪"},
    {"code": "002624", "name": "完美世界"},
    {"code": "002673", "name": "西部证券"},
    {"code": "002714", "name": "牧原股份"},
    {"code": "002841", "name": "视源股份"},
    {"code": "300014", "name": "亿纬锂能"},
    {"code": "300033", "name": "同花顺"},
    {"code": "300059", "name": "东方财富"},
    {"code": "300308", "name": "中际旭创"},
    {"code": "300750", "name": "宁德时代"},
    {"code": "300760", "name": "迈瑞医疗"},
    {"code": "600028", "name": "中国石化"},
    {"code": "600030", "name": "中信证券"},
    {"code": "600036", "name": "招商银行"},
    {"code": "600048", "name": "保利发展"},
    {"code": "600104", "name": "上汽集团"},
    {"code": "600196", "name": "复星医药"},
    {"code": "600276", "name": "恒瑞医药"},
    {"code": "600309", "name": "万华化学"},
    {"code": "600519", "name": "贵州茅台"},
    {"code": "600887", "name": "伊利股份"},
    {"code": "600941", "name": "中国移动"},
    {"code": "601088", "name": "中国神华"},
    {"code": "601899", "name": "紫金矿业"},
]

# 热门股（92只）
HOT_STOCKS = [
    {"code": "605255", "name": "天普股份"},
    {"code": "603163", "name": "圣晖集成"},
    {"code": "002759", "name": "天际股份"},
    {"code": "603778", "name": "国晟科技"},
    {"code": "000592", "name": "平潭发展"},
    {"code": "600376", "name": "首开股份"},
    {"code": "000981", "name": "山子高科"},
    {"code": "002931", "name": "锋龙股份"},
    {"code": "002969", "name": "嘉美包装"},
    {"code": "000620", "name": "盈新发展"},
    {"code": "600408", "name": "安泰集团"},
    {"code": "600403", "name": "大有能源"},
    {"code": "001331", "name": "胜通能源"},
    {"code": "000070", "name": "特发信息"},
    {"code": "603626", "name": "科森科技"},
    {"code": "601869", "name": "长飞光纤"},
    {"code": "603122", "name": "合富中国"},
    {"code": "002792", "name": "通宇通讯"},
    {"code": "603929", "name": "亚翔集成"},
    {"code": "605303", "name": "园林股份"},
    {"code": "601212", "name": "白银有色"},
    {"code": "002083", "name": "孚日股份"},
    {"code": "603601", "name": "再升科技"},
    {"code": "000547", "name": "航天发展"},
    {"code": "002208", "name": "合肥城建"},
    {"code": "002471", "name": "中超控股"},
    {"code": "600629", "name": "华建集团"},
    {"code": "603256", "name": "宏和科技"},
    {"code": "603696", "name": "安记食品"},
    {"code": "002413", "name": "雷科防务"},
    {"code": "002150", "name": "正泰电源"},
    {"code": "600759", "name": "洲际油气"},
    {"code": "000892", "name": "欢瑞世纪"},
    {"code": "001330", "name": "博纳影业"},
    {"code": "600828", "name": "茂业商业"},
    {"code": "002796", "name": "世嘉科技"},
    {"code": "605188", "name": "国光连锁"},
    {"code": "000859", "name": "国风新材"},
    {"code": "600693", "name": "东百集团"},
    {"code": "002519", "name": "银河电子"},
    {"code": "600330", "name": "天通股份"},
    {"code": "605598", "name": "上海港湾"},
    {"code": "600410", "name": "华胜天成"},
    {"code": "002718", "name": "友邦吊顶"},
    {"code": "002512", "name": "达华智能"},
    {"code": "600783", "name": "鲁信创投"},
    {"code": "002361", "name": "神剑股份"},
    {"code": "603222", "name": "济民健康"},
    {"code": "003018", "name": "金富科技"},
    {"code": "603686", "name": "福龙马"},
    {"code": "002682", "name": "龙洲股份"},
    {"code": "000593", "name": "德龙汇能"},
    {"code": "002565", "name": "顺灏股份"},
    {"code": "002115", "name": "三维通信"},
    {"code": "002131", "name": "利欧股份"},
    {"code": "002342", "name": "巨力索具"},
    {"code": "600118", "name": "中国卫星"},
    {"code": "001267", "name": "汇绿生态"},
    {"code": "603516", "name": "淳中科技"},
    {"code": "600151", "name": "航天机电"},
    {"code": "001309", "name": "德明利"},
    {"code": "002181", "name": "粤传媒"},
    {"code": "000572", "name": "海马汽车"},
    {"code": "002636", "name": "金安国纪"},
    {"code": "000559", "name": "万向钱潮"},
    {"code": "001203", "name": "大中矿业"},
    {"code": "601116", "name": "三江购物"},
    {"code": "603618", "name": "杭电股份"},
    {"code": "002639", "name": "雪人集团"},
    {"code": "600105", "name": "永鼎股份"},
    {"code": "002264", "name": "新华都"},
    {"code": "600337", "name": "美克家居"},
    {"code": "603052", "name": "可川科技"},
    {"code": "601069", "name": "西部黄金"},
    {"code": "605288", "name": "凯迪股份"},
    {"code": "600021", "name": "上海电力"},
    {"code": "600172", "name": "黄河旋风"},
    {"code": "605178", "name": "时空科技"},
    {"code": "601231", "name": "环旭电子"},
    {"code": "002865", "name": "钧达股份"},
    {"code": "600103", "name": "青山纸业"},
    {"code": "002951", "name": "金时科技"},
    {"code": "601106", "name": "中国一重"},
    {"code": "001255", "name": "博菲电气"},
    {"code": "000632", "name": "三木集团"},
    {"code": "002716", "name": "湖南白银"},
    {"code": "601566", "name": "九牧王"},
    {"code": "002474", "name": "榕基软件"},
    {"code": "002513", "name": "蓝丰生化"},
    {"code": "002202", "name": "金风科技"},
    {"code": "600078", "name": "澄星股份"},
    {"code": "002163", "name": "海南发展"},
]


def get_stock_pools() -> dict:
    """
    获取股票池列表
    """
    return {
        "zz_a50": {"name": "中证A50", "count": len(ZZ_A50)},
        "hot": {"name": "热门股", "count": len(HOT_STOCKS)}
    }


def get_stock_list(pool: str = "hot") -> list:
    """
    获取股票列表
    
    Args:
        pool: 股票池类型，'zz_a50' 或 'hot'
    
    Returns:
        股票列表
    """
    if pool == "hot":
        return HOT_STOCKS[::-1]  # 热门股倒序返回
    else:
        return ZZ_A50


if __name__ == "__main__":
    # 测试数据获取
    df = get_stock_data("000001")
    print(df.head())
    print(f"\n获取到 {len(df)} 条数据")