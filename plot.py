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
rate             = .05
sigma            = .3
strike           = 100.
init_value       = 100.
unit_grid = unique(hstack((linspace(0  , .4 , 20),     # coarser grid when far away from strike
                           linspace(.4 , .8 , 50),
                           linspace(.8 , .9 , 75),
                           linspace(.9 , 1.1, 200),    # finer grid centered around strike
                           linspace(1.1, 1.2, 75),
                           linspace(1.2, 1.6, 50),
                           linspace(1.6, 2  , 20),
                           linspace(2  , 10 , 50))))   # throw in a few far-far-away points, just in case
strikes = strike * unit_grid

# currying by lambda
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
df = df[(df.index >= 50) & (df.index < 200)]

# make plot
df.plot()
plt.title('American put value\n(r=.05, sigma=.3, strike=100, S0=100)')
plt.xlabel('strikes')
plt.ylabel('option value')
plt.show()
