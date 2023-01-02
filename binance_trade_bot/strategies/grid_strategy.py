from re import M
import time
import numpy as np
import matplotlib.pyplot as plt
import random
import sys
from datetime import datetime

from matplotlib.cbook import print_cycles
from regex import B

from binance_trade_bot.auto_trader import AutoTrader

# TODO: class to handle whole sequence (rsv, kdj, macd, ema)


def rsv(data):
    return 100 * (data[-1]-np.min(data)) / (np.max(data)-np.min(data))


def kdj(data, last_k, last_d):
    rsv_val = rsv(data)
    k = (2/3)*last_k + (1/3)*rsv_val
    d = (2/3)*last_d + (1/3)*last_k
    j = 3*d - 2*k
    return k, d, j


class Strategy(AutoTrader):
    def initialize(self):
        # super().initialize()
        self.initialize_current_coin()
        self.prices = []
        # self.prices_trade = []
        self.max_len = 10000
        self.status = None
        self.last_status = None
        self.action = None
        self.last_action = None
        self.last_k = 50
        self.last_d = 50
        self.trade_times = 0
        self.total_fast = []
        self.total_mid = []
        self.total_slow = []
        self.trade_record = {}
        self.pair = (self.config.CURRENT_COIN_SYMBOL, self.config.BRIDGE_SYMBOL)
        
        self.buy_speed = 0.01
        self.sell_speed = -0.08
        self.growth = 1.0
        
        self.min_price = 100000
        self.max_price = -100000
        self.max_gap = None
        self.buy_event_count = None
        
    def scout(self):
        # Get
        self.speed()
        # self.simple_ma_trade()
    
    def record_prices(self, pair_str):
        cur_price = self.manager.get_ticker_price(pair_str)
        if cur_price < self.min_price:
            self.min_price = cur_price
            self.max_gap = (self.max_price-self.min_price) / self.min_price
            
        if cur_price > self.max_price:
            self.max_price = cur_price
            self.max_gap = (self.max_price-self.min_price) / self.min_price
            
        if cur_price is not None:
            self.prices.append(cur_price)
        else:
            return
        if len(self.prices) > self.max_len:
            self.prices.pop(0)

    def stop_trading(self, cur_price, last_trade_price, hard_stop):
        if self.last_action == 'buy':
            cur_earn = (cur_price-last_trade_price) / last_trade_price
            if cur_earn < hard_stop:
                self.action = 'sell'

    def get_earn_rate(self, seq, length):
        lag_seq = seq.copy()
        seq1 = np.array(seq[length:])
        seq2 = np.array(lag_seq[:-length])
        seq_diff = (seq1-seq2) / seq2
        r = seq_diff[-1]
        return r
        
    def simple_trader(self, signal):
        trade, pair, quant = signal
        altcoin = self.db.get_coin(pair[0])
        pair_str = f'{pair[0]}{pair[1]}'

        if trade == 'sell':
            self.manager.sell_alt(altcoin, self.config.BRIDGE, quant)
            self.trade_times += 1

        if trade == 'buy':
            self.manager.buy_alt(altcoin, self.config.BRIDGE, quant)
        price = self.manager.get_ticker_price(pair_str)
        self.trade_record[self.manager.datetime] = {
            'action': trade,
            'quant': quant,
            'price': price,
            'pair': pair_str
        }
        # self.prices_trade.append(price)
        
    def speed(self):
        buy_speed = self.config.BUY_SPEED * self.growth
        sell_speed = self.config.SELL_SPEED
        long_buy_speed = 1.5 * buy_speed
        long_sell_speed = 1.5 * sell_speed
        seq_len = int(self.config.SEQ_LEN)
        mid_seq_len = 12 * seq_len
        long_seq_len = 48 * seq_len
        max_seq_len = max([seq_len, mid_seq_len, long_seq_len])
        order_ratio = 1.0
        earn_rate = 2
        bonus = 1.1
        # earn_rate = 0.15
        hard_sell_rate = -0.1

        pair_str = f"{self.pair[0]}{self.pair[1]}"
        if self.action is not None:
            self.last_action = self.action

        self.record_prices(pair_str)

        price = self.prices[-1]
        trade_record_list = list(self.trade_record.values())
        if len(trade_record_list) > 0:
            last_trade_info = trade_record_list[-1]

        # if len(self.prices) > long_seq_len+1:  
        #     long_past_price = self.prices[-long_seq_len]
        #     long_r = (price - long_past_price) / long_past_price
        #     if long_r > 0:
        #         buy_speed = b
        #         sell_speed = s
        #     else:
        #         buy_speed = s
        #         sell_speed = b

        if len(self.prices) > max_seq_len+1:
            r = self.get_earn_rate(self.prices, seq_len)
            mid_r = self.get_earn_rate(self.prices, mid_seq_len)
            long_r = self.get_earn_rate(self.prices, long_seq_len)
            print(f'ratio: {r}')
            # if self.buy_event_count is not None:
                # self.buy_event_count += 1
            
            # if long_r > 0:
            #     power = 1
            # else:
            #     power = 1.5
                
            if long_r > 0:
                if r > buy_speed and \
                   mid_r > buy_speed*bonus and \
                   long_r > buy_speed*(bonus**2):
                    self.action = 'buy'
                    # self.buy_event_count = 0
                    

            # if self.last_action == 'buy':
            #     last_trade_price = trade_record_list[-1]['price']
            #     cur_r = (price-last_trade_price) / last_trade_price
            #     if cur_r < hard_sell_rate:
            #         self.action = 'sell'
            
            if self.last_action == 'buy':
                last_buy_price = list(self.trade_record.values())[-1]['price']
                if price > (1+0.02)*last_buy_price:
                    if long_r < 0:
                        if r < sell_speed and \
                        mid_r < sell_speed*bonus and \
                        long_r < sell_speed*(bonus**2):
                            self.action = 'sell'
                    
                    
            # if self.last_action == 'buy':
            #     if mid_r < sell_speed:
            #         self.action = 'sell'
                    
            # if mid_r < sell_speed and \
            #    self.last_action == 'buy':
            #     self.action = 'sell'
                
            # if long_r < long_sell_speed and \
            #    self.last_action == 'buy':
            #     self.action = 'sell'
                
            # if self.buy_event_count is not None:
            #     if r < 0 and self.buy_event_count > 4*mid_seq_len:
            #         self.action = 'sell'
            #         self.buy_event_count = None
                
                # TODO: This is the reset to avoid over-trading
                # but will cause the bad result when plotting
                # self.prices = [price]  

            # # TODO: INcorrect: 
            # if self.last_action == 'buy':
            #     if r < hard_sell_rate:
            #         self.action = 'sell'
            if len(trade_record_list) > 0:
                self.stop_trading(price, last_trade_info['price'], hard_sell_rate)
            # if len(trade_record_list) > 0:
            #     if price < last_trade_info['price']*1.2:
            #         self.action = 'sell'

        # Get oder quantity
        if self.action == 'buy':
            order_quantity = \
                order_ratio * self.manager.balances[self.config.BRIDGE_SYMBOL]
        elif self.action == 'sell':
            order_quantity = \
                order_ratio * self.manager.balances[self.config.CURRENT_COIN_SYMBOL]
                
        # Trading
        if self.action is not None and self.action != self.last_action:
            singal = (self.action, self.pair, order_quantity)
            self.simple_trader(singal)
            if self.action == 'sell':
                print(f'trade times {self.trade_times}')
        # print(time.ctime(time.time()), self.manager.get_ticker_price(f'{self.config.CURRENT_COIN_SYMBOL}{self.config.BRIDGE_SYMBOL}'))
    
    def moving_average(self, x, w):
        return np.convolve(x, np.ones(w), 'valid') / w

    def backtest_and_plot_ma(self):
        N = 2000
        # m = self.get_
        cur_price = self.manager.get_ticker_price(f'{self.config.CURRENT_COIN_SYMBOL}{self.config.BRIDGE_SYMBOL}')
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