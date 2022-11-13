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

if __name__ == "__main__":
    history = []
    profit = []
    idx = 0
    # TODO: long time
    start_time = datetime(2022, 10, 25)
    end_time = datetime(2022, 11, 6)
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
    for manager, trader in backtest(start_time, end_time, interval=15, yield_interval=1):
        pair_str = f'{manager.config.CURRENT_COIN_SYMBOL}{manager.config.BRIDGE.symbol}'
        save_dir = f'plot/{pair_str}/speed_15min_reverse_new'
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
        print(f"{manager.config.BRIDGE.symbol} VALUE:", bridge_value, f"({bridge_diff}%)")
        print("------")

        total_time.append(manager.datetime)
        if total_time[-1].day != days[-1]:
            days.append(total_time[-1].day)

        # TODO: yearly and monthly profit plot
        profit.append(bridge_diff)
        print(idx)
        
        if len(days) % (save_time+1) == 0 and total_time[-1].day != total_time[-2].day:
            pic_time = total_time[pic_start:-1]
            pic_profit = profit[pic_start:-1]
            pic_no_strategy = no_strategy_profit[pic_start:-1]
            pic_start = len(total_time)

            # XXX: plot fig to a single function for reusing
            pic_fig, pic_ax = plt.subplots(1,1)
            line1, = pic_ax.plot(pic_time, pic_profit, label='strategy')
            line2, = pic_ax.plot(pic_time, pic_no_strategy, label='no_strategy')
            pic_fig.autofmt_xdate()
            min_val = min(pic_profit)
            max_val = max(pic_profit)
            for trade_time in trader.trade_record:
                pic_start_day = pic_time[0].day
                pic_end_day = pic_time[-1].day
                # FIXME: not general
                if trade_time.day in list(range(pic_start_day, pic_end_day)):
                    trade_info = trader.trade_record[trade_time]
                    action = trade_info['action']
                    color = 'g' if action == 'buy' else 'r'
                    pic_ax.plot([trade_time, trade_time], [min_val, max_val], color)

            pic_ax.legend(handles=[line1, line2])
            pic_start_time = pic_time[0]
            pic_end_time = pic_time[-1]
            pic_start_time_str = datetime.strftime(pic_start_time, r'%Y%m%d%H%M')
            pic_end_time_str = datetime.strftime(pic_end_time, r'%Y%m%d%H%M')

            # time_str = f'{start_year}_{start_month}_{start_day}-{end_year}_{end_month}_{end_day}'
            filename = f'pic-{pic_start_time_str}-{pic_end_time_str}.png'
            pic_fig.savefig(os.path.join(save_dir, filename))
            plt.close(pic_fig)

        cur_month = manager.datetime.month
        
        # XXX:
        # FIXME: data_length problem
        # FIXME:  mometums = [total_time, total_time, total_time]
        mometums = [total_time, total_time, total_time]
        mometum_2nd = total_time
        if len(trader.prices) > 50:
            mometums = []
            for x in [8, 16, 24]:
                lag_prices = trader.prices.copy()
                mometum = (np.array(trader.prices[x:])-np.array(lag_prices[:-x])) / x
                mometum = np.concatenate([np.zeros(x+1), mometum])
                mometums.append(mometum)

            x = 8
            mometum = mometums[0]
            lag_prices = mometum.copy()
            mometum_2nd = (np.array(mometum[x:])-np.array(lag_prices[:-x])) / x
            mometum_2nd = np.concatenate([np.zeros(x), mometum_2nd])

        if True:
            fig, ax = plt.subplots(1,1)
            line1, = ax.plot(total_time, profit, label='strategy')
            line2, = ax.plot(total_time, no_strategy_profit, label='no_strategy')
            line3, = ax.plot(total_time, mometums[0], label='1st_momentum (m=8)')
            # line4, = ax.plot(total_time, mometums[1], label='m=16')
            # line5, = ax.plot(total_time, mometum_2nd, label='2nd_momentum (m=8)')
            # line5, = ax.plot(total_time, mometums[2], label='m=24')
            ax.grid(True)
            fig.autofmt_xdate()
            
            min_val = min(profit)
            max_val = max(profit)
            for trade_time in trader.trade_record:
                trade_info = trader.trade_record[trade_time]
                action = trade_info['action']
                color = 'g' if action == 'buy' else 'r'
                ax.plot([trade_time, trade_time], [min_val, max_val], color)

            ax.legend(handles=[line1, line2, line3])
            # ax.legend(handles=[line1, line2, line3, line4, line5])
            # ax.legend(['strategy', 'no_strategy'])
            
            # time_str = f'{start_year}_{start_month}-{end_year}_{end_month}'
            filename = f'total-{start_time_str}-{end_time_str}.png'
            fig.savefig(os.path.join(save_dir, filename))
            # plt.show()
            plt.close(fig)
            month_profit[start_month] = profit[-1] - profit[0]
            start_month = cur_month
        idx += 1

        with open('balance_log.txt', 'a+') as fw:
            fw.write("------\n")
            fw.write(f"TIME: {manager.datetime}\n")
            fw.write(f"BALANCES: {manager.balances}\n")
            fw.write(f"BTC VALUE: {btc_value} ({btc_diff}%)\n")
            fw.write(f"{manager.config.BRIDGE.symbol} VALUE: {bridge_value} ({bridge_diff}%)\n")
            fw.write("------\n")
    print(month_profit)
    print(list(month_profit.values()))