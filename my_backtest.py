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
    init_time = start_time
    start_month = start_time.month
    for manager in backtest(start_time, datetime.now()):
        btc_value = manager.collate_coins("BTC")
        bridge_value = manager.collate_coins(manager.config.BRIDGE.symbol)
        history.append((btc_value, bridge_value))
        btc_diff = round((btc_value - history[0][0]) / history[0][0] * 100, 3)
        bridge_diff = round((bridge_value - history[0][1]) / history[0][1] * 100, 3)
        print("------")
        print("TIME:", manager.datetime)
        print("BALANCES:", manager.balances)
        print("BTC VALUE:", btc_value, f"({btc_diff}%)")
        print(f"{manager.config.BRIDGE.symbol} VALUE:", bridge_value, f"({bridge_diff}%)")
        print("------")
        
        # TODO: start and end time
        profit.append(bridge_diff)
        # if bridge_diff < -40: #idx=593 923
        #     print(bridge_diff)
        print(idx)
        if idx == 591:
            print(3)
        cur_month = manager.datetime.month
        # if cur_month > start_month:
        if idx%100==0 and idx>0:
            plt.plot(profit[-100:])
            # time_record = 
            plt.savefig(
                f'plot/ma/ma-USDT-{init_time.month}-{cur_month}-step{idx}.png')
            plt.show()
            start_month = cur_month
        idx += 1

        with open('balance_log.txt', 'a+') as fw:
            fw.write("------\n")
            fw.write(f"TIME: {manager.datetime}\n")
            fw.write(f"BALANCES: {manager.balances}\n")
            fw.write(f"BTC VALUE: {btc_value} ({btc_diff}%)\n")
            fw.write(f"{manager.config.BRIDGE.symbol} VALUE: {bridge_value} ({bridge_diff}%)\n")
            fw.write("------\n")
