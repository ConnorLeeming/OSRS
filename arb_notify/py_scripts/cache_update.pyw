import time
import requests
import json
import ast

def get_tracking_list():
    to_track = []
    also = ['Onyx','Amulet of fury','Berserker necklace','Ring of stone','Regen bracelet']
    with open('../txt/arbs_list.txt','r') as f:
        arb_list = ast.literal_eval(f.read())
    for a in arb_list:
        for b in a[1]:
            if b not in to_track:
                to_track.append(b)
        for s in a[2]:
            if s not in to_track:
                to_track.append(s)
    for i in also:
        to_track.append(i)
    return to_track
to_track = get_tracking_list()

#api callers
headers = {'User-Agent': '#######'}
def get_latest():
    url = 'https://prices.runescape.wiki/api/v1/osrs/latest'
    req = requests.get(url,headers=headers)
    text = req.text
    raw = json.loads(text)
    return raw['data']
def get_5m():
    url = 'https://prices.runescape.wiki/api/v1/osrs/5m'
    req = requests.get(url,headers=headers)
    text = req.text
    raw = json.loads(text)
    return raw['data']
def get_1hr():
    url = 'https://prices.runescape.wiki/api/v1/osrs/1h'
    req = requests.get(url,headers=headers)
    text = req.text
    raw = json.loads(text)
    return raw['data']
def get_24hr():
    url = 'https://prices.runescape.wiki/api/v1/osrs/24h'
    req = requests.get(url,headers=headers)
    text = req.text
    raw = json.loads(text)
    return raw['data']
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


#cache maker
def time_convert(ts):
    now = int(time.time())
    passed = now - ts
    return round(passed / 60,1)
def build(map,latest,_5m,_1hr,_24hr,to_track):
    items_to_cache = {}
    
    for i in latest.items():
        
        try:
            id = int(i[0])
            name = map[id]['name']
        except KeyError:
            continue
        
        if name in to_track:
        
            try:
                alch = map[id]['highalch']
            except KeyError:
                alch = 0
            try:
                limit = map[id]['limit']
            except KeyError:
                limit = 0
            k = i[1]
            high,low,high_time,low_time = k['high'],k['low'],k['highTime'],k['lowTime']

            try:
                j5m = _5m[str(id)]
                h5m = j5m['highPriceVolume']
                l5m = j5m['lowPriceVolume']
                t5m = h5m + l5m
                r5m = h5m / t5m
            except (KeyError,ZeroDivisionError):
                t5m = 0
                r5m = 0
            try:
                j1hr = _1hr[str(id)]
                h1hr = j1hr['highPriceVolume']
                l1hr = j1hr['lowPriceVolume']
                t1hr = h1hr + l1hr
                r1hr = h1hr / t1hr
            except (KeyError,ZeroDivisionError):
                t1hr = 0
                r1hr = 0
            try:
                j24hr = _24hr[str(id)]
                h24hr = j24hr['highPriceVolume']
                l24hr = j24hr['lowPriceVolume']
                t24hr = h24hr + l24hr
                r24hr = h24hr / t24hr
            except (KeyError,ZeroDivisionError):
                t24hr = 0
                r24hr = 0
            try:
                _avg24 = j24hr['avgHighPrice']
            except KeyError:
                _avg24 = 0

            
            items_to_cache[name] = {
                'name':name,
                'id':id,
                'alch':alch,
                'limit':limit,
                'bid':low,
                'ask':high,
                'spread':high - low,
                'ask_time':time_convert(high_time),
                'bid_time':time_convert(low_time),
                'vol_5m':t5m,
                'vratio_5m':round(r5m,2),
                'vol_1hr':t1hr,
                'vratio_1hr':round(r1hr,2),
                'vol_24hr':t24hr,
                'vratio_24hr':round(r24hr,2),
                'avg_ask_24':_avg24
            }
        else:
            continue
    return items_to_cache   
def dump(new_build):
    path = '../txt/cache.txt'
    f = open(path,'w')
    f.write(json.dumps(new_build))
    f.close()
    print('dumped')
#------------------------------------------------------------------------

#get t0 first thing
t0 = int(time.time())

#initial cache build on start
map,latest,_5m,_1hr,_24hr = get_map(),get_latest(),get_5m(),get_1hr(),get_24hr()
dump(build(map,latest,_5m,_1hr,_24hr,to_track))

#main loop -------------------------------------------------------------

while True:
    updated = False
    
    #update endpoint if needed
    now = int(time.time())
    clock = now - t0
    if clock != 0 and clock % 15 == 0:
        latest = get_latest()
        updated = True
        print('updated /latest')
    if clock != 0 and (now % 300) == 15:
        print('/n')
        _5m = get_5m()
        updated = True
        print('updated /5m','\n')
    if clock != 0 and (now % 3600) == 30:
        print('\n')
        _1hr = get_1hr()
        updated = True
        print('updated /1hr','\n')
    if clock != 0 and (now % 86400) == 300:
        print('\n')
        _24hr = get_24hr()
        updated = True
        print('updated /24hr','\n')
    
    #sleep 1 to stop spamming
    time.sleep(1)
    
    #re-build and export cache if update has happened
    if updated == True:
        new_build = build(map,latest,_5m,_1hr,_24hr,to_track)
        dump(new_build)