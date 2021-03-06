import datetime
import pandas as pd
import numpy as np
import re

import Option
import OptionChain

class CBOEFileParser(object):
	def __init__(self,
					remove_options_after_days=60,
					remove_options_before_days=30,
					set_exchange=None):
		self.remove_options_after_days = remove_options_after_days
		self.remove_options_before_days = remove_options_before_days
		self.set_exchange = set_exchange

		self.option_chain_obj = OptionChain.OptionChain()
			
	def parse_cboe_file(self, cboe_file):

		self.parse_header(cboe_file)
		calls, puts = self.parse_option_chains(cboe_file)
		self.add_options(calls, puts)
		
		return self.option_chain_obj


	# *** Internal methods ***
	def add_options(self, calls_list, puts_list):
		min_date = self.option_chain_obj.timestamp + datetime.timedelta(days=self.remove_options_before_days)
		max_date = self.option_chain_obj.timestamp + datetime.timedelta(days=self.remove_options_after_days)

		for call in calls_list:
			if (call.expiration<max_date) & (call.expiration>min_date) & (call.exchange==self.set_exchange):
				self.option_chain_obj.add_call_option(call.expiration, call)

		for put in puts_list:
			if (put.expiration<max_date) & (put.expiration>min_date) & (put.exchange==self.set_exchange):
				self.option_chain_obj.add_put_option(put.expiration, put)



	def parse_header(self, cboe_file):
		quote_data_file = open(cboe_file)

		# read the first 2 lines of the CBOE file
		quote_data_head = []
		quote_data_head.append(quote_data_file.readline())
		quote_data_head.append(quote_data_file.readline())
		
		# ETF CBOE header example:
		# SPY (SPDR S&P 500 ETF TRUST),278.81,+0.91,
		# Jul 10 2018 @ 16:15 ET,Bid,278.81,Ask,278.82,Size,23x537,Vol,46778342,

		# ETF CBOE header with a ',' in the description string:
		# QQQ (INVESCO QQQ TRUST, SERIES 1),172.08,+0.89,
		# Jun 29 2018 @ 09:45 ET,Bid,172.11,Ask,172.12,Size,15x8,Vol,911904,

		# Index CBOE header example:
		# SPX (S&P 500 INDEX),2728.32,+12.01,
		# Jun 29 2018 @ 09:45 ET,

		first_line = quote_data_head[0].split(',')
		# remove the '\n' character
		if first_line[-1] == '\n':
			first_line = first_line[0:-1]

		# symbol is the first item in the first line:
		self.option_chain_obj.underlying_symbol = quote_data_head[0].split()[0]

		# the spot and spot change are always the second to last and last items:
		self.option_chain_obj.underlying_spot = float(first_line[-2])
		self.option_chain_obj.underlying_spot_change = float(first_line[-1])

		# description: between '()'
		description_re = re.compile(r'\(.*\)')
		self.option_chain_obj.underlying_description = description_re.findall(quote_data_head[0])[0][1:-1]

		# Parse the 2nd line of the header file.  For an index option the second
		# line only contains the time stamp. For ETFs and stock datafiles the
		# second line contains: time stamp, bid, ask, volume

		second_line = quote_data_head[1].split(',')

		# parse the time stamp
		self.option_chain_obj.timestamp = datetime.datetime.strptime(second_line[0], '%b %d %Y @ %H:%M ET')

		# parse the bid, ask, volume if this is an ETF or stock:
		if len(second_line) > 2:
			# Parse bid
			bid_idx = second_line.index('Bid') + 1
			self.option_chain_obj.underlying_bid = float(second_line[bid_idx])

			# Parse ask
			ask_idx = second_line.index('Ask') + 1
			self.option_chain_obj.underlying_ask = float(second_line[ask_idx])

			# Parse vol
			vol_idx = second_line.index('Vol') + 1
			self.option_chain_obj.underlying_volume = int(second_line[vol_idx])

		quote_data_file.close()


	def parse_option_chains(self, cboe_file):
		quote_data_file = open(cboe_file)
		option_chains = quote_data_file.readlines()
		# quote_data_file.close()

		# each line in the option chain contains the following data:
		# 0: call description - contains the option ID, expiration, strike, exchange
		# 1: call last sale
		# 2: call net
		# 3: call bid
		# 4: call ask
		# 5: call volumn
		# 6: call open interest
		# 7: put description
		# 8: put last sale
		# 9: put net
		# 10: put bid
		# 11: put ask
		# 12: put volumn
		# 13: put open interest
		# 14: nothing - due to CBOE adding an extra , at the end of all lines
		calls = []
		puts = []
		# the option chains start of line 4:
		for option_chain in option_chains[4:]:
			option_chain_parts = option_chain.split(",")

			# The expiration, strike and exchange are the same for the call
			# and put on each line
			expiration = self.get_expiration(option_chain_parts[0])
			strike = self.get_strike(option_chain_parts[0])
			exchange = self.get_exchange(option_chain_parts[0])
			
	

			call_option = Option.Option(
										expiration=expiration, 
										strike=strike,
										bid=float(option_chain_parts[3]),
										ask=float(option_chain_parts[4]),
										description=self.get_option_description(option_chain_parts[0]),
										exchange=exchange)

			put_option = Option.Option(
										expiration=expiration, 
										strike=strike,
										bid=float(option_chain_parts[10]),
										ask=float(option_chain_parts[11]),
										description=self.get_option_description(option_chain_parts[7]),
										exchange=exchange)

			if call_option.valid():
				calls.append(call_option)

			if put_option.valid():
				puts.append(put_option)

		return (calls, puts)
		# *** Original code to read the options into a pandas dataframe.
		# option_chains = pd.read_csv(cboe_file, sep=',', header=2, na_values=' ')
		# # The Strike, Expiration, and Exchange are embedded in the Call Description
		# option_chains['Strike'] = option_chains['Calls'].apply(lambda x: float(x.split(" ")[3]))
		# option_chains['Expiration'] = option_chains['Calls'].apply(lambda x: datetime.datetime.strptime("{} {} {} 16:00".format(x.split(' ')[0], x.split(' ')[1], x.split(' ')[2]), "%Y %b %d %H:%M"))
		# option_chains['Exchange'] = option_chains['Calls'].apply(lambda x: x.split('-')[1][:-1] if len(x.split('-')) > 1 else None)
		
		# # The option chains are now in one big dataframe. 
		# # Separate the options out by expiration
		# for expiration in set(option_chains['Expiration']):
		# 	#     print("building options with expiration: {}".format(expiration))
		# 	this_chain = option_chains[option_chains['Expiration'] == expiration]

		# 	# Separate calls and puts
		# 	calls = pd.DataFrame({"Description": this_chain['Calls'], 
		# 								"Last Sale": this_chain['Last Sale'], 
		# 								"Net": this_chain['Net'],
		# 								"Bid": this_chain['Bid'],
		# 								"Ask": this_chain['Ask'],
		# 								"Vol": this_chain['Vol'],
		# 								"Open Int": this_chain['Open Int'],
		# 								"Strike": this_chain['Strike'], 
		# 								"Exchange":this_chain['Exchange']})
		# 	calls['Description'] = calls['Description'].apply(lambda x: x.split('(')[1][:-1] if isinstance(x, str) else None)
		# 	calls = calls[calls['Description'].notnull()]

		# 	puts = pd.DataFrame({"Description": this_chain['Puts'], 
		# 								"Last Sale": this_chain['Last Sale.1'], 
		# 								"Net": this_chain['Net.1'],
		# 								"Bid": this_chain['Bid.1'],
		# 								"Ask": this_chain['Ask.1'],
		# 								"Vol": this_chain['Vol.1'],
		# 								"Open Int": this_chain['Open Int.1'],
		# 								"Strike": this_chain['Strike'], 
		# 								"Exchange":this_chain['Exchange']})

		# 	puts['Description'] = puts['Description'].apply(lambda x: x.split('(')[1][:-1] if isinstance(x, str) else None)
		# 	puts = puts[puts['Description'].notnull()]
			
		# 	self.option_chain_obj.add_option_chains(expiration=expiration, 
		# 											calls=calls,
		# 											puts=puts)

	def get_strike(self, description):
		return float(description.split(" ")[3])

	def get_expiration(self, description):
		return datetime.datetime.strptime("{} {} {} 23:59".format(description.split(' ')[0], description.split(' ')[1], description.split(' ')[2]), "%Y %b %d %H:%M")

	def get_exchange(self, description):
		exchange_parts = description.split('-')
		exchange = None
		if len(exchange_parts) > 1:
			exchange = exchange_parts[1][:-1] 

		return exchange

	def get_option_description(self, description):
		option_description = None
		 
		if isinstance(description, str):
			option_description = description.split('(')[1][:-1]

		return option_description
