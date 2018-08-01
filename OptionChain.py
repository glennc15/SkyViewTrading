import datetime
import pandas as pd

# import py_vollib.black_scholes as vollib_bs
import py_vollib.black_scholes.greeks.analytical as vollib_greeks
import py_vollib.black.implied_volatility as vollib_iv 

class OptionChain(object):
	def __init__(self):
		self.underlying_symbol = None
		self.underlying_spot = None
		self.underlying_spot_change = None
		self.underlying_description = None
		self.timestamp = None
		self.underlying_bid = None
		self.underlying_ask = None
		self.underlying_volume = None
		self.risk_free_rate = None
		# each entry in option_chains has the following structure:
		# {expiration:
		#	 {
		# 		'calls': list of Option objects
		# 		'puts' : list of Option object
		# 	 } 
		# }
		#
		# expiration is a datetime object representing the option expiration date
		self.option_chains = {}

	def add_call_option(self, expiration, option_obj):
		if expiration in self.option_chains.keys():
			self.option_chains[expiration]['calls'].append(option_obj)
		else:
			self.option_chains[expiration] = {
				'calls': [option_obj],
				'puts': []
			}

	def add_put_option(self, expiration, option_obj):
		if expiration in self.option_chains.keys():
			self.option_chains[expiration]['puts'].append(option_obj)
		else:
			self.option_chains[expiration] = {
				'calls': [],
				'puts': [option_obj]
			}

	# def add_option_chains(self, expiration, calls, puts):
	# 	assert(isinstance(expiration, datetime.datetime))
	# 	assert(isinstance(calls, pd.DataFrame))
	# 	assert(isinstance(puts, pd.DataFrame))
		
	# 	new_chains = {'calls': calls, 'puts': puts}
	# 	self.option_chains[expiration] = new_chains

	# def remove_options_after(self, days=None, date=None):
	# 	if days:
	# 		cutoff_date = self.days_to_date(days)
	# 		self.remove_options_after(date=cutoff_date)
	# 	else:
	# 		cutoff_date = date

	# 		# in Python3 have to convert the keys to a list as .keys() returns an iterator.
	# 		for expiration in list(self.option_chains.keys()):
	# 			if expiration > cutoff_date:
	# 				del self.option_chains[expiration]

	# 	return self

	# def remove_options_before(self, days=None, date=None):
	# 	if days:
	# 		cutoff_date = self.days_to_date(days)
	# 		self.remove_options_before(date=cutoff_date)
	# 	else:
	# 		cutoff_date = date

	# 		# in Python3 have to convert the keys to a list as .keys() returns an iterator.
	# 		for expiration in list(self.option_chains.keys()):
	# 			if expiration < cutoff_date:
	# 				del self.option_chains[expiration]

	# 	return self

	# def set_exchange(self):
	# 	'''
	# 	2018-07-22: currently only keeps the exchanges that are set to None

	# 	'''
	# 	for k,v in self.option_chains.items():
	# 		self.option_chains[k]['calls'] = v['calls'][v['calls']['Exchange'].isnull()]
	# 		self.option_chains[k]['puts'] = v['puts'][v['puts']['Exchange'].isnull()]

	# 	return self

	def items(self):
		'''
	
		iterator for the option chains

		'''
		for key,values in self.option_chains.items():
			yield (key, values['calls'], values['puts'])

	def pp_expirations(self):
		'''
		
		Not even a pretty print. Utility I use in jupyter notebook to make
		expiration assignments so I can copy & paste for later use

		'''
		expirations = sorted(list(self.option_chains.keys()))
		for expiration in expirations:
			expiraiton_tuple = (expiration.year, expiration.month, expiration.day, expiration.hour, expiration.minute)
			print("expiration = datetime.datetime({}, {}, {}, {}, {})".format(*expiraiton_tuple))

	def add_greeks(self, risk_free_rate):
		self.risk_free_rate = risk_free_rate

		for k,v in self.option_chains.items():
			for call in v['calls']:
				call.sigma = self.iv(call, self.underlying_spot, self.timestamp, k, 'c')
				call.delta = self.delta(call, self.underlying_spot, self.timestamp, k, 'c')
				call.gamma = self.gamma(call, self.underlying_spot, self.timestamp, k, 'c')
				call.theta = self.theta(call, self.underlying_spot, self.timestamp, k, 'c')
				call.vega = self.vega(call, self.underlying_spot, self.timestamp, k, 'c')

		for k,v in self.option_chains.items():
			for put in v['puts']:
				put.sigma = self.iv(put, self.underlying_spot, self.timestamp, k, 'p')
				put.delta = self.delta(put, self.underlying_spot, self.timestamp, k, 'p')
				put.gamma = self.gamma(put, self.underlying_spot, self.timestamp, k, 'p')
				put.theta = self.theta(put, self.underlying_spot, self.timestamp, k, 'p')
				put.vega = self.vega(put, self.underlying_spot, self.timestamp, k, 'p')
			

		return self

	def iv(self, option_obj, asset_price, timestamp, expiration, call_put_flag):
		discounted_option_price = self.option_price(ask=option_obj.ask, bid=option_obj.bid)
		F = asset_price
		K = option_obj.strike
		r = self.risk_free_rate
		t = self.time_2_expiration(timestamp, expiration)  
		flag = call_put_flag 

		try:
		    iv = vollib_iv.implied_volatility(discounted_option_price, F, K, r, t, flag)
		except Exception as e:
		    print(e)
		    iv = 0

		return iv

	def delta(self, option_obj, asset_price, timestamp, expiration, call_put_flag):
		flag = call_put_flag 
		S = asset_price
		K = option_obj.strike 
		t = self.time_2_expiration(timestamp, expiration)  
		r = self.risk_free_rate  
		sigma = option_obj.sigma  

		delta = vollib_greeks.delta(flag, S, K, t, r, sigma)

		return delta

	def gamma(self, option_obj, asset_price, timestamp, expiration, call_put_flag):
		flag = call_put_flag 
		S = asset_price
		K = option_obj.strike 
		t = self.time_2_expiration(timestamp, expiration)  
		r = self.risk_free_rate  
		sigma = option_obj.sigma  

		gamma = vollib_greeks.gamma(flag, S, K, t, r, sigma)

		return gamma

	def theta(self, option_obj, asset_price, timestamp, expiration, call_put_flag):
		flag = call_put_flag 
		S = asset_price
		K = option_obj.strike 
		t = self.time_2_expiration(timestamp, expiration)  
		r = self.risk_free_rate  
		sigma = option_obj.sigma  

		theta = vollib_greeks.theta(flag, S, K, t, r, sigma)

		return theta

	def vega(self, option_obj, asset_price, timestamp, expiration, call_put_flag):
		flag = call_put_flag 
		S = asset_price
		K = option_obj.strike 
		t = self.time_2_expiration(timestamp, expiration)  
		r = self.risk_free_rate  
		sigma = option_obj.sigma  

		vega = vollib_greeks.vega(flag, S, K, t, r, sigma)

		return vega



	# --- Internal methods --- #
	def days_to_date(self, days):
		cutoff_date = self.timestamp + datetime.timedelta(days=days)
		return cutoff_date

	def option_price(self, bid, ask):
		if bid > 0 and ask > 0:
			option_price = (bid+ask) / 2.0
		else:
			if bid > 0:
				option_price = bid
			else:
				option_price = ask

		return option_price

	def time_2_expiration(self, current_date, expiration):
		one_year = datetime.timedelta(days=365)
		time_delta = expiration - current_date
		time_2_expiration = time_delta.total_seconds() / one_year.total_seconds()

		return time_2_expiration






