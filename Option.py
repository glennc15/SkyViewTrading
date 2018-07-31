import pandas as pd
import math

class Option (object):

  def __init__(self, 
              expiration,
              strike,
              price,
              positions):
  
    self.expiration = expiration
    self.strike = strike
    self.positions = positions # if positions is negative => short, if positive => long
    self.price = self.set_price(price)
      
  def set_price(self, price):
    # correct way to enter price is negative for along position
    # and positive for a short position.
    # However, sometime I always enter a positve number due to not paying attention.
    # So if positions is negative (short position) the ensure price is positive 
    # and vice versa
    
    if self.positions < 0: # short position => price is positive
        price = math.fabs(price)
    else: # long position => price is negative
        price = math.fabs(price) * -1.0
    
    return price
        
class CallPayout (Option):
  def __init__(self, 
              expiration,
              strike,
              price,
              positions):
      
    Option.__init__(self=self,
                    expiration=expiration,
                    strike=strike,
                    price=price,
                    positions=positions)

    self.break_even = self.set_break_even()
    self.slope = self.set_slope()
    self.offset = self.set_offset()
      
  def set_break_even(self):
    return self.strike + math.fabs(self.price)

  def set_slope(self):    
    return (-1.0 * self.price) / (self.break_even - self.strike)
      
  def set_offset(self):
    return -1.0 * self.slope * self.break_even

  def payout(self, spots):
    # spots is a pandas series 
    payouts = pd.Series(data=None, index=spots.index)    
    payouts[spots <= self.strike] = self.price
    payouts[spots > self.strike] = self.slope * spots[spots > self.strike] + self.offset
    
    return payouts
    
class PutPayout (Option):
  def __init__(self, 
              expiration,
              strike,
              price,
              positions):

        
    Option.__init__(self=self,
                    expiration=expiration,
                    strike=strike,
                    price=price,
                    positions=positions)

    self.break_even = self.set_break_even()
    self.slope = self.set_slope()
    self.offset = self.set_offset()
        
  def set_break_even(self):
    return self.strike - math.fabs(self.price)
  
  def set_slope(self):    
    return (self.price) / (self.strike - self.break_even)
      
  def set_offset(self):
    return -1.0 * self.slope * self.break_even
  
  def payout(self, spots):
    # spots is a pandas series 
    payouts = pd.Series(data=None, index=spots.index)    
    payouts[spots >= self.strike] = self.price
    payouts[spots < self.strike] = self.slope * spots[spots < self.strike] + self.offset
    
    return payouts

