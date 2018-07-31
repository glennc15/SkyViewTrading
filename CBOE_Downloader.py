import bs4, requests, os
import CBOE_File_Processor
import re
from urllib.parse import unquote

class CBOE_Downloader(object):
	pass
	def __init__(self, symbol):
		self.symbol = symbol
		self.cboe_data = None
		self.path = None
		self.filename = None
		self.status_code = None

	def download(self):
		# cboe_url = "http://www.cboe.com/delayedquote/QuoteTableDownload.aspx"
		cboe_url = "http://www.cboe.com/delayedquote/quote-table-download"
		header_info = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36",}

		# Use a session to keep track of cookies, etc.
		cboe_session = requests.Session()

		# Download QuoteTableDownload.aspx because it has some hidden values that
		# have to be POSTed along with the symbol to be able to download a
		# QuoteData.dat file.
		cboe_html = cboe_session.get(cboe_url, headers=header_info)
		self.status_code = cboe_html.status_code

		# Continue if successfully got QuoteTableDownload.aspx
		assert cboe_html.status_code == 200, "Error during GET request, status code: {}".format(cboe_html.status_code)

		# Extract the require POST data values from the QuoteTableDownload.aspx
		# file
		post_data = self.get_POST_params(cboe_html.text)
		# Make a POST request to
		# http://www.cboe.com/delayedquote/QuoteTableDownload.aspx using the POST
		# data.  Have to add the referer URL or the request will be rejected.
		header_info["Referer"] = "http://www.cboe.com/delayedquote/quote-table-download"			
		post_request = cboe_session.post(cboe_url, data=post_data, headers=header_info)
		self.status_code = post_request.status_code
		assert post_request.status_code == 200, "Error during POST request, status code: {}".format(post_request.status_code)


		self.cboe_data = post_request.text

		return self
	
	def save_download(self):
		# Use CBOE_File_Processor to parse the data file for the underlying
		# info. The underlying info is used to construct the filename.

		file_processor = CBOE_File_Processor.CBOE_File_Processor()
		underlying_data = file_processor.get_underlying_info(self.cboe_data)

		self.filename = underlying_data['symbol']
		self.filename += "_"
		self.filename += underlying_data['timestamp'].strftime("%Y%m%d%H%M")
		self.filename += ".dat"

		# current_dir = os.getcwd()
		# 
		if os.path.exists("/Users/glenn/Documents/CBOE_Data"):
			self.path = "/Users/glenn/Documents/CBOE_Data"
		if os.path.exists("/home/glenn/Documents/CBOE_Data"):
			self.path = "/home/glenn/Documents/CBOE_Data"
		# self.path = "/home/glenn/Docu"
		filename_path = self.get_filename() 
		cboe_html = open(filename_path, "w")
		cboe_html.write(self.cboe_data)
		cboe_html.close()

		return self

	def get_filename(self):
		return os.path.join(self.path, self.filename)

	def get_POST_params(self, cboe_html):
		# This is the data that CBOE requires to be POSTed to get a data file.
		cboe_post_data = {
			"ctl05_TSM": '',
			"ctl06_TSSM": '',

			"__EVENTTARGET": '',
			"__EVENTARGUMENT": '',
			"__VIEWSTATE": '',
			"__VIEWSTATEGENERATOR": '',
			"__EVENTVALIDATION": '',
			"ctl00$ctl05": '',
			"SearchQuery": '',
			"ctl00$ContentTop$C005$txtTicker": self.symbol.upper(),
			"ctl00$ContentTop$C005$cmdSubmit": "Download"}
			# "ctl00$ctl00$AllContent$ContentMain$QuoteTableDownloadCtl1$txtTicker": self.symbol.upper(),
			# "ctl00$ctl00$AllContent$ContentMain$QuoteTableDownloadCtl1$cmdSubmit": "Download"}
		
		# These are ids of hidden input tags whos values must be entered into
		# cboe_post_data
		cboe_html_input_ids = ["__EVENTTARGET", 
			"__EVENTARGUMENT",
			"__VIEWSTATE", 
			"__VIEWSTATEGENERATOR",
			"__EVENTVALIDATION"]

		# Go through each input tag and if it's id is in cboe_html_input_ids then
		# save it's value to cboe_post_data
		cboe_html_bs4 = bs4.BeautifulSoup(cboe_html, 'lxml')
		for input_tag in cboe_html_bs4.select('input'):
			current_id = input_tag.attrs['id']
			if current_id in cboe_html_input_ids:
				cboe_post_data[current_id] = input_tag.attrs['value']

		# find the value for ctl06_TSSM.  It's located in <script
		# type="text/javascript"> tag under hf.value += '[WHAT WE WANT IS BETWEEN
		# THESE SINGLE QUOTES]';
		
		# get position of $get('ctl06_TSSM');
		start_index = cboe_html.find("$get('ctl06_TSSM');")
		end_index = start_index + 500 # 500 was found by trial and error.

		# print "start_index: %s" % start_index
		# print cboe_html[start_index:end_index]

		ctl06_regex = re.compile(r"hf.value \+= '(.+)'")
		ctl06_regex_results = ctl06_regex.search(cboe_html[start_index:end_index])

		cboe_post_data["ctl06_TSSM"] = str(ctl06_regex_results.group(1))
		


		# find the value for ctl05_TSM.  Not good pattern.  Begins with
		# %3b%3bSystem.Web.Extension ... and goes on until " type' 
		
		# The %3b%3b is url encoded nonsense and has to be decoded with urllib
		# unquote()

		ctl005_regex = re.compile(r'(%3b%3bSystem.Web.Extensions.+)" type')
		ctl005_regex_results = ctl005_regex.search(cboe_html)
		ctl005_value = str(unquote(ctl005_regex_results.group(1)))
		cboe_post_data["ctl05_TSM"] = ctl005_value
		
		return cboe_post_data

	def print_POST_parameters(self, post_parameters):
		
		partial_value_len = 25

		for key in post_parameters.keys():
			this_value = post_parameters[key]
			if len(this_value) > 100:
				first_part = this_value[:partial_value_len]
				last_part = this_value[-partial_value_len:]
			else:
				first_part = this_value
				last_part = None

			if last_part:
				print("%s: %s... + ...%s" % (key, first_part, last_part))
			else:
				print("%s: %s" % (key, first_part))


if __name__ == "__main__":
	pass
			
	# import os
	# current_dir = os.getcwd()
	# filename = "QuoteData_SPY.dat"
	# # filename = "QuoteData_IWM.dat"
	# filename_path = current_dir + "/" + filename 
	# # print filename_path

	# cboe_html = open(filename_path)
	# cboe_data = cboe_html.read()
	# cboe_html.close()

	# print os.path.exists("/Users/glenn/Documents/CBOE_Data")
	# print os.path.exists("/home/glenn/Documents/CBOE_Data")
	
	# Original tests
	# myCBOE_Downloader = CBOE_Downloader('SPX')
	# myCBOE_Downloader.download()
	# myCBOE_Downloader.save_download()






