import pandas as pd
import numpy as np
import sqlalchemy as sql
import datetime as dt
import requests
import time
import json
import sqlite3



def refresh():
    path1 = r"#####################"
    table1 = '#######'


    def update_db(path,table):
        headers = {'User-Agent': '##########'}
        def get_tm1():
            now = int(time.time())
            day = 86400
            over = now % day
            t0 = now - over
            tm1 = t0 - day
            return tm1

        def get_map():
            url = 'https://prices.runescape.wiki/api/v1/osrs/mapping'
            req = requests.get(url,headers=headers)
            text = req.text
            raw = json.loads(text)
            map = {}
            for i in raw:
                id = i['id']
                map[id] = i
            return map

        def get_24hr(timestamp):
            url = 'https://prices.runescape.wiki/api/v1/osrs/24h?timestamp='+str(timestamp)
            req = requests.get(url,headers=headers)
            text = req.text
            raw = json.loads(text)
            return raw['data']

        def get_neeeded():

            def get_done():
                '''
                pulls list of done timestamps from timestamps.txt
                returns list asc order
                '''
                done = []
                with open('timestamps.txt','r') as f:
                    lines = f.readlines()
                    for line in lines:
                        done.append(int(line.rstrip()))
                return done
            done = get_done()
            def stamp_gen():
                day = 86400
                now = int(time.time())
                t0 = now - (now % day)

                pos = t0
                while True:
                    pos = pos - day
                    yield pos
            aaa = stamp_gen()

            needed = []
            for i in range(300):
                x = next(aaa)
                if x not in done:
                    needed.append(x)
                else:
                    return needed
            return needed

        def add_stamp(stamp):
            with open('timestamps.txt','a') as f:
                f.write(str(stamp)+'\n')

        def update():

            n = get_neeeded()
            map = get_map()

            #for each missing timestamp:
            for i in range(len(n)):
                print('needed:',len(n))
                stamp = n.pop()
                time.sleep(4)
                data = get_24hr(stamp)
                print('getting',stamp)       
                records = []
                
                #for each item in the timestamp:
                for j in data.items():
                    id = int(j[0])
                    d = j[1]
                    try:
                        name = map[id]['name']
                    except KeyError:
                        continue
                    records.append(
                        [
                            int(str(id)+str(stamp)),
                            stamp,
                            id,
                            name,
                            d['avgHighPrice'],
                            d['avgLowPrice'],
                            d['highPriceVolume'],
                            d['lowPriceVolume']
                        ]
                    )
                        
                    '''
                    'key':int(str(i)+str(id))
                    'timestamp':i
                    'id':id
                    'name':map[id]['name']
                    'high':d['avgHighPrice']
                    'low':d['avgLowPrice']
                    'hvol':d['highPriceVolume']
                    'lvol':d['lowPriceVolume']
                    '''
                #push that timestamp to db

                #connect db
                con = sqlite3.connect(path1)
                cur = con.cursor()
                sqlstring = 'INSERT INTO '+table1+''' (key,timestamp,id,name,high,low,hvol,lvol)
                                VALUES(?,?,?,?,?,?,?,?)'''
                #push to db
                for r in records:
                    cur.execute(sqlstring,r)
                    

                #commit / close
                con.commit()
                print('commit',stamp)
                con.close()


                #add to timestamps txt
                add_stamp(stamp)
                
        update()

    def load(path,table):
        '''
        path = path to sqlite3 db
        table = table name
        '''

        db_name = path
        table_name = table

        engine = sql.create_engine("sqlite:///%s" % db_name, execution_options={"sqlite_raw_colnames": True})
        df = pd.read_sql_table(table_name, engine)
        return df
    
    def arrange(df):
        '''
        df = dataframe passed from load
        outputs to pickle
        '''
                
        #create / drop columns
        df['p'] = (df['high']+df['low']) / 2
        df['vol'] = (df['hvol']+df['lvol']) / 2
        df.drop(['id','high','low','hvol','lvol','key'],axis=1,inplace=True)

        #save vols for later
        vols = df.groupby('name').median().vol
        avg = df.groupby('name').median().p

        #re-index to datetime
        df['timestamp'] = df['timestamp'].apply(
        lambda x: dt.datetime.fromtimestamp(x))
        df.set_index(df.timestamp,inplace=True)

        #drop timestamp and vol
        df.drop(['timestamp','vol'],axis=1,inplace=True)

        #convert to time-series
        dd = {i:df[df.name == i].p.to_dict() for i in list(df.name.unique())}
        df = pd.DataFrame(dd)

        #remove outliers
        q1 = df.quantile(0.25)
        q3 = df.quantile(0.75)
        iqr = q3 - q1
        outliers = ((df < (q1 - (iqr*1.5 )))|( df > (q3 + (iqr*1.5))))
        df[outliers == True] = np.nan

        #interpolate
        df.ffill(inplace=True)
        df.backfill(inplace=True)

        #drop any items which are all NA
        missing = list(df.isnull().sum()[(df.isnull().sum() > 0)].index)
        df.drop(missing,axis=1,inplace=True)
        vols.drop(missing,inplace=True)
        avg.drop(missing,inplace=True)

        #make stats frame:
        stds = df.pct_change().std()
        retframe = (df.pct_change()+1).cumprod()
        rets = retframe.iloc[-1]
        stats = pd.concat([vols,stds,rets,avg],axis=1)
        stats.columns = ['vol','std','return','avgp']
        stats['sharpe'] = stats['return'] / stats['std']

        #save data to disk
        stats.to_pickle('stats.txt')
        df.to_pickle('tseries.txt')
    
    #run: pull from db, arrange then pickle into 'stats' and 'tseries'
    update_db(path1,table1)
    print('database up to date, arranging data')
    arrange(load(path1,table1))