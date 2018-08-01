class IronCondor:
	def __init__(self, bull_side, bear_side):
		self.K1_Ask = bull_side.K1_Ask
		self.K1_Bid = bull_side.K1_Bid
		self.K1_Description = bull_side.K1_Description        
		self.K1_Exchange = bull_side.K1_Exchange        
		self.K1_Last_Sale = bull_side.K1_Last_Sale      
		self.K1_Net = bull_side.K1_Net        
		self.K1_Open_Int = bull_side.K1_Open_Int        
		self.K1_Strike = bull_side.K1_Strike        
		self.K1_Vol = bull_side.K1_Vol
		self.K1_Sigma = bull_side.K1_Sigma                
		self.K1_Delta = bull_side.K1_Delta                
		self.K1_Gamma = bull_side.K1_Gamma                
		self.K1_Theta = bull_side.K1_Theta                
		self.K1_Vega = bull_side.K1_Vega                
		self.K1_Entry = bull_side.K1_Entry
		
		self.K2_Ask = bull_side.K2_Ask
		self.K2_Bid = bull_side.K2_Bid
		self.K2_Description = bull_side.K2_Description        
		self.K2_Exchange = bull_side.K2_Exchange        
		self.K2_Last_Sale = bull_side.K2_Last_Sale      
		self.K2_Net = bull_side.K2_Net        
		self.K2_Open_Int = bull_side.K2_Open_Int        
		self.K2_Strike = bull_side.K2_Strike        
		self.K2_Vol = bull_side.K2_Vol
		self.K2_Sigma = bull_side.K2_Sigma                
		self.K2_Delta = bull_side.K2_Delta                
		self.K2_Gamma = bull_side.K2_Gamma                
		self.K2_Theta = bull_side.K2_Theta                
		self.K2_Vega = bull_side.K2_Vega                
		self.K2_Entry = bull_side.K2_Entry
		
		self.K3_Ask = bear_side.K1_Ask
		self.K3_Bid = bear_side.K1_Bid
		self.K3_Description = bear_side.K1_Description        
		self.K3_Exchange = bear_side.K1_Exchange        
		self.K3_Last_Sale = bear_side.K1_Last_Sale      
		self.K3_Net = bear_side.K1_Net        
		self.K3_Open_Int = bear_side.K1_Open_Int        
		self.K3_Strike = bear_side.K1_Strike        
		self.K3_Vol = bear_side.K1_Vol
		self.K3_Sigma = bear_side.K1_Sigma                
		self.K3_Delta = bear_side.K1_Delta                
		self.K3_Gamma = bear_side.K1_Gamma                
		self.K3_Theta = bear_side.K1_Theta                
		self.K3_Vega = bear_side.K1_Vega                
		self.K3_Entry = bear_side.K1_Entry
		
		self.K4_Ask = bear_side.K2_Ask
		self.K4_Bid = bear_side.K2_Bid
		self.K4_Description = bear_side.K2_Description        
		self.K4_Exchange = bear_side.K2_Exchange        
		self.K4_Last_Sale = bear_side.K2_Last_Sale      
		self.K4_Net = bear_side.K2_Net        
		self.K4_Open_Int = bear_side.K2_Open_Int        
		self.K4_Strike = bear_side.K2_Strike        
		self.K4_Vol = bear_side.K2_Vol
		self.K4_Sigma = bear_side.K2_Sigma                
		self.K4_Delta = bear_side.K2_Delta                
		self.K4_Gamma = bear_side.K2_Gamma                
		self.K4_Theta = bear_side.K2_Theta                
		self.K4_Vega = bear_side.K2_Vega                
		self.K4_Entry = bear_side.K2_Entry
		
		self.strike_display = "{}/{}/{}/{}".format(self.K1_Strike, self.K2_Strike, self.K3_Strike, self.K4_Strike)
		self.max_profit = self.K1_Entry + self.K2_Entry + self.K3_Entry + self.K4_Entry
		self.max_risk = self.get_max_risk()
		self.put_break_even = self.get_put_break_even(strike_diff=(self.K2_Strike-self.K1_Strike), K2_strike=self.K2_Strike)
		self.call_break_even = self.get_call_break_even(strike_diff=(self.K4_Strike-self.K3_Strike), K3_strike=self.K3_Strike)
		self.delta = self.K1_Delta + self.K2_Delta + self.K3_Delta + self.K4_Delta
		self.gamma = self.K1_Gamma + self.K2_Gamma + self.K3_Gamma + self.K4_Gamma
		self.theta = self.K1_Theta + self.K2_Theta + self.K3_Theta + self.K4_Theta
		self.vega = self.K1_Vega + self.K2_Vega + self.K3_Vega + self.K4_Vega
		self.pop = None
		self.er = None
		
		if (self.put_break_even==None) or (self.call_break_even==None):
			self.broken_condor = True
			self.adjust_max_profit()
		else:
			self.broken_condor = False
			
		
	def get_max_risk(self):
		put_strike_diff = self.K2_Strike - self.K1_Strike
		call_strike_diff = self.K4_Strike - self.K3_Strike
		if put_strike_diff > call_strike_diff:
			max_risk = -put_strike_diff + self.max_profit
		else:
			max_risk = -call_strike_diff + self.max_profit
			
		return max_risk
	
	def get_put_break_even(self, strike_diff, K2_strike):
		# check for a broken wing condor:
		if self.max_profit > strike_diff:
			break_even = None
		else:
			break_even = K2_strike - self.max_profit
			
		return break_even

	def get_call_break_even(self, strike_diff, K3_strike):
		# check for a broken wing condor:
		if self.max_profit > strike_diff:
			break_even = None
		else:
			break_even = K3_strike + self.max_profit
			
		return break_even
			
	def adjust_max_profit(self):
		if self.put_break_even == None:
			self.max_profit -= (self.K2_Strike - self.K1_Strike)
		
		if self.call_break_even == None:
			self.max_profit -= (self.K4_Strike - self.K3_Strike)
		
	def valid_condor(self):
		max_profit_ok = False
		max_risk_ok = False
		break_evens_ok = False
		put_break_even_ok = False
		call_break_even_ok = False
		
		if self.max_profit > 0:
			max_profit_ok = True
		
		if self.max_risk < 0:
			max_risk_ok = True
			
		if self.put_break_even or self.call_break_even:
			break_evens_ok = True
		
		if (self.put_break_even==None) or (self.K1_Strike < self.put_break_even < self.K2_Strike):
			put_break_even_ok = True
		
		if (self.call_break_even==None) or (self.K3_Strike < self.call_break_even < self.K4_Strike):
			call_break_even_ok = True
		
			
		if (max_profit_ok & max_risk_ok & break_evens_ok & put_break_even_ok & call_break_even_ok):
			return self
		else:
			return None

	def to_dict(self):
		data_dict = {
			"strike_display": self.strike_display,
			"max_profit": self.max_profit,
			"max_risk": self.max_risk,
			"put_break_even": self.put_break_even,
			"call_break_even": self.call_break_even,
			"delta": self.delta,
			"gamma": self.gamma,
			"theta": self.theta,
			"vega": self.vega,
			"pop": self.pop,
			"expected_return": self.er
		}

		return data_dict

