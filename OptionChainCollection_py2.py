import pandas as pd

import datetime

import pdb 

"""

Stores an option chain and has methods for interacting with the option chain
such as in iterator to retrieve data and  modify data.

"""
class OptionChain(object):
	def __init__(self):
		self.data_filename = None
		self.underlying_symbol = None
		self.underlying_description = None
		self.underlying_spot = None
		self.underlying_spot_change = None
		# 2nd line of data file underlying data
		self.timestamp = None
		self.underlying_bid = None
		self.underlying_ask = None
		self.underlying_size = None
		self.underlying_volume = None

		self.option_chains = {} 

		self.has_am_settlement = None 
		self.am_settlement_symbol = None

		self.expirations = None

		self.total_chains = 0

	def set_option_chains(self, option_chains_df):
		# option_chains_df is the raw data frame contining all option chains
		# from the CBOE data file. Most chains are not needed and can be
		# removed. The option chains are stored in a dictionary with the keys
		# as expiration dates and the values the option chains for that
		# expiration.

		# self.option_chains = {
		# 	'[Expiraiton:] 2017-12-18 15:00': [option chain dataframe with expiration of 2017-12-18 15:00],
		#   '[Expiraiton:] 2018-01-28 15:00': [option chain dataframe with expiration of 2018-01-28 15:00],
		#                                       :
		#                                       :
		#                                       :
		#   '[Expiraiton:] 2020-02-20 15:00': [option chain dataframe with expiration of 2020-02-20 15:00],
		# }

		# 1st a little clean up on the column names and keeping only options
		# with no exchange. (may change this later if specific exchange data
		# is needed)
		
		option_chains_df.columns = [i.lower() for i in option_chains_df.columns]
		option_chains_df = option_chains_df[option_chains_df.exchange == '']

		# clean up the descriptions
		option_chains_df.call_desc = option_chains_df.call_desc.apply(lambda x: x.split('(')[1][:-1] if isinstance(x, str) else None)
		option_chains_df.put_desc = option_chains_df.put_desc.apply(lambda x: x.split('(')[1][:-1] if isinstance(x, str) else None)

		# option_chains_df.put_desc = option_chains_df.put_desc.apply(lambda x: x.split('(')[1][:-1])

		self.expirations = set(option_chains_df.expiration)

		for expiration in self.expirations:
			these_chains = option_chains_df[option_chains_df.expiration == expiration]
			these_chains = these_chains.reset_index(drop=True)

			self.option_chains[expiration] = these_chains
			self.total_chains += len(these_chains)

	def option_chain_iter(self, expiration_before_days=None, expiration_after_days=None):

		"""
        
        how to use expiration_before_days and expiraiton_after_days:
        expiration_before_days > expiration_after days
        timestamp           timestamp+expiraiton_after_days       		timestamp+expiration_before_days
        |___________________|+++++++++++++++++++++++++++++++++++++++++++|_________________________________
							  (options returned in this time region)

        """

		after_cutoff_date = self.set_after_cutoff_date(expiration_after_days)
		before_cutoff_date = self.set_before_cutoff_date(expiration_before_days)

		for expiration in self.expirations:
			if (expiration >= after_cutoff_date) and (expiration <= before_cutoff_date):
				yield (expiration, self.option_chains[expiration])


	# def drop_chains_between_dates(self, before_drop_date=None, after_drop_date=None):
	# 	# swap dates if needed
	# 	if before_drop_date > after_drop_date:
	# 		temp_date = after_drop_date
	# 		after_drop_date = before_drop_date
	# 		before_drop_date = temp_date

	# 	self.drop_chains_before_date(before_drop_date)
	# 	self.drop_chains_after_date(after_drop_date)

	# def drop_chains_expire_after_n_days(self, number_of_days):
	def set_after_cutoff_date(self, number_of_days):

		if number_of_days:
			days_to_add = datetime.timedelta(days = number_of_days)
			after_cutoff_date = self.timestamp + days_to_add
			# self.options_after_date = cutoff_date
			# self.drop_chains_before_date(cutoff_date)
		else:
			# no after days are specified so set the cutoff date to 1 day
			# before the file timestamp
			days_to_add = datetime.timedelta(days = 1)
			after_cutoff_date = self.timestamp - days_to_add

		return after_cutoff_date

	# def drop_chains_expire_before_n_days(self, number_of_days):
	def set_before_cutoff_date(self, number_of_days):
		if number_of_days:
			days_to_add = datetime.timedelta(days = number_of_days)
			before_cutoff_date = self.timestamp + days_to_add
			# self.options_before_date = cutoff_date
			# self.drop_chains_after_date(cutoff_date)
		else:
			# set the cutoff date to something far in the future so it has not affect
			days_to_add = datetime.timedelta(days = (365*10))
			before_cutoff_date = self.timestamp + days_to_add

		return before_cutoff_date

	# def drop_chains_before_date(self, before_drop_date):
	# 	if before_drop_date:
	# 		expirations_to_remove = []

	# 		for expiration in self.expirations:
	# 			if expiration < before_drop_date:
	# 				expirations_to_remove.append(expiration)

	# 		self.remove_expirations(expirations_to_remove)


	# def drop_chains_after_date(self, after_drop_date):
	# 	if after_drop_date:
	# 		expirations_to_remove = []

	# 		for expiration in self.expirations:
	# 			if expiration > after_drop_date:
	# 				expirations_to_remove.append(expiration)

	# 		self.remove_expirations(expirations_to_remove)

	# def remove_expirations(self, expirations_remove_list):
	# 	for expiration in expirations_remove_list:
	# 		chain_length = len(self.option_chains[expiration])

	# 		if self.option_chains.pop(expiration, None) is not None:
	# 			self.total_chains -= chain_length

	# 	valid_expirations = [expiration for expiration in self.expirations if expiration not in expirations_remove_list]
	# 	self.expirations = set(valid_expirations)

	def drop_columns(self, drop_columns_list):
		for expiration, option_chain in self.option_chain_iter():
			self.option_chains[expiration] = option_chain.drop(drop_columns_list, axis=1)



