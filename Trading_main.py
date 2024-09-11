import pandas as pd
from Data import getData
from BackTest import ChartTrade, Performance
import mplfinance as mpf
from talib.abstract import EMA, ATR

# 取得回測資料
prod = '0050'
data = getData(prod, '2013-01-01', '2022-05-01')

# 計算指數移動平均線和ATR
data['ema'] = EMA(data, timeperiod=80)
data['atr1'] = ATR(data, timeperiod=120)
data['atr2'] = ATR(data, timeperiod=200)

# 交易策略參數
stop_loss_pct = 0.3  # 止損百分比
take_profit_pct = 0.1  # 止盈百分比
risk_multiplier = 0.1  # ATR 風險乘數

# 初始變數
position = 0
trade = pd.DataFrame()
order_price = None
order_time = None

# 回測策略
for i in range(len(data) - 1):
    # 取得當前和下一期的數據
    c_time = data.index[i]
    c_close = data.loc[c_time, 'close']
    c_ema = data.loc[c_time, 'ema']
    c_atr1 = data.loc[c_time, 'atr1']
    c_atr2 = data.loc[c_time, 'atr2']
    
    n_time = data.index[i + 1]
    n_open = data.loc[n_time, 'open']

    # 進場條件：收盤價高於 EMA，ATR 高於一定閾值
    if position == 0 and c_close > c_ema and c_atr1 > c_atr2 * risk_multiplier:
        position = 1
        order_price = n_open
        order_time = n_time
        print(f"進場：{n_time}, 價格：{n_open}")

    # 出場條件：當前價格低於 EMA 或價格達到止損/止盈
    elif position == 1:
        # 計算止損和止盈價格
        stop_loss_price = order_price * (1 - stop_loss_pct)
        take_profit_price = order_price * (1 + take_profit_pct)

        # 觸發止損或止盈
        if n_open <= stop_loss_price or n_open >= take_profit_price:
            position = 0
            trade = pd.concat([trade, pd.DataFrame([[
                prod, 'Buy', order_time, order_price, n_time, n_open, 1
            ]])], ignore_index=True)
            print(f"出場：{n_time}, 價格：{n_open}, 原因：止損/止盈")

        # 平倉條件：收盤價低於 EMA
        elif n_open < c_ema:
            position = 0
            trade = pd.concat([trade, pd.DataFrame([[
                prod, 'Buy', order_time, order_price, n_time, n_open, 1
            ]])], ignore_index=True)
            print(f"出場：{n_time}, 價格：{n_open}, 原因：EMA交叉")

# 繪製副圖
addp = []
addp.append(mpf.make_addplot(data['ema'], color='blue'))
addp.append(mpf.make_addplot(data['atr1'], panel=2, color='orange', secondary_y=True))
addp.append(mpf.make_addplot(data['atr2'], panel=2, color='green', secondary_y=True))

# 績效分析
Performance(trade, 'ETF')
# 繪製K線圖與交易明細
ChartTrade(data, addp=addp)
