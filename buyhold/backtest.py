import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlalchemy as sql
import datetime as dt

def backtest(ts,st,pf,start,end,mv,mp):
    ts = pd.read_pickle(ts)
    st = pd.read_pickle(st)
    
    #subset ts,st by market params and time
    market_names = list(st[(st.vol>=mv) & (st.avgp >= mp)].index)
    market_ts = ts[market_names].iloc[start:end]
    market_st = st.loc[market_names]
    
    #subset ts,st by portfolio and time
    pf_ts = ts[pf].iloc[start:end]
    pf_st = st.loc[pf]
    
    #push market line, market stats
    a = (market_ts.pct_change()+1)
    a[a>3]=1
    market_line = a.mean(axis=1).cumprod()
    plt.plot(market_line)
    
    #push pf line, pf stats
    port_line = (pf_ts.pct_change()+1).mean(axis=1).cumprod()
    plt.plot(port_line)
    
    #print stats
    pf_rtn = round((port_line[-1]-1)*100,2)
    print('Portfolio return:',str(pf_rtn)+' %')
    print('Portfolio Std.Dev.:',round(port_line.std(),2))
    
    print('')
    
    mkt_rtn = round((market_line[-1]-1)*100,2)
    print('Market return: '+str(mkt_rtn)+' %')
    print('Market Std.Dev.:',round(market_line.std(),2))