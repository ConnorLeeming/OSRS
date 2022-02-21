import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlalchemy as sql
import datetime as dt


def gen_portfolio(tseries,stats,n,start,end,vmin=100,vmax=10**10,pmin=100,pmax=10**10,nsharpe=50,minret=1.1):

    '''
    get the best portfolio of *n* items over *start* to *end* date, with optional filters for volume and price.
    (one with high return, low volatility, low correltaion)
    
    
    tseries = path to timeframe file
    stats = path to stats file
    start = index of first timestamp
    end = index of last timestamp
    vmin = minimun daily volume
    vmin = maximum daily volume
    pmin = minimum price
    pmax = maximum price
    n = number of items in portfolio
    nsharpe = nlargest of sharpe ratio
    minret = minimum return
    '''
    
    #def get dataset
    def get_data():
        #read data from pickle
        df = pd.read_pickle(tseries)
        st = pd.read_pickle(stats)
        df.drop('Old school bond',axis=1,inplace=True)
        st.drop('Old school bond',inplace=True)
        return (df,st)
    
    
    #subset by interval,vol,price and sharpe
    def subset(df,st):
        #by parameters
        filters = list(st[(st.vol >= vmin) & (st.vol <= vmax) & (st.avgp >= pmin) & (st.avgp <= pmax) & (st['return']<= 2) & (st['return']>= 1.2)].index)
        df = df.filter(filters).iloc[start:end]
        st = st.loc[filters]
        
        #by sharpe
        high_sharpe = st.sharpe.nlargest(nsharpe).index
        df,st = df[high_sharpe],st.loc[high_sharpe]
        
        #by return
        high_return = st[st['return']>=minret].index
        df,st = df[high_return],st.loc[high_return]
        return (df,st)
        
    #generate portfolio
    def gen_portfolio(df,st):
        a = df.corr().sum(axis=1).nsmallest(n=1).index[0]
        selection = [a]
        for i in range(n-1):
            frame = df.corr()[selection].drop(selection)
            add = frame.sum(axis=1).nsmallest(n=1).index[0]
            selection.append(add)
        return selection

    df,st = get_data()
    df,st = subset(df,st)
    selection = gen_portfolio(df,st)
    return selection