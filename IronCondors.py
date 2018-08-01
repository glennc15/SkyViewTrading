import pandas as pd 
import numpy as np

import VerticalSpreads

import VerticalSpread
import IronCondor

class IronCondors(VerticalSpreads.VerticalSpreads):
	def __init__(self):
		super().__init__()
		# each entry in condors has the following structure:
		# {
		# expiration: {
		#     "iron condors" : pandas dataframe of condors,
		#     "put condors" : pandas dataframe of condors,
		#     "call condors" : pandas dataframe of condors,
		# }
		# }
		#
		# expiration is a datetime object representing the option expiration date
		self.condors = {}   

	def build_condors(self, option_chain_obj, risk_limit=200):
		self.build_spreads(option_chain_obj)

		for expiration, bull_calls, bull_puts, bear_calls, bear_puts in super().items():
			print("There are {:,} bull put spreads".format(bull_puts.shape[0]))
			print("There are {:,} bear call spreads".format(bear_calls.shape[0]))
			print("There are {:,} condors for expiration {}".format((bull_puts.shape[0]*bear_calls.shape[0]), expiration))			
			iron_condors, put_condors, call_condors =  self.get_condors(bull_puts, bear_calls, risk_limit, option_chain_obj.underlying_spot)

			condors = {
				"iron condors": iron_condors,
				"bull condors": put_condors,
				"bear condors": call_condors
			}

			self.condors[expiration] = condors 
		
		return self


	def itm_condors(self, spot):
		for k,v in self.condors.items():
			self.condors[k]['iron condors'] = [condor for condor in self.condors[k]['iron condors'] if (condor.put_break_even<spot<condor.call_break_even)]
			self.condors[k]['bull condors'] = [condor for condor in self.condors[k]['bull condors'] if (condor.put_break_even<spot)]
			self.condors[k]['bear condors'] = [condor for condor in self.condors[k]['bear condors'] if (condor.call_break_even>spot)]

		return self

	def sky_view_condors(self):
		for k,v in self.condors.items():
			iron_condors1 = [condor for condor in self.condors[k]['iron condors'] if (((condor.K2_Strike-condor.K1_Strike) >=(condor.K4_Strike-condor.K3_Strike)) and (condor.K2_Strike-condor.K1_Strike)*0.2<=condor.max_profit<=(condor.K2_Strike-condor.K1_Strike)*0.33)]
			iron_condors2 = [condor for condor in self.condors[k]['iron condors'] if (((condor.K2_Strike-condor.K1_Strike) < (condor.K4_Strike-condor.K3_Strike)) and (condor.K4_Strike-condor.K3_Strike)*0.2<=condor.max_profit<=(condor.K4_Strike-condor.K3_Strike)*0.33)]
			self.condors[k]['iron condors'] = iron_condors1 + iron_condors2
	
			self.condors[k]['bull condors'] = [condor for condor in self.condors[k]['bull condors'] if ((condor.K2_Strike-condor.K1_Strike)*0.2<=condor.max_profit<=(condor.K2_Strike-condor.K1_Strike)*0.33)]
			self.condors[k]['bear condors'] = [condor for condor in self.condors[k]['bear condors'] if ((condor.K4_Strike-condor.K3_Strike)*0.2<=condor.max_profit<=(condor.K4_Strike-condor.K3_Strike)*0.33)]

			return self


	def add_pop(self, pop_calculator):
		'''
		adds POP (percentage of profitability)
		a POP calculator object must be supplied that has .set_days_til_expiration()
		and

		'''
		self.pop_added = True

		for k,v in self.condors.items():
			pop_calculator.set_days_til_expiration(k)

			if isinstance(v['iron condors'], pd.DataFrame):
				put_pops = v['iron condors']['Put Break Even'].apply(lambda x: pop_calculator.pop(x))
				call_pops = v['iron condors']['Call Break Even'].apply(lambda x: pop_calculator.pop(x))
				self.condors[k]['iron condors']["POP"] = (put_pops - call_pops)

			if isinstance(v['put condors'], pd.DataFrame):
				pops = v['put condors']['Put Break Even'].apply(lambda x: pop_calculator.pop(x))
				self.condors[k]['put condors']["POP"] = pops

			if isinstance(v['call condors'], pd.DataFrame):
				pops = v['call condors']['Call Break Even'].apply(lambda x: pop_calculator.pop(x))
				self.condors[k]['call condors']["POP"] = (1-pops)

		return self


	def items(self, pretty_df=False):
		''' 
		Iterator

		'''

		for k,v in self.condors.items():
			iron_condors = None
			put_condors = None
			call_condors = None

			if pretty_df:
				if isinstance(v['iron condors'], pd.DataFrame):
					iron_condors = self.pretty_condor_df(v['iron condors'])

				if isinstance(v['put condors'], pd.DataFrame):
					put_condors = self.pretty_condor_df(v['put condors'])

				if isinstance(v['call condors'], pd.DataFrame):
					call_condors = self.pretty_condor_df(v['call condors'])

			else:
				iron_condors = v['iron condors']
				put_condors = v['put condors']
				call_condors = v['call condors']

			yield (k, iron_condors, put_condors, call_condors)

	# **** Internal methods ****

	def get_condors(self, bull_puts_df, bear_calls_df, risk_limit, spot_price):
		condor_list = self.build_condor_list(bull_puts_df, bear_calls_df, spot_price)

		# Apply risk_limit:
		# risk limit is given per contract => needs to be converter to the per option price:
		risk_limit = -risk_limit/100.0
		condor_list = [condor for condor in condor_list if condor.max_risk > risk_limit]

		# separate the condors:
		iron_condors = [condor for condor in condor_list if (condor.put_break_even and condor.call_break_even)]
		bull_condors = [condor for condor in condor_list if (condor.put_break_even and condor.call_break_even==None)]
		bear_condors = [condor for condor in condor_list if (condor.put_break_even==None and condor.call_break_even)]

		return (iron_condors, bull_condors, bear_condors)


	def build_condor_list(self, bull_spreads_df, bear_spreads_df, spot_price):
		# The condor matrix can be HUGE. Basically it's the size of the bull
		# spreads times the size of the bear spreads. 

		bull_spreads = [VerticalSpread.VerticalSpread(bull_spreads_df.iloc[idx]) for idx in range(bull_spreads_df.shape[0])]
		bear_spreads = [VerticalSpread.VerticalSpread(bear_spreads_df.iloc[idx]) for idx in range(bear_spreads_df.shape[0])]

		condor_list = [IronCondor.IronCondor(bull_put, bear_call) for bull_put in bull_spreads for bear_call in bear_spreads if (bull_put.K2_Strike<=bear_call.K1_Strike) and (bull_put.K1_Strike<spot_price<bear_call.K2_Strike)]
		condor_list = [condor for condor in condor_list if condor.valid_condor()]

		return condor_list 

		# # Example
		# # Bull Spreads index    Bear Spreads index
		# # 1             100
		# # 2             101
		# # 3             101
		# #               102
		# #               103

		# # The the condor matrix entries
		# # 1             100
		# # 1             101
		# # 1             101
		# # 1             102
		# # 1             103
		# # 2             100
		# # 2             101
		# # 2             101
		# # 2             102
		# # 2             103
		# # 3             100
		# # 3             101
		# # 3             101
		# # 3             102
		# # 3             103

		# # Bull Spread Matrix:
		# # each bull spread is repeated once for every bear spread
		# print("Going to build the initial condor matrix with shape {:,} rows".format(bull_spreads_df.shape[0]*bear_spreads_df.shape[0]))
		
		# bull_spread_repeats = bear_spreads_df.shape[0]
		# bull_spreads_matrix = bull_spreads_df.loc[np.repeat(bull_spreads_df.index.values, bull_spread_repeats)]
		# bull_spreads_matrix = bull_spreads_matrix.reset_index(drop=True)

		# # Bear Spread Matrix:
		# bear_spreads_repeats = bull_spreads_df.shape[0]
		# bear_spreads_matrix = bear_spreads_df.loc[list(bear_spreads_df.index.values)*bear_spreads_repeats] 
		# bear_spreads_matrix = bear_spreads_matrix.reset_index(drop=True)

		# # change the K1 => K3 and K2 => K4 in the column names
		# new_columns = [x if "K1_" not in x else x.replace("K1_", "K3_") for x in bear_spreads_matrix.columns]
		# new_columns = [x if "K2_" not in x else x.replace("K2_", "K4_") for x in new_columns]
		# bear_spreads_matrix.columns = new_columns

		# # remove the calculated columns from each matrix. These values were
		# # calculated when the spread was build and are not need for the condor
		# calculated_columns = ['Strike Display', 'Max Profit', 'Max Risk', 'Break Even', 'Delta', 'Gamma', 'Theta', 'Vega']
		# bull_spreads_matrix = bull_spreads_matrix.drop(calculated_columns, axis=1)
		# bear_spreads_matrix = bear_spreads_matrix.drop(calculated_columns, axis=1)


		# condor_matrix = pd.concat([bull_spreads_matrix, bear_spreads_matrix], axis=1)

		# return condor_matrix

	def pretty_condor_df(self, condor_df):
		condor_data = {
			"Strike Display": condor_df["Strike Display"],
			"Max Risk": condor_df["Max Risk"],
			"Max Profit": condor_df["Max Profit"],
			"Put Break Even": condor_df["Put Break Even"],
			"Call Break Even": condor_df["Call Break Even"],
			"Delta": np.round(condor_df['Delta'], 4),
			"Gamma": np.round(condor_df['Gamma'], 4),
			"Theta": np.round(condor_df['Theta'], 4),
			"Vega": np.round(condor_df['Vega'], 4)
		}
		
		if self.pop_added:
			condor_data["POP"] = np.round(condor_df["POP"], 3)

		condor_df = pd.DataFrame(condor_data)

		if self.pop_added:
			columns = ["Strike Display", "Max Risk", "Max Profit", "Put Break Even", "Call Break Even", "POP", "Delta", "Gamma", "Theta", "Vega"]
		else:
			columns = ["Strike Display", "Max Risk", "Max Profit", "Put Break Even", "Call Break Even", "Delta", "Gamma", "Theta", "Vega"]


		condor_df = condor_df[columns]

		return condor_df












