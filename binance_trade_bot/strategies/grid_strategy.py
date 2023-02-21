from re import M
import time
import numpy as np
import matplotlib.pyplot as plt
import random
import sys
from datetime import datetime
from collections import deque

from matplotlib.cbook import print_cycles
from regex import B

from binance_trade_bot.strategies.base_strategy import BaseStrategy

# TODO: class to handle whole sequence (rsv, kdj, macd, ema)


def rsv(data):
    return 100 * (data[-1]-np.min(data)) / (np.max(data)-np.min(data))


def kdj(data, last_k, last_d):
    rsv_val = rsv(data)
    k = (2/3)*last_k + (1/3)*rsv_val
    d = (2/3)*last_d + (1/3)*last_k
    j = 3*d - 2*k
    return k, d, j


class Strategy(BaseStrategy):
    def initialize(self, coins):
        super().initialize(coins)
        self.initialize_current_coin()
        # self.prices = []
        # self.prices_trade = []
        # self.max_len = 10000
        # self.status = None
        # self.last_status = None
        self.action = None
        self.last_action = None
        # self.last_k = 50
        # self.last_d = 50
        self.trade_times = 0
        # self.total_fast = []
        # self.total_mid = []
        # self.total_slow = []
        self.trade_record = {}
        # self.pair = (self.config.CURRENT_COIN_SYMBOL, self.config.BRIDGE_SYMBOL)
        
        # self.buy_speed = 0.01
        # self.sell_speed = -0.08
        self.growth = 1.0
        
        self.min_price = 100000
        self.max_price = -100000
        # self.max_gap = None
        self.buy_event_count = None
        self.sell_flag = False
        self.hard_sell_price = None
        N = 10
        self.sell_points = {'corners': deque(maxlen=N), 'prices': deque(maxlen=N)}
        self.near_corners = deque(maxlen=32)
        
    def run(self, price_record):
        # Get
        # self.speed()
        self.momentum()
        # self.simple_ma_trade()
    
    def get_earn_rate(self, seq):
        cur_price = seq[-1]
        diff = (np.ones_like(seq) * cur_price) - seq
        earn = diff / cur_price
        return earn
        
    def simple_get_corner(self, prices, diff_len=1, smooth_len=5):
        if len(prices) <= smooth_len+diff_len+1:
            return None
        
        prices = prices[-smooth_len-diff_len-1:]
        prices_lag = prices.copy()
        diff = np.array(prices[diff_len:]) - np.array(prices_lag[:-diff_len])
        # diff = np.abs(diff)
        corner = prices[np.argmax(diff)]
        return corner
    
    def find_sell_point(self, prices, pool_size=3):
        prices = np.array(prices[-3:])
        corner = -(prices[1]-prices[0]) + (prices[2]-prices[1])
        corner_price = prices[2]
        self.near_corners.append(corner)
        
        if corner > max(list(self.near_corners)[:-1]):
            self.sell_points['corners'].append(corner)
            self.sell_points['prices'].append(corner_price)
            
        return self.sell_points['prices'][-1]
    
    def stop_trading(self, cur_price, last_trade_price, hard_stop):
        if self.last_action == 'buy':
            cur_earn = (cur_price-last_trade_price) / last_trade_price
            if cur_earn < hard_stop:
                self.action = 'sell'
        
    def find_sell_point_old(self, prices, pool_size=3):
        prices = np.array(prices[-3:])
        corners = self.get_corners(prices)
        max_corner, max_corner_price = np.max(corners), prices[np.argmax(corners)+1]

        if len(self.sell_points['corners']) >= pool_size:
            if max_corner > np.max(list(self.sell_points['corners'])[(-pool_size-1):]):
                self.sell_points['corners'].append(max_corner)
                self.sell_points['prices'].append(max_corner_price)
        else:
            self.sell_points['corners'].extend(corners[(-pool_size-1):])
            self.sell_points['prices'].extend(prices[(-pool_size-1):])
        return self.sell_points['prices'][-1]
        
    def get_corners(self, prices):
        mid = prices[1:-1]
        last = prices[:-2]
        next = prices[2:]
        corners = -(mid-last) + (next-mid)
        return corners
            
    def momentum(self):
        buy_speed = self.config.BUY_SPEED * self.growth
        sell_speed = self.config.SELL_SPEED
        long_buy_speed = 1.5 * buy_speed
        long_sell_speed = 1.5 * sell_speed
        seq_len = int(self.config.SEQ_LEN)
        mid_seq_len = 2 * seq_len
        long_seq_len = 8 * seq_len
        very_long_seq_len = 48 * 60 * seq_len
        max_seq_len = max([seq_len, mid_seq_len, long_seq_len, very_long_seq_len])
        order_ratio = 1.0
        earn_rate = 2
        bonus = 1.05
        # bonus = 1.15 # BAND 2021.11.1~2021.11.9
        # earn_rate = 0.15
        hard_sell_rate = -0.1
        stop_profit_decay = 0.99

        pair_str = f"{self.pair[0]}{self.pair[1]}"
        if self.action is not None:
            self.last_action = self.action

        # self.record_prices(pair_str)

        prices, timestamp = list(self.prices.values()), list(self.prices.keys())
        price = prices[-1]
        trade_record_list = list(self.trade_record.values())
        if len(trade_record_list) > 0:
            last_trade_info = trade_record_list[-1]

        if len(prices) > max_seq_len+1:
            earn_rates = self.get_earn_rate(prices)
            r = earn_rates[-seq_len-1]
            mid_r = earn_rates[-mid_seq_len-1]
            long_r = earn_rates[-long_seq_len-1]
            very_long_r = earn_rates[-very_long_seq_len-1]
            print(f'ratio={r:.4f}, mid_r={mid_r:.4f}, long_r={long_r:.4f}')
           
            if self.last_action != 'buy':
                if very_long_r > 0:
                    # if r > buy_speed:
                    if r > buy_speed and \
                    mid_r > buy_speed**bonus and \
                    long_r > (buy_speed**bonus)**bonus:
                        self.action = 'buy'
                        self.hard_sell_price = price * (1+hard_sell_rate)
                        # self.buy_event_count = 0
                    
            if self.last_action == 'buy':
                last_buy_price = list(self.trade_record.values())[-1]['price']
                if (price - last_buy_price) / last_buy_price > 0.03:
                    # stop_profit_price = self.simple_get_corner(self.prices)
                    stop_profit_price = self.find_sell_point(prices)
                    print('stop', stop_profit_price*stop_profit_decay)
                    if price < stop_profit_price*stop_profit_decay:
                        self.action = 'sell'
                
            if len(trade_record_list) > 0:
                if self.last_action == 'buy':
                    if price < self.hard_sell_price:
                        self.action = 'sell'
                        
                self.stop_trading(price, last_trade_info['price'], hard_sell_rate)
            # if len(trade_record_list) > 0:
            #     if price < last_trade_info['price']*1.2:
            #         self.action = 'sell'

        # Get oder quantity
        # XXX: temp
        current_coin = self.coins[0]
        if self.action == 'buy':
            order_quantity = \
                order_ratio * self.manager.balances[self.config.BRIDGE_SYMBOL]
        elif self.action == 'sell':
            order_quantity = \
                order_ratio * self.manager.balances[current_coin]
                # order_ratio * self.manager.balances[self.config.CURRENT_COIN_SYMBOL]
                
        # Trading
        if self.action is not None and self.action != self.last_action:
            singal = (self.action, self.pair, order_quantity)
            self.trade_worker(singal)
            
            self.trade_record[self.manager.datetime] = {
                'action': self.action,
                'quant': order_quantity,
                'price': price,
                'pair': pair_str
            }
            if self.action == 'sell':
                earn = (price-last_buy_price) / last_buy_price
                earn_str = f'{earn*100:.2f} %'
                self.trade_record[self.manager.datetime]['earn'] = earn_str
                print(f'trade times {self.trade_times}')
        # print(time.ctime(time.time()), self.manager.get_ticker_price(f'{self.config.CURRENT_COIN_SYMBOL}{self.config.BRIDGE_SYMBOL}'))
    
    def speed(self):
        buy_speed = self.config.BUY_SPEED * self.growth
        sell_speed = self.config.SELL_SPEED
        long_buy_speed = 1.5 * buy_speed
        long_sell_speed = 1.5 * sell_speed
        seq_len = int(self.config.SEQ_LEN)
        mid_seq_len = 2 * seq_len
        long_seq_len = 8 * seq_len
        max_seq_len = max([seq_len, mid_seq_len, long_seq_len])
        order_ratio = 1.0
        earn_rate = 2
        bonus = 1.05
        # earn_rate = 0.15
        hard_sell_rate = -0.15

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
            earn_rates = self.get_earn_rate(self.prices)
            r = earn_rates[-seq_len-1]
            mid_r = earn_rates[-mid_seq_len-1]
            long_r = earn_rates[-long_seq_len-1]
            print(f'ratio: {r}')
            # if self.buy_event_count is not None:
                # self.buy_event_count += 1
            
            # if long_r > 0:
            #     power = 1
            # else:
            #     power = 1.5
                
            if self.last_action != 'buy':
                if long_r > 0:
                    if r > buy_speed:
                    # if r > buy_speed and \
                    # mid_r > buy_speed*bonus and \
                    # long_r > buy_speed*(bonus**2):
                        self.action = 'buy'
                        self.hard_sell_price = price * (1+hard_sell_rate)
                        # self.buy_event_count = 0
                    

            # if self.last_action == 'buy':
            #     last_trade_price = trade_record_list[-1]['price']
            #     cur_r = (price-last_trade_price) / last_trade_price
            #     if cur_r < hard_sell_rate:
            #         self.action = 'sell'
            
                
            if self.last_action == 'buy':
                # TODO: lock status
                if not self.sell_flag:
                    if long_r < 0:
                        self.sell_flag = True
                    
                last_buy_price = list(self.trade_record.values())[-1]['price']
                if price > self.hard_sell_price*1.011:
                    if mid_r > 0:
                        self.hard_sell_price = price*0.93
                else:
                    if self.sell_flag:
                        if price > (1+0.02)*last_buy_price:
                            self.action = 'sell'
                            self.sell_flag = False
                        else:
                            if long_r < 0:
                                if r < sell_speed and \
                                mid_r < sell_speed*bonus and \
                                long_r < sell_speed*(bonus**2):
                                    self.action = 'sell'
                                    self.sell_flag = False
                    
                    
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
                if self.last_action == 'buy':
                    if price < self.hard_sell_price:
                        self.action = 'sell'
                        
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
            self.trade_worker(singal)
            
            self.trade_record[self.manager.datetime] = {
                'action': self.action,
                'quant': order_quantity,
                'price': price,
                'pair': pair_str
            }
            if self.action == 'sell':
                earn = (price-last_buy_price) / last_buy_price
                earn_str = f'{earn*100:.2f} %'
                self.trade_record[self.manager.datetime]['earn'] = earn_str
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
    