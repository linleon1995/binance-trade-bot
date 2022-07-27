from logging import handlers
import os
import matplotlib.pyplot as plt
from datetime import datetime
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
    start_time = datetime(2021, 1, 1)
    end_time = datetime(2022, 1, 1)
    # end_time = datetime.now()
    init_time = start_time
    start_year = start_time.year
    start_month = start_time.month
    end_year = end_time.year
    end_month = end_time.month
    month_profit = {}
    save_dir = 'plot/ma/2021'
    os.makedirs(save_dir, exist_ok=True)
    no_strategy_profit = []
    for manager in backtest(start_time, end_time):
        btc_value = manager.collate_coins("BTC")
        bridge_value = manager.collate_coins(manager.config.BRIDGE.symbol)
        history.append((btc_value, bridge_value))

        # TODO: this is not precise, we should also get the current bridge price
        
        target_price =  manager.get_ticker_price('ETHUSDT')
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
        print("BTC VALUE:", btc_value, f"({btc_diff}%)")
        print(f"{manager.config.BRIDGE.symbol} VALUE:", bridge_value, f"({bridge_diff}%)")
        print("------")
        
        # TODO: yearly and monthly profit plot
        profit.append(bridge_diff)
        # if bridge_diff < -40: #idx=593 923
        #     print(bridge_diff)
        print(idx)
        # if idx == 591:
        #     print(3)
        cur_month = manager.datetime.month
        if cur_month > start_month:
        # if idx%100==0 and idx>0:
            fig, ax = plt.subplots(1,1)
            line1, = ax.plot(profit, label='strategy')
            line2, = ax.plot(no_strategy_profit, label='no_strategy')
            ax.legend(handles=[line1, line2])
            # ax.legend(['strategy', 'no_strategy'])
            
            filename = f'ma-ETHUSDT-{start_year}_{start_month}-{end_year}_{end_month}.png'
            fig.savefig(os.path.join(save_dir, filename))
            # plt.show()
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