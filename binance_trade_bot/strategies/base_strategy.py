from re import M
import time
import numpy as np
import matplotlib.pyplot as plt
import random
import sys
from datetime import datetime
from collections import deque, OrderedDict

from matplotlib.cbook import print_cycles
from regex import B

from binance_trade_bot.auto_trader import AutoTrader


class BaseStrategy(AutoTrader):
    def initialize(self):
        # super().initialize()
        self.initialize_current_coin()
        self.maxlen = 10000
        self.prices = OrderedDict()
        self.status = None
        self.action = None
        self.trade_times = 0
        self.pair = (self.config.CURRENT_COIN_SYMBOL, self.config.BRIDGE_SYMBOL)
        
        self.min_price = 100000
        self.max_price = -100000
        self.max_gap = None
        
    def scout(self):
        pair_str = f"{self.pair[0]}{self.pair[1]}"
        price_record = self.record_prices(pair_str)
        cur_price, cur_time = price_record
        self.check_stop_condition()
        self.get_max_gap(cur_price)
        self.run(price_record)
    
    def run(self, price_record):
        raise NotImplementedError
    
    def check_stop_condition(self):
        # TODO: -20% stop 
        balance = self.manager.get_currency_balance()
        
    def stop(self):
        raise KeyboardInterrupt
    
    def record_prices(self, pair_str):
        cur_price = self.manager.get_ticker_price(pair_str)
        if cur_price is not None:
            self.prices[self.manager.datetime] = cur_price
            return cur_price, self.manager.datetime
        else:
            return None, None
        
    def get_max_gap(self, cur_price):
        if cur_price < self.min_price:
            self.min_price = cur_price
            self.max_gap = (self.max_price-self.min_price) / self.min_price
            
        if cur_price > self.max_price:
            self.max_price = cur_price
            self.max_gap = (self.max_price-self.min_price) / self.min_price
            
    def get_earn_rate(self, seq):
        cur_price = seq[-1]
        diff = (np.ones_like(seq) * cur_price) - seq
        earn = diff / cur_price
        return earn
    
    def trade_worker(self, signal):
        trade, pair, quant = signal
        altcoin = self.db.get_coin(pair[0])
        pair_str = f'{pair[0]}{pair[1]}'

        if trade == 'sell':
            order = self.manager.sell_alt(altcoin, self.config.BRIDGE, quant)
            self.trade_times += 1

        if trade == 'buy':
            order = self.manager.buy_alt(altcoin, self.config.BRIDGE, quant)
        return order
            
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