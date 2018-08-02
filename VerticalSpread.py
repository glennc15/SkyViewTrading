class VerticalSpread:
	def __init__(self, k1_option, k2_option):

		self.k1_option = k1_option
		self.k2_option = k2_option

		self.strike_display = "{}/{}".format(self.k1_option.strike, self.k2_option.strike)

		self.delta = k1_option.positions * k1_option.delta + k2_option.positions * k2_option.delta
		self.gamma = k1_option.positions * k1_option.gamma + k2_option.positions * k2_option.gamma
		self.theta = k1_option.positions * k1_option.theta + k2_option.positions * k2_option.theta
		self.vega = k1_option.positions * k1_option.vega + k2_option.positions * k2_option.vega

		self.pop = None
		self.expected_return = None
		
	def valid(self):
		strikes_ok = False
		break_even_ok = False

		if self.k1_option.strike < self.k2_option.strike:
			strike_ok = True

		if self.k1_option.strike < self.break_even < self.k2_option.strike:
			break_even_ok = True

		if (strike_ok & break_even_ok):
			return True
		else:
			return False

class CreditSpread(VerticalSpread):
	def __init__(self, k1_option, k2_option):
		super().__init__(k1_option, k2_option)
		self.max_profit = self.k1_option.entry_price + self.k2_option.entry_price
		self.max_risk = self.k1_option.strike - self.k2_option.strike + self.max_profit

	def valid(self):
		strikes_ok = False
		break_even_ok = False
		max_profit_ok = False
		max_risk_ok = False

		if self.k1_option.strike < self.k2_option.strike:
			strikes_ok = True

		if self.k1_option.strike < self.break_even < self.k2_option.strike:
			break_even_ok = True

		if self.max_profit > 0:
			max_profit_ok = True

		if self.max_risk < 0:
			max_risk_ok = True

		# print("strike_ok: {}".format(strikes_ok))
		# print("break_even_ok: {}".format(break_even_ok))
		# print("max_profit_ok: {}".format(max_profit_ok))
		# print("max_risk_ok: {}".format(max_risk_ok))
	

		if (max_profit_ok & max_risk_ok & strikes_ok & break_even_ok):
			return True
		else:
			return False


class BullSpread:
	def set_break_even(self):
		self.break_even = self.k2_option.strike - self.max_profit


class BearSpread:
	def set_break_even(self):
		self.break_even = self.k1_option.strike + self.max_profit


class BullPutSpread(CreditSpread, BullSpread):
# class BullPutSpread(CreditSpread):
	def __init__(self, k1_option, k2_option):
		super().__init__(k1_option.set_positions(1), k2_option.set_positions(-1))
		
		self.set_break_even()

		# print(self.strike_display)
		# print("max_profit: {}".format(self.max_profit))
		# print("max_risk: {}".format(self.max_risk))
		# print("break_even: {}".format(self.break_even))


class BearCallSpread(CreditSpread, BearSpread):
# class BullPutSpread(CreditSpread):
	def __init__(self, k1_option, k2_option):
		super().__init__(k1_option.set_positions(-1), k2_option.set_positions(1))
		
		self.set_break_even()

		# print(self.strike_display)
		# print("max_profit: {}".format(self.max_profit))
		# print("max_risk: {}".format(self.max_risk))
		# print("break_even: {}".format(self.break_even))

