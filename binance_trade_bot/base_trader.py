from datetime import datetime
from typing import Dict, List

from sqlalchemy.orm import Session

from .binance_api_manager import BinanceAPIManager
from .config import Config
from .database import Database
from .logger import Logger
from .models import Coin, CoinValue, Pair


class BaseTader:
    def __init__(self, binance_manager: BinanceAPIManager, 
                 database: Database, logger: Logger, config: Config):
        self.manager = binance_manager
        self.db = database
        self.logger = logger
        self.config = config
        
        self.lose_times = 0
        self.max_lose_times = config.max_lose_times
    
    def run(self):
        self.strategy()
    
    def strategy(self):
        raise NotImplementedError()
        
    def stop(self):
        if self.lose_times > self.max_lose_times:
            return True
        else:
            return False
    
    def pause(self):
        pass
    
    
if __name__ == '__main__':
    trader = BaseTader()
    trader.run()