import pandas as pd
import numpy as np

def calcSharpe(ret):
    m = (ret.mean() + 1)**12 - 1
    s = ret.std() * np.sqrt(12)
    return m/s



def calc_mw_sharpe(data, window):
    data = data.dropna()
    mwsharpes = pd.DataFrame(index=data.iloc[window:].index, columns=data.columns)
    for i in range(0, len(data) - window):
        tempData = data.iloc[i:i+window]
        for col in data.columns.to_list():
            mwsharpes.iloc[i][col] = calcSharpe(tempData[col])


    return mwsharpes











