from logging import handlers
import os
from datetime import datetime
from dataclasses import dataclass

import numpy as np
from pprint import pprint
import matplotlib.pyplot as plt
import yaml

from binance_trade_bot import backtest
from binance_trade_bot.grid_config import Config
# TODO: stop condition
# TODO: record more information
# TODO: why getting slower?
# TODO: compare with holding balance simply
# TODO: check the big drop in this year
# TODO: check the correctness of profit
CONFIG = 'backtest_setting.yaml'

     
    
def main(cfg):
    history = []
    profit = []
    idx = 0
    # TODO: time zone problem
    save_time = 2 # day
    
    # start_time = datetime(2022, 10, 20)
    # end_time = datetime(2022, 11, 4)
    start_time = datetime(*cfg['START_TIME'])
    end_time = datetime(*cfg['END_TIME'])
    
    # days = [start_time.day]
    # pic_start = 0
    # # end_time = datetime.now()
    # start_time_str = datetime.strftime(start_time, r'%Y%m%d%H%M')
    # end_time_str = datetime.strftime(end_time, r'%Y%m%d%H%M')
    # init_time = start_time
    # start_year = start_time.year
    # start_month = start_time.month
    # end_year = end_time.year
    # end_month = end_time.month
    # month_profit = {}
    no_strategy_profit = []
    total_time = []
    manager, _, _ = next(backtest(start_time, end_time, interval=1, yield_interval=1))
    coin_list = manager.config.SUPPORTED_COIN_LIST
    if cfg['TEST_COINS']:
        for coin in cfg['TEST_COINS']:
            assert coin in coin_list, f'{coin} not insupported_coin_list'
        coin_list = cfg['TEST_COINS']
        
    if cfg['SOLO_TEST']:
        backtest_coins = [[coin] for coin in coin_list]
    else:
        backtest_coins = [coin_list]
        
    coins = {}
    for test_coins in backtest_coins:
        for manager, trader, recorder in backtest(start_time, end_time, interval=1, yield_interval=1, coins=test_coins):
            # XXX: temporally
            coin = test_coins[0]
            try:
                pair_str = f'{coin}{manager.config.BRIDGE.symbol}'
                save_dir = f'plot/{pair_str}/speed'
                os.makedirs(save_dir, exist_ok=True)

                # btc_value = manager.collate_coins("BTC")
                bridge_value = manager.collate_coins(manager.config.BRIDGE.symbol)
                btc_value = bridge_value
                history.append((btc_value, bridge_value))

                # TODO: this is not precise, we should also get the current bridge price
                
                # target_price = manager.get_ticker_price(pair_str)
                # if target_price is not None:
                #     last_target_price = target_price
                # else:
                #     target_price = last_target_price
                
                # if len(no_strategy_profit) == 0:
                #     init_target_balance = bridge_value / target_price

                #     init_target_balance = bridge_value * target_price
                # else:
                #     no_strategy_value = 
                no_strategy_diff = round((bridge_value-history[0][1]) / history[0][1] * 100, 3)
                
                # if target_price is not None:
                #     target_balance = target_price * history[0][0]
                #     no_strategy_value = history[0][1] + target_balance
                #     no_strategy_diff = round((no_strategy_value - history[0][1]) / history[0][1] * 100, 3)
                # else:
                #     no_strategy_diff = no_strategy_profit[-1]
                no_strategy_profit.append(no_strategy_diff)

                btc_diff = round((btc_value - history[0][0]) / history[0][0] * 100, 3)
                bridge_diff = round((bridge_value - history[0][1]) / history[0][1] * 100, 3)
                
                
                print("------")
                print("COIN:", coin)
                print("TIME:", manager.datetime)
                print("BALANCES:", manager.balances)
                # print("BTC VALUE:", btc_value, f"({btc_diff}%)")
                print(f"{manager.config.BRIDGE.symbol} VALUE:", bridge_value, f"({bridge_diff} %)")
                if trader.max_gap is not None:
                    print(f"Max {trader.max_price} Min {trader.min_price}", f"({100*trader.max_gap:.4f} %)")
                print("------")

                total_time.append(manager.datetime)
                # if total_time[-1].day != days[-1]:
                #     days.append(total_time[-1].day)

                # TODO: yearly and monthly profit plot
                profit.append(bridge_diff)
                print(idx)
                idx += 1
            except:
                print(f'Fail to get {coin}')
                break
            
            # profit_plot(total_time, trader, manager, start_month, profit)
        # print(month_profit)
        # print(list(month_profit.values()))
        coins[coin] = {'earn': bridge_diff, 'max_gap': 100*trader.max_gap}
        # TODO: max_gap problem
        # recorder.save(
        #     f'record/'
        #     f'{pair_str} | '
        #     f'len={manager.config.SEQ_LEN} | '
        #     f'B={manager.config.BUY_SPEED} | '
        #     f'S={manager.config.SELL_SPEED} | '
        #     f'profit={bridge_diff:.2f}% | '
        #     f'max={100*trader.max_gap:.2f}%.csv'
        # )
    # pprint(coins)
    avg_earn = 0
    avg_gap = 0
    avg_diff = 0
    result = []
    for coin_name, info in coins.items():
        earn_diff = info["earn"] - info["max_gap"]
        coin_result = f'{coin_name} earn: {info["earn"]:.2f} %  gap: {info["max_gap"]:.2f} % diff {earn_diff:.2f} %'
        print(coin_result)
        result.append(coin_result)
        avg_earn += info['earn']
        avg_gap += info['max_gap']
        avg_diff += earn_diff
    avg_earn /= len(list(coins.keys()))
    avg_gap /= len(list(coins.keys()))
    avg_diff /= len(list(coins.keys()))
    result.append(20*'-')
    result.append(f'Earn (avg) {avg_earn:.2f} %')
    result.append(f'Gap (avg) {avg_gap:.2f} %')
    result.append(f'Diff (avg) {avg_diff:.2f} %')
        
    # import git
    # repo = git.Repo(search_parent_directories=True)
    # sha = repo.head.object.hexsha
    with open(f'test_record.txt', 'a+') as fw:
        fw.write('\n')
        fw.write(f'start_time: {start_time}\n')
        fw.write(f'end_time: {end_time}\n')
        # print(f'git commit: {sha}')
        for r in result:
            fw.write(f'{r}\n')
    
    
if __name__ == "__main__":
    with open(CONFIG, "r") as f:
       cfg = yaml.safe_load(f)

    main(cfg)