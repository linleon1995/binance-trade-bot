import random
import sys
from datetime import datetime

from binance_trade_bot.auto_trader import AutoTrader


class Strategy(AutoTrader):
    def initialize(self):
        super().initialize()
        self.initialize_current_coin()

    def scout(self):
        # Get
        self.grid_strategy_trade()
    
    def grid_strategy_trade(self):
        # TODO: bridge coin
        # TODO: fit buy_alt api
        # TODO: amount for each trade
        # TODO: leverage --> this is about Binance API , can think later
        buy_thrshold = 0.7
        sell_threshold = -0.7
        end_trade_ratio_threshold = 0.8 # [0, 1] ma change more than threshold then end trade
        m = self.get_ma_slope()
        if m > buy_thrshold:
            self.buy_alt()
            while 1:
                m = self.get_ma_slope()
                if m < buy_thrshold*(1-end_trade_ratio_threshold):
                    self.sell_alt()
                    break
        # TODO: complete sell after buy success
        # elif m < sell_threshold:
        #     self.sell_alt()

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