class VerticalSpreads(object):
	def __init__(self):
		self.vertical_spreads = {}
		self.expirations = set()
		self.total_verticals = 0

	def build_empty_collection(self, expirations_list):
		spread_types = ['bull_calls', 'bull_puts', 'bear_calls', 'bear_puts']

		# removes any possible duplicate dates 
		self.expirations = list(set(expirations_list))

		for expiration in self.expirations:
			spreads_dict = {}
			
			for spread_type in spread_types:
				spreads_dict[spread_type] = None
			
			self.vertical_spreads[expiration] = spreads_dict


		return self

	def add_vertical_spreads(self, expiration, spread_type, vertical_spreads):
		if expiration in self.expirations:
			self.vertical_spreads[expiration][spread_type] = vertical_spreads
			# self.total_verticals += len(vertical_spreads)
		else:
			self.vertical_spreads[expiration] = {spread_type: vertical_spreads}
			self.expirations = set(self.vertical_spreads.keys())
			# self.total_verticals += len(vertical_spreads)

		if vertical_spreads is not None:
			self.total_verticals += len(vertical_spreads)

	def vertical_expirations_iter(self):
		for expiration in self.expirations:
			yield (expiration, self.vertical_spreads[expiration])

	def vertical_spreads_iter(self):
		for expiration in self.expirations:
			for spread_type in self.vertical_spreads[expiration].keys():
				yield (expiration, spread_type, self.vertical_spreads[expiration][spread_type])


	def replace_spreads(self, expiration, spread_type, new_spreads):
		if (expiration in self.vertical_spreads.keys()) and (spread_type in self.vertical_spreads[expiration].keys()):
			
			if self.vertical_spreads[expiration][spread_type] is not None:
				self.total_verticals -= len(self.vertical_spreads[expiration][spread_type])
			
			self.vertical_spreads[expiration][spread_type] = new_spreads
			
			if new_spreads is not None:
				self.total_verticals += len(new_spreads)

	def get_spreads(self, expiraiton, spread_type):
		try:
			results = self.vertical_spreads[expiraiton][spread_type]
		except Exception as e:
			# raise e
			results = None 

		return results

	def merge_spreads(self, expiration, spread_type, spreads1, spreads2):
		# pdb.set_trace()

		if spreads1 is None:
			self.replace_spreads(expiration, spread_type, spreads2)

		elif spreads2 is None:
			self.replace_spreads(expiration, spread_type, spreads1)

		else:
			# pdb.set_trace()
			joined_spreads = pd.concat([spreads1, spreads2]).reset_index().drop('index', axis=1)
			self.replace_spreads(expiration, spread_type, joined_spreads)
			# pdb.set_trace()












