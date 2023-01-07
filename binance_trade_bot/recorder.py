import pandas as pd


class TradeRecorder():
    def __init__(self):
        self.df = pd.DataFrame()
    
    def record(self, event):
        self.df = self.df.append(event, ignore_index=True)
        print(self.df)
        
    def save(self, save_dir):
        self.df.to_csv(save_dir)