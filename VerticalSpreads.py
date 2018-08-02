import numpy as np
import pandas as pd

from pymongo import MongoClient

import VerticalSpread
import Option
'''

Builds vertical spreads from an OptionChain object.

'''

class VerticalSpreads(object):
	def __init__(self):
		# each entry in vertical_spreads has the following structure:
		# {expiration:
		#	 {
		# 		'bull_calls': pandas dataframe of bull call debit spreads
		# 		'bull_puts' : pandas dataframe of bull put credit spreads
		#		'bear_calls': pandas dataframe of bear call credit spreads
		#		'bear_puts' : pandas dataframe of bear put debit spreads
		# 	 } 
		# }
		#
		# expiration is a datetime object representing the option expiration date
		self.vertical_spreads = {}
		self.pop_added = False

		self.underlying_symbol = None
		self.timestamp = None

	def build_spreads(self, 
					option_chain_obj, 
					bull_put_spreads=True,
					bull_call_spreads=False,
					bear_call_spreads=True,
					bear_put_spreads=False):

		self.underlying_symbol = option_chain_obj.underlying_symbol
		self.timestamp = option_chain_obj.timestamp

		for expiration, calls, puts in option_chain_obj.items():
			bull_put_list = []
			bull_call_list = []
			bear_put_list = []
			bear_call_list = [] 

			if bull_call_spreads:
				bull_call_list = self.get_bull_calls(option_chains=calls, spot=option_chain_obj.underlying_spot)

			if bull_put_spreads:
				bull_put_list = self.get_bull_puts(option_chains=puts, spot=option_chain_obj.underlying_spot)

			if bear_put_spreads:
				bear_put_list = self.get_bear_puts(option_chains=puts, spot=option_chain_obj.underlying_spot)

			if bear_call_spreads:
				bear_call_list = self.get_bear_calls(option_chains=calls, spot=option_chain_obj.underlying_spot)

			spreads_data = {
				"Bull Puts": bull_put_list,
				"Bull Calls": bull_call_list,
				"Bear Calls": bear_call_list,
				"Bear Puts": bear_put_list
			}

			self.vertical_spreads[expiration] = spreads_data

		return self

	def risk_limit(self, risk_limit):
		''' 

		risk_limit is per contract, not per option.

		'''

		for k,v in self.vertical_spreads.items():
			self.vertical_spreads[k]["Bull Puts"] = [spread for spread in self.vertical_spreads[k]["Bull Puts"] if (spread.max_risk>=(-risk_limit/100))]
			self.vertical_spreads[k]["Bull Calls"] = [spread for spread in self.vertical_spreads[k]["Bull Calls"] if (spread.max_risk>=(-risk_limit/100))]
			self.vertical_spreads[k]["Bear Puts"] = [spread for spread in self.vertical_spreads[k]["Bear Puts"] if (spread.max_risk>=(-risk_limit/100))]
			self.vertical_spreads[k]["Bear Calls"] = [spread for spread in self.vertical_spreads[k]["Bear Calls"] if (spread.max_risk>=(-risk_limit/100))]


		return self

	def sky_view_spreads(self):
		'''

		Criteria from SkyView Trading. Collect premium between 20% - 33% of
		width of strikes.  Only applies to short spreads (bull puts and bear calls)

		'''
		for k,v in self.vertical_spreads.items():			
			self.vertical_spreads[k]["Bull Puts"] = [spread for spread in self.vertical_spreads[k]["Bull Puts"] if (((spread.k2_option.strike-spread.k1_option.strike)*0.2)<=spread.max_profit<=((spread.k2_option.strike-spread.k1_option.strike)*0.33))]
			self.vertical_spreads[k]["Bull Calls"] = [spread for spread in self.vertical_spreads[k]["Bull Calls"] if (((spread.k2_option.strike-spread.k1_option.strike)*0.2)<=spread.max_profit<=((spread.k2_option.strike-spread.k1_option.strike)*0.33))]
			self.vertical_spreads[k]["Bear Puts"] = [spread for spread in self.vertical_spreads[k]["Bear Puts"] if (((spread.k2_option.strike-spread.k1_option.strike)*0.2)<=spread.max_profit<=((spread.k2_option.strike-spread.k1_option.strike)*0.33))]
			self.vertical_spreads[k]["Bear Calls"] = [spread for spread in self.vertical_spreads[k]["Bear Calls"] if (((spread.k2_option.strike-spread.k1_option.strike)*0.2)<=spread.max_profit<=((spread.k2_option.strike-spread.k1_option.strike)*0.33))]

		return self

	def add_pop(self, pop_calculator, current_spot):
		'''

		adds POP (percentage of profitability)
		a POP calculator object must be supplied that has .set_days_til_expiration()
		and

		'''

		for k,v in self.vertical_spreads.items():
			pop_calculator.set_days_til_expiration(k)

			for spread in self.vertical_spreads[k]["Bull Puts"]: 
				spread.pop = pop_calculator.pop(spread.break_even, current_spot)

			for spread in self.vertical_spreads[k]["Bull Calls"]:
				spread.pop = pop_calculator.pop(spread.break_even, current_spot)

			for spread in self.vertical_spreads[k]["Bear Puts"]:
				spread.pop = 1 - pop_calculator.pop(spread.break_even, current_spot)

			for spread in self.vertical_spreads[k]["Bear Calls"]:
				spread.pop = 1 - pop_calculator.pop(spread.break_even, current_spot)

		return self

	def add_expected_return(self, pop_calculator, current_spot):
		'''

		adds expected return.

		using pop_calculators returns to project spots, kinda hackerish but
		works for now.

		'''

		for k,v in self.vertical_spreads.items():
			pop_calculator.set_days_til_expiration(k)
			projected_returns = pop_calculator.returns * current_spot

			for spread in self.vertical_spreads[k]["Bull Puts"]:
				k1_payouts = spread.k1_option.set_payout_method(Option.put_option_payout).payouts(projected_returns) 
				k2_payouts = spread.k2_option.set_payout_method(Option.put_option_payout).payouts(projected_returns) 
				spread.expected_return = (k1_payouts+k2_payouts).mean()

			for spread in self.vertical_spreads[k]["Bull Calls"]:
				k1_payouts = spread.k1_option.set_payout_method(Option.call_option_payout).payouts(projected_returns) 
				k2_payouts = spread.k2_option.set_payout_method(Option.call_option_payout).payouts(projected_returns) 
				spread.expected_return = (k1_payouts+k2_payouts).mean()

			for spread in self.vertical_spreads[k]["Bear Puts"]:
				k1_payouts = spread.k1_option.set_payout_method(Option.put_option_payout).payouts(projected_returns) 
				k2_payouts = spread.k2_option.set_payout_method(Option.put_option_payout).payouts(projected_returns) 
				spread.expected_return = (k1_payouts+k2_payouts).mean()

			for spread in self.vertical_spreads[k]["Bear Calls"]:
				k1_payouts = spread.k1_option.set_payout_method(Option.call_option_payout).payouts(projected_returns) 
				k2_payouts = spread.k2_option.set_payout_method(Option.call_option_payout).payouts(projected_returns) 
				spread.expected_return = (k1_payouts+k2_payouts).mean()

		return self

	def write_to_mongo(self, mongo_address):
		'''

		'''

		client = MongoClient(mongo_address)

		for k,v in self.vertical_spreads.items():
			for spread in self.vertical_spreads[k]["Bull Puts"]:
				mongo_data = spread.to_dict()
				mongo_data['symbol'] = self.underlying_symbol
				mongo_data['timestamp'] = self.timestamp
				mongo_data['expiration'] = k 
				mongo_data['type'] = "Bull Put Credit Spread"	
				
				client.Spreads.vertical.insert_one(mongo_data)			

			for spread in self.vertical_spreads[k]["Bull Calls"]:
				mongo_data = spread.to_dict()
				mongo_data['symbol'] = self.underlying_symbol
				mongo_data['timestamp'] = self.timestamp
				mongo_data['expiration'] = k 
				mongo_data['type'] = "Bull Call Debit Spread"

				client.Spreads.vertical.insert_one(mongo_data)			


			for spread in self.vertical_spreads[k]["Bear Puts"]:
				mongo_data = spread.to_dict()
				mongo_data['symbol'] = self.underlying_symbol
				mongo_data['timestamp'] = self.timestamp
				mongo_data['expiration'] = k 
				mongo_data['type'] = "Bear Put Debit Spread"

				client.Spreads.vertical.insert_one(mongo_data)			


			for spread in self.vertical_spreads[k]["Bear Calls"]:
				mongo_data = spread.to_dict()
				mongo_data['symbol'] = self.underlying_symbol
				mongo_data['timestamp'] = self.timestamp
				mongo_data['expiration'] = k 
				mongo_data['type'] = "Bear Call Credit Spread"

				client.Spreads.vertical.insert_one(mongo_data)			


		return self

	def itm_spreads(self, spot):
		'''

		bull spreads break even < spot
		bear spreads break even > spot


		'''

		for k,v in self.vertical_spreads.items():			
			self.vertical_spreads[k]["Bull Puts"] = [spread for spread in self.vertical_spreads[k]["Bull Puts"] if (spread.break_even<spot)]
			self.vertical_spreads[k]["Bull Calls"] = [spread for spread in self.vertical_spreads[k]["Bull Calls"] if (spread.break_even<spot)]
			self.vertical_spreads[k]["Bear Puts"] = [spread for spread in self.vertical_spreads[k]["Bear Puts"] if (spread.break_even>spot)]
			self.vertical_spreads[k]["Bear Calls"] = [spread for spread in self.vertical_spreads[k]["Bear Calls"] if (spread.break_even>spot)]

		return self

	def items(self):
		''' 

		Iterator

		'''
		for expiration,v in self.vertical_spreads.items():
			
			bull_calls = v["Bull Calls"]
			bull_puts = v["Bull Puts"]
			bear_calls = v["Bear Calls"]
			bear_puts = v["Bear Puts"]

			yield (expiration, bull_calls, bull_puts, bear_calls, bear_puts)

	# --- Internal methods --- #
	def build_option_matrix(self, option_chain):
		k1_options = self.build_k1_options(option_chain)
		k2_options = self.build_k2_options(option_chain)

		option_matrix = pd.concat([k1_options, k2_options], axis=1)
		# option_matrix['underlying_symbol'] = self.option_chain_obj.underlying_symbol
		option_matrix['Strike Display'] = option_matrix.K1_Strike.astype(str).str.cat(option_matrix.K2_Strike.astype(str), sep=" / ")
		# option_matrix['strike_delta'] = option_matrix['k2_strike'] - option_matrix['k1_strike']
		
		return option_matrix 

	def build_k1_options(self, option_chain):
		k1_repeats = [(i-1) for i in  range(len(option_chain), 0, -1)]
		k1_options = option_chain.loc[np.repeat(option_chain.index.values, k1_repeats)]
		k1_options = k1_options.reset_index(drop=True)
		# prepend "k1_" to all column names
		k1_options.columns = [("K1_" + i) for i in k1_options.columns]

		return k1_options

	def build_k2_options(self, option_chain):
		k2_indices = [x for j in range(1, len(option_chain)) for x in range(j, len(option_chain))]
		k2_options = option_chain.copy()
		k2_options = k2_options.reset_index(drop=True)
		k2_options = k2_options.loc[k2_indices]
		k2_options = k2_options.reset_index(drop=True)
		#prepend "k2_" to all column names
		k2_options.columns = [("K2_" + i) for i in k2_options.columns]

		return k2_options

	def get_bull_puts(self, option_chains, spot):
		bull_puts = [VerticalSpread.BullPutSpread(k1_option.my_copy(), k2_option.my_copy()) for k1_option in option_chains for k2_option in option_chains if (k1_option.strike<k2_option.strike) and (k1_option.strike<spot)]
		bull_puts = [bull_put for bull_put in bull_puts if bull_put.valid()]

		return bull_puts 

	def get_bull_calls(self, option_chain_obj):
		pass

	def get_bear_calls(self, option_chains, spot):

		bear_calls = [VerticalSpread.BearCallSpread(k1_option.my_copy(), k2_option.my_copy()) for k1_option in option_chains for k2_option in option_chains if (k1_option.strike<k2_option.strike) and (k2_option.strike>spot)]
		bear_calls = [bear_call for bear_call in bear_calls if bear_call.valid()]

		return bear_calls 

	def get_bear_puts(self, option_chain_obj):
		pass


	def pretty_spread_df(self, option_matrix):
		option_data = {
			"Strike Display": option_matrix["Strike Display"],
			"Max Risk": option_matrix["Max Risk"],
			"Max Profit": option_matrix["Max Profit"],
			"Break Even": option_matrix["Break Even"],
			"Delta": np.round(option_matrix['Delta'], 4),
			"Gamma": np.round(option_matrix['Gamma'], 4),
			"Theta": np.round(option_matrix['Theta'], 4),
			"Vega": np.round(option_matrix['Vega'], 4)
		}

		if self.pop_added:
			option_data["POP"] = np.round(option_matrix["POP"], 3)

		spreads_df = pd.DataFrame(option_data)

		if self.pop_added:
			columns = ["Strike Display", "Max Risk", "Max Profit", "Break Even", "POP", "Delta", "Gamma", "Theta", "Vega"]	
		else:
			columns = ["Strike Display", "Max Risk", "Max Profit", "Break Even", "Delta", "Gamma", "Theta", "Vega"]	

		spreads_df = spreads_df[columns]

		return spreads_df

	def spreads_clean_up(self, spread_df):
		'''

		All spreads should have the following:
		Max Profit > 0
		Max Risk < 0
		K1 < Break Even < K2

		'''

		spread_df = spread_df[spread_df['Max Profit'].gt(0)]
		spread_df = spread_df[spread_df['Max Risk'].lt(0)]
		spread_df = spread_df[spread_df['Break Even'].between(spread_df['K1_Strike'], spread_df['K2_Strike'])]

		return spread_df







