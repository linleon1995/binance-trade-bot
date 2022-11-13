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
        self.max_len = 1000
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
        
    def scout(self):
        # Get
        # self.slow_fast_ma_trade()
        # self.slow_fast_ma_kdj_trade()
        # self.slow_fast_ma_kdj_trade_new()
        self.speed()
        # self.simple_ma_trade()
    
    def grid_strategy_trade(self):
        # TODO: bridge coin
        # TODO: fit buy_alt api
        # TODO: amount for each trade
        # TODO: leverage --> this is about Binance API , can think later
        buy_thrshold = 0.7
        sell_threshold = -0.7
        end_trade_ratio_threshold = 0.8 # [0, 1] ma change more than threshold then end trade
        
    def simple_ma_trade(self):
        use_margin = True
        buy_margin = 0.1
        sell_margin = 0.1
        ma_lenth = 25

        cur_price = self.manager.get_ticker_price(f'{self.config.CURRENT_COIN_SYMBOL}{self.config.BRIDGE_SYMBOL}')
        if cur_price is not None:
            self.prices.append(cur_price)
        else:
            return
        if len(self.prices) > self.max_len:
            self.prices.pop(0)

        if len(self.prices) >= ma_lenth:
            ma = np.mean(self.prices[-ma_lenth:])

        if not self.status:
            if cur_price < ma*(1-buy_margin):
                altcoin = self.db.get_coin(self.config.CURRENT_COIN_SYMBOL)
                order_quantity = 0.1 * self.manager.balances[self.config.BRIDGE_SYMBOL]
                self.manager.buy_alt(altcoin, self.config.BRIDGE, order_quantity)
                # TODO: sell if earn money (not nessecary)
                buy_price = cur_price
                self.status = True
        else:
            if cur_price >= ma*(1+sell_margin) and cur_price > buy_price:
                altcoin = self.db.get_coin(self.config.CURRENT_COIN_SYMBOL)
                order_quantity = 0.1 * self.manager.balances[self.config.BRIDGE_SYMBOL]
                self.manager.sell_alt(altcoin, self.config.BRIDGE, order_quantity)
                self.status = False

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

    def record_prices(self, pair_str):
        cur_price = self.manager.get_ticker_price(pair_str)
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

    def speed(self):

        b = 10e-5
        s = -10e-5
        # b = 4
        # s = -4
        # b = 0.04
        # s = -0.04
        buy_speed = b
        sell_speed = s
        seq_len = 8
        long_seq_len = 12 * seq_len
        order_ratio = 1.0
        earn_rate = 0.01
        # earn_rate = 0.15
        hard_sell_rate = -0.07

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

        if len(self.prices) > seq_len+1:
            # past_price = self.prices[-seq_len]

            lag_prices = self.prices.copy()
            mometum = (np.array(self.prices[seq_len:])-np.array(lag_prices[:-seq_len])) / seq_len
            mometum = np.concatenate([np.zeros(seq_len+1), mometum])
            r = mometum[-1]
            print(f'r: {r}')

            # r = (price - past_price) / past_price
            if r > buy_speed:
                self.action = 'buy'
            # if r < sell_speed and \
            #    self.last_action == 'buy':
            if r < sell_speed and \
               self.last_action == 'buy' and \
               price > last_trade_info['price']*(1+earn_rate):
                self.action = 'sell'
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


    def slow_fast_ma_kdj_trade_new(self):
        fast_interval = 7
        mid_interval = 25
        slow_interval = 99
        gap = 0.005
        k_min = 65
        k_max = 80
        order_ratio = 1.0
        # FIXME: 100000 for testing change back to 0.05
        surrender_ratio = 100000
        earn_rate = 0.02
        pair_str = f"{self.pair[0]}{self.pair[1]}"

        cur_price = self.manager.get_ticker_price(pair_str)
        if cur_price is not None:
            self.prices.append(cur_price)
        else:
            return
        if len(self.prices) > self.max_len:
            self.prices.pop(0)

        if len(self.prices) >= max(fast_interval, slow_interval):
            fast = np.mean(self.prices[-fast_interval:])
            mid = np.mean(self.prices[-mid_interval:])
            slow = np.mean(self.prices[-slow_interval:])
            self.total_fast.append(fast)
            self.total_mid.append(mid)
            self.total_slow.append(slow)
            # k, d, j = kdj(self.prices[-9:], self.last_k, self.last_d)
            # self.last_k = k
            # self.last_d = d

            if self.status is not None:
                self.last_status = self.status
            if fast > slow * (1+gap):
                self.status = 'long'
            if fast-mid <= mid * (0.002):
                self.status = 'short'
            # else:
            #     self.status = None

            if self.action is not None:
                self.last_action = self.action


            price = self.manager.get_ticker_price(pair_str)
            trade_record_list = list(self.trade_record.values())
            if len(trade_record_list) > 0:
                last_trade_info = trade_record_list[-1]
                
            # speed = 0.1
            # seq_len = 8
            # if len(trade_record_list) > seq_len+1:
            #     past_price = trade_record_list[-seq_len]['price']
            #     r = (price - past_price) / past_price
            #     if r > speed and self.last_action == 'sell':
            #         self.action = 'buy'
            #     if r < -speed and self.last_action == 'buy':
            #         self.action = 'sell'

            # Get trading action
            if self.last_status == 'short' and self.status == 'long':
                self.action = 'buy'
            elif self.last_status == 'long' and \
                 self.status == 'short' and \
                 self.last_action == 'buy'and \
                 price > last_trade_info['price']*(1+earn_rate):
                self.action = 'sell'
            else:
                self.action = None

            # Surrender
            if len(trade_record_list) > 0 and \
               price < (1-surrender_ratio)*last_trade_info['price']:
                self.action = 'sell' 

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

    def slow_fast_ma_trade(self):
        ma_lenth1 = 7 * 15
        ma_lenth2 = 99 * 15
        cur_price = self.manager.get_ticker_price(f'{self.config.CURRENT_COIN_SYMBOL}{self.config.BRIDGE_SYMBOL}')
        if cur_price is not None:
            self.prices.append(cur_price)
        else:
            return
        if len(self.prices) > self.max_len:
            self.prices.pop(0)

        if len(self.prices) >= max(ma_lenth1, ma_lenth2):
            ma1 = np.mean(self.prices[-ma_lenth1:])
            ma2 = np.mean(self.prices[-ma_lenth2:])

            if self.status:
                if ma1 > ma2:
                # if ma1 > ma2 and (ma1-ma2)/ma2>0.5:
                    if self.status == 'sell':
                        altcoin = self.db.get_coin(self.config.CURRENT_COIN_SYMBOL)
                        order_quantity = 0.1 * self.manager.balances[self.config.BRIDGE_SYMBOL]
                        self.manager.buy_alt(altcoin, self.config.BRIDGE, order_quantity)
                    self.status = 'buy'
                else:
                # elif ma1 < ma2 and (ma2-ma1)/ma1>0.5:
                    if self.status == 'buy':
                        altcoin = self.db.get_coin(self.config.CURRENT_COIN_SYMBOL)
                        order_quantity = 0.1 * self.manager.balances[self.config.BRIDGE_SYMBOL]
                        self.manager.sell_alt(altcoin, self.config.BRIDGE, order_quantity)
                    self.status = 'sell'
            else:
                self.status = 'buy' if ma1 > ma2 else 'sell'

            # print(self.manager.datetime, self.status)

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