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
		# 		'calls': pandas dataframe of call option chains
		# 		'puts' : pandas dataframe of put option chains
		# 	 } 
		# }
		#
		# expiration is a datetime object representing the option expiration date
		self.option_chains = {}

	def add_option_chains(self, expiration, calls, puts):
		assert(isinstance(expiration, datetime.datetime))
		assert(isinstance(calls, pd.DataFrame))
		assert(isinstance(puts, pd.DataFrame))
		
		new_chains = {'calls': calls, 'puts': puts}
		self.option_chains[expiration] = new_chains

	def remove_options_after(self, days=None, date=None):
		if days:
			cutoff_date = self.days_to_date(days)
			self.remove_options_after(date=cutoff_date)
		else:
			cutoff_date = date

			# in Python3 have to convert the keys to a list as .keys() returns an iterator.
			for expiration in list(self.option_chains.keys()):
				if expiration > cutoff_date:
					del self.option_chains[expiration]

		return self

	def remove_options_before(self, days=None, date=None):
		if days:
			cutoff_date = self.days_to_date(days)
			self.remove_options_before(date=cutoff_date)
		else:
			cutoff_date = date

			# in Python3 have to convert the keys to a list as .keys() returns an iterator.
			for expiration in list(self.option_chains.keys()):
				if expiration < cutoff_date:
					del self.option_chains[expiration]

		return self

	def set_exchange(self):
		'''
		2018-07-22: currently only keeps the exchanges that are set to None

		'''
		for k,v in self.option_chains.items():
			self.option_chains[k]['calls'] = v['calls'][v['calls']['Exchange'].isnull()]
			self.option_chains[k]['puts'] = v['puts'][v['puts']['Exchange'].isnull()]

		return self

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
			v['calls']['Sigma'] = v['calls'].apply(lambda x: self.iv(x, self.underlying_spot, self.timestamp, k, 'c'), axis=1)
			v['calls']['Delta'] = v['calls'].apply(lambda x: self.delta(x, self.underlying_spot, self.timestamp, k, 'c'), axis=1)
			v['calls']['Gamma'] = v['calls'].apply(lambda x: self.gamma(x, self.underlying_spot, self.timestamp, k, 'c'), axis=1)
			v['calls']['Theta'] = v['calls'].apply(lambda x: self.theta(x, self.underlying_spot, self.timestamp, k, 'c'), axis=1)
			v['calls']['Vega'] = v['calls'].apply(lambda x: self.vega(x, self.underlying_spot, self.timestamp, k, 'c'), axis=1)

			v['puts']['Sigma'] = v['puts'].apply(lambda x: self.iv(x, self.underlying_spot, self.timestamp, k, 'p'), axis=1)
			v['puts']['Delta'] = v['puts'].apply(lambda x: self.delta(x, self.underlying_spot, self.timestamp, k, 'p'), axis=1)
			v['puts']['Gamma'] = v['puts'].apply(lambda x: self.gamma(x, self.underlying_spot, self.timestamp, k, 'p'), axis=1)
			v['puts']['Theta'] = v['puts'].apply(lambda x: self.theta(x, self.underlying_spot, self.timestamp, k, 'p'), axis=1)
			v['puts']['Vega'] = v['puts'].apply(lambda x: self.vega(x, self.underlying_spot, self.timestamp, k, 'p'), axis=1)

		return self

	def iv(self, option_chain_data, asset_price, timestamp, expiration, call_put_flag):
		discounted_option_price = self.option_price(ask=option_chain_data['Ask'], bid=option_chain_data["Bid"])
		F = asset_price
		K = option_chain_data["Strike"]
		r = self.risk_free_rate
		t = self.time_2_expiration(timestamp, expiration)  
		flag = call_put_flag 

		try:
		    iv = vollib_iv.implied_volatility(discounted_option_price, F, K, r, t, flag)
		except Exception as e:
		    print(e)
		    iv = 0

		return iv

	def delta(self, option_chain_data, asset_price, timestamp, expiration, call_put_flag):
		flag = call_put_flag 
		S = asset_price
		K = option_chain_data["Strike"]  
		t = self.time_2_expiration(timestamp, expiration)  
		r = self.risk_free_rate  
		sigma = option_chain_data["Sigma"]  

		delta = vollib_greeks.delta(flag, S, K, t, r, sigma)

		return delta

	def gamma(self, option_chain_data, asset_price, timestamp, expiration, call_put_flag):
		flag = call_put_flag 
		S = asset_price
		K = option_chain_data["Strike"]  
		t = self.time_2_expiration(timestamp, expiration)  
		r = self.risk_free_rate  
		sigma = option_chain_data["Sigma"]  

		gamma = vollib_greeks.gamma(flag, S, K, t, r, sigma)

		return gamma

	def theta(self, option_chain_data, asset_price, timestamp, expiration, call_put_flag):
		flag = call_put_flag 
		S = asset_price
		K = option_chain_data["Strike"]  
		t = self.time_2_expiration(timestamp, expiration)  
		r = self.risk_free_rate  
		sigma = option_chain_data["Sigma"]  

		theta = vollib_greeks.theta(flag, S, K, t, r, sigma)

		return theta

	def vega(self, option_chain_data, asset_price, timestamp, expiration, call_put_flag):
		flag = call_put_flag 
		S = asset_price
		K = option_chain_data["Strike"]  
		t = self.time_2_expiration(timestamp, expiration)  
		r = self.risk_free_rate  
		sigma = option_chain_data["Sigma"]  

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






