import datetime
import pandas_datareader.data as web
import pandas as pd
import numpy as np

class POP(object):
	def __init__(self):
		self.symbol = None
		self.ohlc_data = None
		self.days_til_expiration = None
		self.spots = None
		
	def get_ohlc_data(self, symbol):
		self.symbol = symbol
		ohlc_end_date = datetime.datetime.today()
		ohlc_start_date = ohlc_end_date - datetime.timedelta(days=(2*365))
		self.ohlc_data = web.DataReader(name=self.symbol, data_source='yahoo', start=ohlc_start_date, end=ohlc_end_date)
		
		return self
	
	def set_days_til_expiration(self, expiration, start_date=None):
		if start_date:
			current_date = start_date
		else:
			current_date = datetime.datetime.today()

		days_til_expiration = 0            
		one_day = datetime.timedelta(days=1)
		while current_date < expiration:
			if current_date.isoweekday() < 6:
				days_til_expiration += 1
			current_date += one_day
			
		self.days_til_expiration = days_til_expiration
		
		self.set_return_spots(days_til_expiration)
		
		return self
		
	def set_return_spots(self, days_til_expiration):
		# calculate the new projected spots using past returns
		# returns
		spots = (self.ohlc_data['Adj Close'] / self.ohlc_data['Adj Close'].shift(days_til_expiration)) * self.ohlc_data['Adj Close'][-1]
		# some clean up
		spots = spots[-252:]
		
		self.spots = spots
		
	def pop(self, spot):
		return self.spots.gt(spot).sum() / self.spots.size