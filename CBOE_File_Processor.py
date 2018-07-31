# Class to process a CBOE QuoteData.dat file. Opens the file and reads the
# contents to a dataframe. Also calculates IV for each option in the chain
# 
import datetime
import pandas
import io
import re


class CBOE_File_Processor(object):

	def __init__(self, cboe_filename=None):
		# the filename needs to include the path
		self.cboe_filename = cboe_filename
		self.cboe_data = None
		self.underlying_data = None

		self.month_codes = {'jan': 'A', 'feb': 'B', 'mar': 'C',
							'apr': 'D', 'may': 'E', 'jun': 'F',
							'jul': 'G', 'aug': 'H', 'sep': 'I',
							'oct': 'J', 'nov': 'K', 'dec': 'L'}

		self.symbols = []

	def open_cboe_file(self, cboe_filename=None):
		if not cboe_filename:
			cboe_filename =self.cboe_filename
		self.cboe_data = open(cboe_filename)

	# The first two lines of a QuoteData.dat file contain underlying data
	# including date/time info.
	def set_underlying_info(self, cboe_data):
		first_line, second_line = cboe_data.splitlines()[0:2]

		# print "first_line: {}".format(first_line)
		# print "second_line: {}".format(second_line)
		
		# Symbol and the description come mixed together 
		first_line_parts = first_line.split(',')[:-1]
		if len(first_line_parts) > 3:
		    new_first_line = [first_line_parts[0] + first_line_parts[1]]
		    for idx in range(2,4):
		        new_first_line.append(first_line_parts[idx])

		    description, close, last_change = new_first_line
		else:
			description, close, last_change = first_line.split(',')[0:-1]

		symbol = description.split()[0]
		begin_idx = len(symbol)+2
		description = description[begin_idx:-1]
		if len(second_line.split(',')) >= 9:
			timestamp, bid_tag, bid, ask_tag, ask, size_tag, size, vol_tag, volume = second_line.split(',')[0:-1]
		else:
			timestamp = second_line.split(',')[0]
			bid = 0.0
			ask = 0.0
			size = "0x0"
			volume = 0
			
		timestamp = datetime.datetime.strptime(timestamp, "%b %d %Y @ %H:%M ET")
		self.underlying_data = {
			'symbol': symbol,
			'description': description,
			'close': float(close),
			'last_change': float(last_change),
			'timestamp': timestamp,
			'bid': float(bid),
			'ask': float(ask),
			'size': size,
			'volume': int(volume)
		}

	def get_underlying_info(self, cboe_data=None):
		if cboe_data:
			self.cboe_data = cboe_data
		if not self.underlying_data:
			self.set_underlying_info(cboe_data)

		return self.underlying_data

	def getExpiration(self, x):
		exp_year, exp_month, strike_str, option_desc = x.split()

		# Need to get expiration month:
        # Can use the description string, strike price and the month code.
        # Remove the ".00" form the strike price, get the month code from the
        # description, prepend the month code to the strike price, then find
        # the poistion of the substing inside the option desciption string.
        # The expiration day begins at 3 positions before and ends 2 more
        # positions from this position.
		strike_str = strike_str.split('.')[0]
		# add month code to strike_str
		strike_str = self.month_codes[exp_month.lower()] + strike_str
		strike_str_idx = option_desc.find(strike_str)
		day_idx_begin = strike_str_idx - 2
		day_idx_end = day_idx_begin + 2
		expiration_day = option_desc[day_idx_begin:day_idx_end]
		date_str =  expiration_day + ' ' + exp_month + ' ' + exp_year
		# Convert the date string to a datetime object
		expiration_date = datetime.datetime.strptime(date_str, "%d %b %y")		
		return expiration_date

	def getStrike(self, x):
		# The strike is in the desciption string.
		exp_year, exp_month, strike_str, option_desc = x.split()
		return float(strike_str)

	def getSymbol(self, x):
		exp_year, exp_month, strike_str, option_desc = x.split()
		# The symbol begins after the option description opening '(' and
		# continues to the date code. The symbol can be up to 5 characters and
		# can contain numbers.
		symbol_regex = re.compile(r'(\()(\w+)(\d{4}\w{1})')
		regex_results = symbol_regex.search(option_desc)
		symbol = regex_results.group(2)

		if symbol not in self.symbols:
			self.symbols.append(symbol)

		return symbol

	def getExchange(self, x):
		# The exchange is in the description string and right after a hyphen
		# and before the closing ')'. Sometimes the is no exchange and no
		# hyphen. Example option description string: 18 Jan 57.00
		# (SMH1819A57-8)
		# (SMH1819A57)
		exchange = x.split('-')
		if len(exchange) > 1:
			return exchange[-1][0]
		else:
			return ''

	def getDescription(self, x):
		description = x.split('(')
		return description[1][:-1]

	# def getExpirationDate(self, x):
	# 	print x
	# 	new_expiration = x + datetime.timedelta(hours=15, minutes=15)
	# 	print new_expiration

    # def getStrike(self, x):
    #     monthday = x.split()
    #     return float(monthday[2])

    # def getExchange(self, x):
    #     exchange = x.split('-')
    #     if len(exchange) > 1:
    #         return (exchange[-1])[0]
    #     else:
    #         return ''

	def process_data_file(self):

		data = pandas.io.parsers.read_csv(io.StringIO(unicode(self.cboe_data)), sep=',', header=2, na_values=' ')
		data = data.fillna(0.0)

		# Get the Option Expiration Date:
		exp = data.Calls.apply(self.getExpiration)
		exp.name = 'Expiration'

		# Get the Option Strike Price:
		strike = data.Calls.apply(self.getStrike)
		strike.name = 'Strike'

		# Get the Option Exchange:
		exchange = data.Calls.apply(self.getExchange)
		exchange.name = 'Exchange'

		# Get the Option Symbol. This is normally the same as the underlying
		# but can different for weekly, mini options, etc.
		symbol = data.Calls.apply(self.getSymbol)
		symbol.name = 'Symbol'

		

		# data = data.join(exp)
		data = data.join(exp).join(strike).join(exchange).join(symbol)


		# Get expiration date with time
		expiration_date = data.Expiration.apply(self.getExpirationDate)

		# Scrub the option description strings
		calls_desc = data.Calls.apply(self.getDescription)
		data.Calls = calls_desc
		put_desc = data.Puts.apply(self.getDescription)
		data.Puts = put_desc

		# print data.head()
		# print data.tail()
		# print data.columns

		# # Get the Options Expiration Date
	    # exp = data.Calls.apply(self.getExpiration)
	    # exp.name = 'Expiration'

	 #    # Get the Strike Prices
	 #    strike = data.Calls.apply(getStrike)
	 #    strike.name = 'Strike'

	 #    # Get the Exchanges:
	 #    exchange = data.Calls.apply(getExchange)
	 #    exchange.name = 'Exchange'

	 #    data = data.join(exp).join(strike).join(exchange)
		# print data.head()
	 #    # # Get the option type (weekly, monthly, quarterly, mini)
	 #    # option_type = data.Expiration.apply(getOptionType)
	 #    # option_type.name = "OptionType"




