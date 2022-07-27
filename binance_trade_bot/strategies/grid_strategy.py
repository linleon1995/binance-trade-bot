from re import M
import time
import numpy as np
import matplotlib.pyplot as plt
import random
import sys
from datetime import datetime

from matplotlib.cbook import print_cycles

from binance_trade_bot.auto_trader import AutoTrader


class Strategy(AutoTrader):
    def initialize(self):
        # super().initialize()
        self.initialize_current_coin()
        self.prices = []
        self.max_len = 2000
        self.status = None

    def scout(self):
        # Get
        self.simple_ma_trade()
    
    def grid_strategy_trade(self):
        # TODO: bridge coin
        # TODO: fit buy_alt api
        # TODO: amount for each trade
        # TODO: leverage --> this is about Binance API , can think later
        buy_thrshold = 0.7
        sell_threshold = -0.7
        end_trade_ratio_threshold = 0.8 # [0, 1] ma change more than threshold then end trade
        
    def simple_ma_trade(self):
        ma_lenth1 = 7 * 60
        ma_lenth2 = 25 * 60 * 2
        cur_price = self.manager.get_ticker_price("ETHUSDT")
        if cur_price is None:
            return
        if cur_price is not None:
            self.prices.append(cur_price)
        if len(self.prices) > self.max_len:
            self.prices.pop(0)

        if len(self.prices) >= max(ma_lenth1, ma_lenth2):
            ma1 = np.mean(self.prices[-ma_lenth1:])
            ma2 = np.mean(self.prices[-ma_lenth2:])

            if self.status:
                if ma1 > ma2:
                # if ma1 > ma2 and (ma1-ma2)/ma2>0.5:
                    if self.status == 'sell':
                        altcoin = self.db.get_coin("ETH")
                        order_quantity = 0.1 * self.manager.balances[self.config.BRIDGE_SYMBOL]
                        self.manager.buy_alt(altcoin, self.config.BRIDGE, order_quantity)
                    self.status = 'buy'
                else:
                # elif ma1 < ma2 and (ma2-ma1)/ma1>0.5:
                    if self.status == 'buy':
                        altcoin = self.db.get_coin("ETH")
                        order_quantity = 0.1 * self.manager.balances[self.config.BRIDGE_SYMBOL]
                        self.manager.sell_alt(altcoin, self.config.BRIDGE, order_quantity)
                    self.status = 'sell'
            else:
                self.status = 'buy' if ma1 > ma2 else 'sell'

            # print(self.manager.datetime, self.status)

        # print(time.ctime(time.time()), self.manager.get_ticker_price("ETHUSDT"))
    def moving_average(self, x, w):
        return np.convolve(x, np.ones(w), 'valid') / w

    def backtest_and_plot_ma(self):
        N = 2000
        # m = self.get_
        cur_price = self.manager.get_ticker_price("ETHUSDT")
        self.prices.append(cur_price)
        cur_len = len(self.prices)
        # if cur_len > self.max_len:
        #     self.prices.pop(0)
        if cur_len == N+240-1:
            ma_15 = self.moving_average(self.prices, 15)
            ma_60 = self.moving_average(self.prices, 60)
            ma_240 = self.moving_average(self.prices, 240)

            ma_15 = ma_15[len(ma_15)-N:]
            ma_60 = ma_60[len(ma_60)-N:]
            prices = self.prices[len(self.prices)-N:]

            if len(ma_240) == N:
                r = 200
                for i in range(0, N, r):
                    fig, ax = plt.subplots(1, 1)
                    ax.plot(prices[i:i+r])
                    ax.plot(ma_15[i:i+r])
                    ax.plot(ma_60[i:i+r])
                    ax.plot(ma_240[i:i+r])
                    ax.legend(['price', '15', '60', '240'])
                    fig.savefig(f'plot/ma/ma_{i}_{i+r}.png')
    
    def bridge_scout(self):
        current_coin = self.db.get_current_coin()
        if self.manager.get_currency_balance(current_coin.symbol) > self.manager.get_min_notional(
            current_coin.symbol, self.config.BRIDGE.symbol
        ):
            # Only scout if we don't have enough of the current coin
            return
        new_coin = super().bridge_scout()
        if new_coin is not None:
            self.db.set_current_coin(new_coin)

    def initialize_current_coin(self):
        """
        Decide what is the current coin, and set it up in the DB.
        """
        if self.db.get_current_coin() is None:
            current_coin_symbol = self.config.CURRENT_COIN_SYMBOL
            if not current_coin_symbol:
                current_coin_symbol = random.choice(self.config.SUPPORTED_COIN_LIST)

            self.logger.info(f"Setting initial coin to {current_coin_symbol}")

            if current_coin_symbol not in self.config.SUPPORTED_COIN_LIST:
                sys.exit("***\nERROR!\nSince there is no backup file, a proper coin name must be provided at init\n***")
            self.db.set_current_coin(current_coin_symbol)

            # if we don't have a configuration, we selected a coin at random... Buy it so we can start trading.
            if self.config.CURRENT_COIN_SYMBOL == "":
                current_coin = self.db.get_current_coin()
                self.logger.info(f"Purchasing {current_coin} to begin trading")
                self.manager.buy_alt(current_coin, self.config.BRIDGE)
                self.logger.info("Ready to start trading")