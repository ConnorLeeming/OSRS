import json
import ast
import time
from plyer import notification


def get_arb_list():
    with open('../txt/arbs_list.txt','r') as f:
       return ast.literal_eval(f.read())

def get_cache():
    with open('../txt/cache.txt','r') as f:
        return json.loads(f.read())

def get_item(name):
    if isinstance(name,int):
        return name
    else:
        return cache[name]

class arb_obj():
    def __init__(self,name,buys,sells):
        self.name = name
        self.buy_names = buys
        self.sell_names = sells
        self.buy_items = [get_item(b) for b in self.buy_names]
        self.sell_items = [get_item(s) for s in self.sell_names]
        self.profit = 0
        self.pushed = 10
    def update(self):
        self.buy_items = [get_item(b) for b in self.buy_names]
        self.sell_items = [get_item(s) for s in self.sell_names]

    def calc_profit(self):
        buy_prices = []
        sell_prices = []

        for b in self.buy_items:
            if isinstance(b,int):
                buy_prices.append(b)
            elif b['name'] == 'Kraken tentacle':
                buy_prices.append(b['ask']* 10)
            else:
                buy_prices.append(b['ask'])
        buy = sum(buy_prices)

        for s in self.sell_items:
            if s['name'] == "Zulrah's scales":
                sell_prices.append(s['bid'] * 20000)
            else:
                sell_prices.append(s['bid'])
        sell = sum(sell_prices)

        tax = sell * 0.01

        self.profit = sell - tax - buy

def make_arb_objects():
    arb_objects = []
    for arb in arb_list:
        name = arb[0]
        buys = arb[1]
        sells = arb[2]
        rev = arb[3]
        arb_objects.append(arb_obj(name,buys,sells))
        if rev == True:
            arb_objects.append(arb_obj(name,sells,buys))
    return arb_objects

def push():
    active = []

    threshold = 200000
    now = int(time.time())

    for arb in arb_objects:
        if arb.profit > threshold and (now - arb.pushed) > 300 and arb.name != 'Ancient wyvern':
            active.append(arb)
            arb.pushed = now
    
    message = ''
    for a in active:
        profit = str(int(a.profit))
        message = message + (a.name + ': ' + f"{int(profit):,}" + '\n')
    if len(active) > 0:
        notification.notify(title = 'Runescape',message = message,timeout = 10)

def push_onyx():
    global last_onyx
    
    now = int(time.time())    
    active = []
    items = ['Amulet of fury','Berserker necklace','Regen bracelet','Ring of stone']
    for i in items:
        data = get_item(i)
        spread = data['spread']
        if spread > 50000:
            active.append(i)
    
    message = ''
    for a in active:
        message = message + a + ': ' + str(cache[a]['spread']) + '\n'
    if last_onyx > 30 and len(active) > 1:
        notification.notify(title = 'Runescape',message=message,timeout = 15)
        last_onyx = now



cache = get_cache()
arb_list = get_arb_list()
arb_objects = make_arb_objects()
last_onyx = 30

while True:
    cache = get_cache()
    for arb in arb_objects:
        arb.update()
        arb.calc_profit()
    push()
    time.sleep(10)
    push_onyx()
    time.sleep(10)