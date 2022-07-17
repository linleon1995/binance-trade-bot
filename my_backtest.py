import matplotlib.pyplot as plt
from datetime import datetime
from binance_trade_bot import backtest

if __name__ == "__main__":
    history = []
    profit = []
    idx = 0
    for manager in backtest(datetime(2022, 2, 1), datetime.now()):
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
        if idx % 200 == 0 and idx > 0:
            plt.plot(profit)
            plt.savefig(f'plot/ma/ma-USDT-{manager.datetime}.png')
            plt.show()
        idx += 1

        with open('balance_log.txt', 'a+') as fw:
            fw.write("------\n")
            fw.write(f"TIME: {manager.datetime}\n")
            fw.write(f"BALANCES: {manager.balances}\n")
            fw.write(f"BTC VALUE: {btc_value} ({btc_diff}%)\n")
            fw.write(f"{manager.config.BRIDGE.symbol} VALUE: {bridge_value} ({bridge_diff}%)\n")
            fw.write("------\n")