if __name__ == "__main__":
	pass
	# import os
	# current_dir = os.getcwd()

	# # filename = "SPY_201605170855.dat"
	# # filename = "SPX_201605170924.dat"
	# # filename = "QuoteData_IWM.dat"
	# filename = "SMH_201605231348.dat"

	# # SPY_201605170855 SPX_201605170924

	# filename_path = current_dir + "/" + filename 
	# # print filename_path

	# cboe_html = open(filename_path)
	# cboe_data = cboe_html.read()
	# # cboe_html.write(html.text.encode('utf-8'))
	# cboe_html.close() 

	# myCBOE_File_Processor = CBOE_File_Processor()
	# underlying_data = myCBOE_File_Processor.get_underlying_info(cboe_data)

	# print underlying_data
	# # for key in underlying_data.keys():
	# # 	print key + "\t\tvalue: " + str(underlying_data[key]) + "\t\ttype: " + str(type(underlying_data[key]))

	# # filename = underlying_data['symbol']
	# # filename += "_"
	# # filename += underlying_data['timestamp'].strftime("%Y%m%d%H%M")
	# # print filename

	# myCBOE_File_Processor.process_data_file()
	# pandas.show_versions()

	# print myCBOE_File_Processor.symbols
	# print datetime.timedelta(days=365).total_seconds()
