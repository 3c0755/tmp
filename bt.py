import tushare as ts
import pandas as pd
import numpy as np
import backtrader as bt
import datetime as dt
#from SimpleStrategy import *

import backtrader as bt

class SimpleStrategy(bt.Strategy):
    # 策略参数
    params = dict(
        period=20,  # 均线周期
        look_back_days=30,
        printlog=False
    )
    def __init__(self):
        self.mas = dict()
        #遍历所有股票,计算20日均线
        for data in self.datas:
            self.mas[data._name] = bt.ind.SMA(data.close, period=self.p.period) 
    def next(self):
        #计算截面收益率
        rate_list=[]
        for data in self.datas:
            if len(data)>self.p.look_back_days:
                p0=data.close[0]
                pn=data.close[-self.p.look_back_days]
                rate=(p0-pn)/pn
                rate_list.append([data._name,rate])
        #股票池   
        long_list=[]
        sorted_rate=sorted(rate_list,key=lambda x:x[1],reverse=True)
        long_list=[i[0] for i in sorted_rate[:10]]
        # 得到当前的账户价值
        total_value = self.broker.getvalue()
        p_value = total_value*0.9/10
        for data in self.datas:
            #获取仓位
            pos = self.getposition(data).size
            if not pos and data._name in long_list and \
              self.mas[data._name][0]>data.close[0]:
                size=int(p_value/100/data.close[0])*100
                self.buy(data = data, size = size) 
            if pos!=0 and data._name not in long_list or \
              self.mas[data._name][0]<data.close[0]:
                self.close(data = data)                        
    def log(self, txt, dt=None,doprint=False):
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()},{txt}')
    #记录交易执行情况（可省略，默认不输出结果）
    def notify_order(self, order):
        # 如果order为submitted/accepted,返回空
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 如果order为buy/sell executed,报告价格结果
        if order.status in [order.Completed]: 
            if order.isbuy():
                self.log(f'买入:\n价格:{order.executed.price:.2f},\
                成本:{order.executed.value:.2f},\
                手续费:{order.executed.comm:.2f}')
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(f'卖出:\n价格：{order.executed.price:.2f},\
                成本: {order.executed.value:.2f},\
                手续费{order.executed.comm:.2f}')
            self.bar_executed = len(self) 
        # 如果指令取消/交易失败, 报告结果
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('交易失败')
        self.order = None
    #记录交易收益情况（可省略，默认不输出结果）
    def notify_trade(self,trade):
        if not trade.isclosed:
            return
        self.log(f'策略收益：\n毛收益 {trade.pnl:.2f}, 净收益 {trade.pnlcomm:.2f}')

TOKEN = '76d0121aa860eb7945280ee984bdf91caa7293a58d90ce737c3c4e4a'
pro = ts.pro_api(token=TOKEN)

data = {
    'code':['600819.SH','000612.SZ','000998.SZ','002009.SZ','300159.SZ','300048.SZ','600150.SH','002041.SZ','601669.SH','002368.SZ'],
    'name':['耀皮玻璃','焦作万方','隆平高科','天奇股份','新研股份','合康新能','中国船舶','登海种业','中国电建','太极股份']
}
frame = pd.DataFrame(data)
stock=frame['code']
print(stock)

def fetch_daily_data(stock,start,end):
    data = pro.daily(ts_code=stock,start_date=start,end_date=end)
    data['trade_date'] = pd.to_datetime(data['trade_date'])
    data=data.sort_values(by = 'trade_date')
    data.index = data['trade_date']
    data = data[
        ['ts_code', 'open', 'high', 'low', 'close', 'pre_close', 'change', 'pct_chg', 'vol', 'amount']]
    return data
	
for i in range(len(stock)):
    data=fetch_daily_data(stock.iloc[i],'20200813', '20210813')#字段分别为股票代码、开始日期、结束日期
    data.to_csv(stock.iloc[i]+'.csv')

cerebro = bt.Cerebro()
for i in range(len(stock)):#循环获取10支股票历史数据
    data = bt.feeds.GenericCSVData(
            dataname=stock.iloc[i]+'.csv',
            fromdate=dt.datetime(2020, 8, 13),
            todate=dt.datetime(2021, 8, 13),
            dtformat='%Y-%m-%d',
            datetime=0,#定义trade_date在第0列
            open=2,
            high=3,
            low=4,
            close=5,
            volume=9,
            nullvalue=0.0,#设置空值
        )
    cerebro.adddata(data)
#回测设置
startcash=100000.0
cerebro.broker.setcash(startcash)
# 设置佣金为万分之二
cerebro.broker.setcommission(commission=0.0002)
 # 添加策略
cerebro.addstrategy(SimpleStrategy,printlog=True) 
cerebro.run() 
#获取回测结束后的总资金
portvalue = cerebro.broker.getvalue()
pnl = portvalue - startcash
#打印结果
print(f'总资金: {round(portvalue,2)}')
print(f'净收益: {round(pnl,2)}')
#绘图，暂时先不测试了
#cerebro.plot()
