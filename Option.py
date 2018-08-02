import pandas as pd
import math

class Option(object):

  def __init__(self, 
              expiration,
              strike,
              bid,
              ask,
              description,
              exchange):
  
    self.expiration = expiration
    self.strike = strike
    self.bid = bid
    self.ask = ask
    self.description = description
    self.exchange = exchange

    self.sigma = None
    self.delta = None
    self.gamma = None
    self.vega = None
    self.theta = None

    self.positions = None
    self.entry_price = None

    self.payoff_method = None
  
  def my_copy(self):
    new_option = Option(
                  expiration=self.expiration,
                  strike=self.strike,
                  bid=self.bid,
                  ask=self.ask,
                  description=self.description,
                  exchange=self.exchange)

    new_option.sigma = self.sigma
    new_option.delta = self.delta
    new_option.gamma = self.gamma
    new_option.vega = self.vega
    new_option.theta = self.theta

    new_option.positions = self.positions
    new_option.entry_price = self.entry_price

    new_option.payoff_method = self.payoff_method

    return new_option

  def set_positions(self, positions):
    self.positions = positions 
    if positions > 0:
      self.entry_price = -self.ask
    else:
      self.entry_price = self.bid 

    return self

  def set_payout_method(self, payout_method):
    self.payoff_method = payout_method

    return self

  def payouts(self, spots):
    return self.payoff_method(self, spots) 

  def valid(self):
    bid_ok = False
    ask_ok = False
    bid_ask_ok = False

    if self.bid > 0:
      bid_ok = True

    if self.ask > 0:
      ask_ok = True

    if self.bid < self.ask:
      bid_ask_ok = True

    if (bid_ok & ask_ok & bid_ask_ok):
      return self
    else:
      return None

def call_option_payout(option_obj, spots):
  break_even = option_obj.strike + math.fabs(option_obj.entry_price)
  slope = (-1.0 * option_obj.entry_price) / (break_even - option_obj.strike)
  offset = -1.0 * slope * break_even

  payouts = pd.Series(data=None, index=spots.index)
  payouts[spots <= option_obj.strike] = option_obj.entry_price
  payouts[spots > option_obj.strike] = slope * spots[spots > option_obj.strike] + offset

  return payouts

def put_option_payout(option_obj, spots):
  break_even = option_obj.strike - math.fabs(option_obj.entry_price)
  slope = (option_obj.entry_price) / (option_obj.strike - break_even)
  offset = -1.0 * slope * break_even

  payouts = pd.Series(data=None, index=spots.index)
  payouts[spots >= option_obj.strike] = option_obj.entry_price
  payouts[spots < option_obj.strike] = slope * spots[spots < option_obj.strike] + offset

  return payouts
        
# class CallPayout (Option):
#   def __init__(self, 
#               expiration,
#               strike,
#               price,
#               positions):
      
#     Option.__init__(self=self,
#                     expiration=expiration,
#                     strike=strike,
#                     price=price,
#                     positions=positions)

#     self.break_even = self.set_break_even()
#     self.slope = self.set_slope()
#     self.offset = self.set_offset()
      
#   def set_break_even(self):
#     return self.strike + math.fabs(self.price)

#   def set_slope(self):    
#     return (-1.0 * self.price) / (self.break_even - self.strike)
      
#   def set_offset(self):
#     return -1.0 * self.slope * self.break_even

#   def payout(self, spots):
#     # spots is a pandas series 
#     payouts = pd.Series(data=None, index=spots.index)    
#     payouts[spots <= self.strike] = self.price
#     payouts[spots > self.strike] = self.slope * spots[spots > self.strike] + self.offset
    
#     return payouts
    
# class PutPayout (Option):
#   def __init__(self, 
#               expiration,
#               strike,
#               price,
#               positions):

        
#     Option.__init__(self=self,
#                     expiration=expiration,
#                     strike=strike,
#                     price=price,
#                     positions=positions)

#     self.break_even = self.set_break_even()
#     self.slope = self.set_slope()
#     self.offset = self.set_offset()
        
#   def set_break_even(self):
#     return self.strike - math.fabs(self.price)
  
#   def set_slope(self):    
#     return (self.price) / (self.strike - self.break_even)
      
#   def set_offset(self):
#     return -1.0 * self.slope * self.break_even
  
#   def payout(self, spots):
#     # spots is a pandas series 
#     payouts = pd.Series(data=None, index=spots.index)    
#     payouts[spots >= self.strike] = self.price
#     payouts[spots < self.strike] = self.slope * spots[spots < self.strike] + self.offset
    
#     return payouts


