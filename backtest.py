import os

from datetime import datetime
from unittest.mock import MagicMixin
import matplotlib.pyplot as plt
from binance_trade_bot import backtest

values = []
time_record = []
if __name__ == "__main__":
    history = []
    os.makedirs('plot', exist_ok=True)
    for manager in backtest(datetime(2022, 4, 1), datetime.now()):
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

        # ##
        time_record.append(manager.datetime)
        prices = {coin: manager.get_ticker_price(f'{coin}{manager.config.BRIDGE.symbol}') \
            for coin in manager.balances if coin!=manager.config.BRIDGE.symbol}
        if None in list(prices.values()):
            break
        values.append(bridge_value)
        print(f'# {len(values)}')
        print("Prices:", prices)
        # if len(values) % 100 == 0:
        #     plt.plot(values)
        #     plt.savefig(f'plot/default-USDT-{time_record[0]}-{time_record[-1]}.png')
        
        with open('balance_log.txt', 'a+') as fw:
            fw.write("------\n")
            fw.write(f"TIME: {manager.datetime}\n")
            fw.write(f"BALANCES: {manager.balances}\n")
            fw.write(f"BTC VALUE: {btc_value} ({btc_diff}%)\n")
            fw.write(f"{manager.config.BRIDGE.symbol} VALUE: {bridge_value} ({bridge_diff}%)\n")
            fw.write("------\n")

    # plt.plot(time_record, values)
    # plt.plot(values)
    # plt.savefig(f'plot/default-USDT-{manager.datetime}.png')
    # print(f'Start Time: {time_record[0]}')
    # print(f'End Time: {time_record[-1]}')
    # plt.show()
