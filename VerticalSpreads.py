import numpy as np
import pandas as pd


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

	def build_spreads(self, 
					option_chain_obj, 
					bull_put_spreads=True,
					bull_call_spreads=False,
					bear_call_spreads=True,
					bear_put_spreads=False):

		for expiration, calls, puts in option_chain_obj.items():
			bull_put_spreads_df = None
			bull_call_spreads_df = None
			bear_put_spreads_df = None
			bear_call_spreads_df = None 

			if bull_call_spreads:
				bull_call_spreads_df = self.get_bull_calls(calls)

			if bull_put_spreads:
				bull_put_spreads_df = self.get_bull_puts(puts)

			if bear_put_spreads:
				bear_put_spreads_df = self.get_bear_puts(puts)

			if bear_call_spreads:
				bear_call_spreads_df = self.get_bear_calls(calls)

			spreads_data = {
				"Bull Puts": bull_put_spreads_df,
				"Bull Calls": bull_call_spreads_df,
				"Bear Calls": bear_call_spreads_df,
				"Bear Puts": bear_put_spreads_df
			}

			self.vertical_spreads[expiration] = spreads_data

		return self

	def risk_limit(self, risk_limit):
		''' 

		risk_limit is per contract, not per option.

		'''

		for k,v in self.vertical_spreads.items():
			if isinstance(v["Bull Puts"], pd.DataFrame):
				self.vertical_spreads[k]["Bull Puts"] = self.vertical_spreads[k]["Bull Puts"][self.vertical_spreads[k]["Bull Puts"]['Max Risk'].gt(-risk_limit/100)]

			if isinstance(v["Bull Calls"], pd.DataFrame):
				self.vertical_spreads[k]["Bull Calls"] = self.vertical_spreads[k]["Bull Calls"][self.vertical_spreads[k]["Bull Calls"]['Max Risk'].gt(-risk_limit/100)]

			if isinstance(v["Bear Puts"], pd.DataFrame):
				self.vertical_spreads[k]["Bear Puts"] = self.vertical_spreads[k]["Bear Puts"][self.vertical_spreads[k]["Bear Puts"]['Max Risk'].gt(-risk_limit/100)]

			if isinstance(v["Bear Calls"], pd.DataFrame):
				self.vertical_spreads[k]["Bear Calls"] = self.vertical_spreads[k]["Bear Calls"][self.vertical_spreads[k]["Bear Calls"]['Max Risk'].gt(-risk_limit/100)]

		return self

	def sky_view_spreads(self):
		'''

		Criteria from SkyView Trading. Collect premium between 20% - 33% of
		width of strikes.  Only applies to short spreads (bull puts and bear calls)

		'''

		# max_profit = strike_diff - premium => premium = strike_diff - max_profit 

		for expiration, bull_calls, bull_puts, bear_calls, bear_puts in self.items():
			if isinstance(bull_calls, pd.DataFrame):
				# strike_diff = bull_calls["K2 Strike"] - bull_calls["K1 Strike"]
				# self.vertical_spreads[expiration]['Bull Calls'] = bull_calls[bull_calls["Max Profit"].between(strike_diff*0.2, strike_diff*0.33)]
				self.vertical_spreads[expiration]['Bull Calls'] = None

			if isinstance(bull_puts, pd.DataFrame):
				strike_diff = bull_puts["K2_Strike"] - bull_puts["K1_Strike"]
				self.vertical_spreads[expiration]['Bull Puts'] = bull_puts[bull_puts["Max Profit"].between(strike_diff*0.2, strike_diff*0.33)]
			
			if isinstance(bear_calls, pd.DataFrame):
				strike_diff = bear_calls["K2_Strike"] - bear_calls["K1_Strike"]
				self.vertical_spreads[expiration]['Bear Calls'] = bear_calls[bear_calls["Max Profit"].between(strike_diff*0.2, strike_diff*0.33)]
			
			if isinstance(bear_puts, pd.DataFrame):
				# strike_diff = bear_puts["K2 Strike"] - bear_puts["K1 Strike"]
				# self.vertical_spreads[expiration]['Bear Puts'] = bear_puts[bear_puts["Max Profit"].between(strike_diff*0.2, strike_diff*0.33)]
				self.vertical_spreads[expiration]['Bear Puts'] = None

		return self

	def add_pop(self, pop_calculator):
		'''

		adds POP (percentage of profitability)
		a POP calculator object must be supplied that has .set_days_til_expiration()
		and


		'''
		self.pop_added = True

		for expiration, bull_calls, bull_puts, bear_calls, bear_puts in self.items():
			pop_calculator.set_days_til_expiration(expiration)

			if isinstance(bull_calls, pd.DataFrame):
				pops = bull_calls['Break Even'].apply(lambda x: pop_calculator.pop(x))
				self.vertical_spreads[expiration]['Bull Calls']['POP'] = pops
			
			if isinstance(bull_puts, pd.DataFrame):
				pops = bull_puts['Break Even'].apply(lambda x: pop_calculator.pop(x))
				self.vertical_spreads[expiration]['Bull Puts']['POP'] = pops 
			
			if isinstance(bear_calls, pd.DataFrame):
				pops = bear_calls['Break Even'].apply(lambda x: pop_calculator.pop(x))
				self.vertical_spreads[expiration]['Bear Calls']['POP'] = (1-pops)
			
			if isinstance(bear_puts, pd.DataFrame):
				pops = bear_puts['Break Even'].apply(lambda x: pop_calculator.pop(x))
				self.vertical_spreads[expiration]['Bear Puts']['POP'] = (1-pops) 

		return self

	def itm_spreads(self, spot):
		'''

		bull spreads break even < spot
		bear spreads break even > spot


		'''

		for expiration, bull_calls, bull_puts, bear_calls, bear_puts in self.items():
			if isinstance(bull_calls, pd.DataFrame):
				self.vertical_spreads[expiration]['Bull Calls'] = bull_calls[bull_calls['Break Even'].lt(spot)]
			
			if isinstance(bull_puts, pd.DataFrame):
				self.vertical_spreads[expiration]['Bull Puts'] = bull_puts[bull_puts['Break Even'].lt(spot)]
			
			if isinstance(bear_calls, pd.DataFrame):
				self.vertical_spreads[expiration]['Bear Calls'] = bear_calls[bear_calls['Break Even'].gt(spot)]
			
			if isinstance(bear_puts, pd.DataFrame):
				self.vertical_spreads[expiration]['Bear Puts'] = bear_puts[bear_puts['Break Even'].gt(spot)]

		return self

	def items(self, pretty_df=False):
		''' 

		Iterator

		'''
		for k,v in self.vertical_spreads.items():
			bull_calls = None
			bull_puts = None
			bear_calls = None
			bear_puts = None

			if pretty_df:
				if isinstance(v["Bull Calls"], pd.DataFrame):
					bull_calls = self.pretty_spread_df(v["Bull Calls"])

				if isinstance(v["Bull Puts"], pd.DataFrame):
					bull_puts = self.pretty_spread_df(v["Bull Puts"])

				if isinstance(v["Bear Calls"], pd.DataFrame):					
					bear_calls = self.pretty_spread_df(v["Bear Calls"])

				if isinstance(v["Bear Puts"], pd.DataFrame):	
					bear_puts = self.pretty_spread_df(v["Bear Puts"])

			else:
				bull_calls = v["Bull Calls"]
				bull_puts = v["Bull Puts"]
				bear_calls = v["Bear Calls"]
				bear_puts = v["Bear Puts"]

			yield (k, bull_calls, bull_puts, bear_calls, bear_puts)

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

	def get_bull_puts(self, option_chains):
		option_matrix = self.build_option_matrix(option_chains)

		option_matrix["K1_Entry"] = -option_matrix["K1_Ask"]
		option_matrix["K2_Entry"] = option_matrix["K2_Bid"]

		option_matrix['Max Profit'] = option_matrix['K1_Entry'] + option_matrix["K2_Entry"]
		option_matrix['Max Risk'] = (option_matrix["K1_Strike"] - option_matrix["K2_Strike"]) + option_matrix['Max Profit']
		option_matrix['Break Even'] = option_matrix["K2_Strike"] - option_matrix['Max Profit']
		
		option_matrix['Delta'] = -1*option_matrix['K2_Delta'] + 1*option_matrix['K1_Delta']
		option_matrix['Gamma'] = -1*option_matrix['K2_Gamma'] + 1*option_matrix['K1_Gamma']
		option_matrix['Theta'] = -1*option_matrix['K2_Theta'] + 1*option_matrix['K1_Theta']
		option_matrix['Vega'] = -1*option_matrix['K2_Vega'] + 1*option_matrix['K1_Vega']

		# spreads = self.spreads_clean_up(option_matrix)
		spreads = option_matrix

		return spreads

	def get_bull_calls(self, option_chain_obj):
		pass

	def get_bear_calls(self, option_chains):
		option_matrix = self.build_option_matrix(option_chains)

		option_matrix["K1_Entry"] = option_matrix["K1_Bid"]
		option_matrix["K2_Entry"] = -option_matrix["K2_Ask"]

		option_matrix['Max Profit'] = option_matrix['K1_Entry'] + option_matrix["K2_Entry"]
		option_matrix['Max Risk'] = (option_matrix["K1_Strike"] - option_matrix["K2_Strike"]) + option_matrix['Max Profit']
		option_matrix['Break Even'] = option_matrix["K1_Strike"] + option_matrix['Max Profit']
		
		option_matrix['Delta'] = -1*option_matrix['K1_Delta'] + 1*option_matrix['K2_Delta']
		option_matrix['Gamma'] = -1*option_matrix['K1_Gamma'] + 1*option_matrix['K2_Gamma']
		option_matrix['Theta'] = -1*option_matrix['K1_Theta'] + 1*option_matrix['K2_Theta']
		option_matrix['Vega'] = -1*option_matrix['K1_Vega'] + 1*option_matrix['K2_Vega']

		spreads = self.spreads_clean_up(option_matrix)
		
		return spreads

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







