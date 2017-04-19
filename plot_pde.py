from functools import partial

# numerical lib
import numpy as np
import pandas as pd
from numpy import unique, hstack, linspace

# plotting lib
import matplotlib.pyplot as plt
plt.style.use('ggplot')

from pde import AmericanPut

# model parameters
rate             = .001
sigma            = .37
strike           = 99.
init_value       = 100.25
unit_grid = hstack((linspace(0  , .4 , 50 , endpoint=False),
                    linspace(.4 , .8 , 80 , endpoint=False),
                    linspace(.8 , .9 , 80 , endpoint=False),
                    linspace(.9 , 1.1, 200, endpoint=False),
                    linspace(1.1, 1.2, 80 , endpoint=False),
                    linspace(1.2, 1.6, 80 , endpoint=False),
                    linspace(1.6, 2  , 50 , endpoint=False),
                    linspace(2  , 5  , 50)))
strikes = strike * unit_grid

# lambda currying
# optionT := AmericanPut with all parameters fixed except *time_to_maturity*
optionT = lambda t: AmericanPut(rate, sigma, strike, init_value, t, unit_grid=unit_grid)

# now fill in time_to_maturity
a1 = optionT(1./12)
a2 = optionT(2./12)
a3 = optionT(3./12)
a6 = optionT(6./12)
a12 = optionT(1.)

# prepare dataframe
payoff = a1.payoff
data = {'payoff'     : payoff,
        'put (T=1m)' : a1.soln,
        'put (T=2m)' : a2.soln,
        'put (T=3m)' : a3.soln,
        'put (T=6m)' : a6.soln,
        'put (T=1y)' : a12.soln}
df = pd.DataFrame(data, index=strikes)
# focus on (interesting) area near strike
df = df[(df.index >= 40) & (df.index < 200)]

# make plot
df.plot()
title = 'American put value\n(r={}, sigma={}, strike={}, S0={})'.format(rate, sigma, strike, init_value)
plt.title(title)
plt.xlabel('strikes')
plt.ylabel('option value')
plt.show()
