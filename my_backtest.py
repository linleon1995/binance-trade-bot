from logging import handlers
import os
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt
from binance_trade_bot import backtest
# TODO: stop condition
# TODO: record more information
# TODO: why getting slower?
# TODO: compare with holding balance simply
# TODO: check the big drop in this year
# TODO: check the correctness of profit

        
def main():
    history = []
    profit = []
    idx = 0
    # TODO: long time
    # TODO: time zone problem
    start_time = datetime(2022, 10, 20)
    end_time = datetime(2022, 11, 4)
    save_time = 2 # day
    days = [start_time.day]
    pic_start = 0
    # end_time = datetime.now()
    start_time_str = datetime.strftime(start_time, r'%Y%m%d%H%M')
    end_time_str = datetime.strftime(end_time, r'%Y%m%d%H%M')
    init_time = start_time
    start_year = start_time.year
    start_month = start_time.month
    end_year = end_time.year
    end_month = end_time.month
    month_profit = {}
    no_strategy_profit = []
    total_time = []
    for manager, trader, recorder in backtest(start_time, end_time, interval=1, yield_interval=1):
        pair_str = f'{manager.config.CURRENT_COIN_SYMBOL}{manager.config.BRIDGE.symbol}'
        save_dir = f'plot/{pair_str}/speed'
        os.makedirs(save_dir, exist_ok=True)

        btc_value = manager.collate_coins("BTC")
        bridge_value = manager.collate_coins(manager.config.BRIDGE.symbol)
        history.append((btc_value, bridge_value))

        # TODO: this is not precise, we should also get the current bridge price
        
        target_price =  manager.get_ticker_price(pair_str)
        if target_price is not None:
            last_target_price = target_price
        else:
            target_price = last_target_price
        
        if len(no_strategy_profit) == 0:
            init_target_balance = bridge_value / target_price

        #     init_target_balance = bridge_value * target_price
        # else:
        #     no_strategy_value = 
        no_strategy_diff = round((init_target_balance*target_price-history[0][1]) / history[0][1] * 100, 3)
        
        # if target_price is not None:
        #     target_balance = target_price * history[0][0]
        #     no_strategy_value = history[0][1] + target_balance
        #     no_strategy_diff = round((no_strategy_value - history[0][1]) / history[0][1] * 100, 3)
        # else:
        #     no_strategy_diff = no_strategy_profit[-1]
        no_strategy_profit.append(no_strategy_diff)

        btc_diff = round((btc_value - history[0][0]) / history[0][0] * 100, 3)
        bridge_diff = round((bridge_value - history[0][1]) / history[0][1] * 100, 3)
        
        
        print("------")
        print("TIME:", manager.datetime)
        print("BALANCES:", manager.balances)
        # print("BTC VALUE:", btc_value, f"({btc_diff}%)")
        print(f"{manager.config.BRIDGE.symbol} VALUE:", bridge_value, f"({bridge_diff} %)")
        if trader.max_gap is not None:
            print(f"Max {trader.max_price} Min {trader.min_price}", f"({100*trader.max_gap:.4f} %)")
        print("------")

        total_time.append(manager.datetime)
        if total_time[-1].day != days[-1]:
            days.append(total_time[-1].day)

        # TODO: yearly and monthly profit plot
        profit.append(bridge_diff)
        print(idx)
        idx += 1
        
        # profit_plot(total_time, trader, manager, start_month, profit)
    # print(month_profit)
    # print(list(month_profit.values()))
    
    recorder.save(
        f'record/'
        f'{pair_str} | '
        f'len={manager.config.SEQ_LEN} | '
        f'B={manager.config.BUY_SPEED} | '
        f'S={manager.config.SELL_SPEED} | '
        f'profit={bridge_diff:.2f}% | '
        f'max={100*trader.max_gap:.2f}%.csv'
    )
    
    
if __name__ == "__main__":
    main()