# numerical lib
import numpy as np
from numpy import hstack, linspace
import pandas as pd

# plotting lib
import matplotlib.pyplot as plt
plt.style.use('ggplot')

from pde import AmericanPut
from greeks import Greeks

# BS parameters
rate             = .001
sigma            = .37
strike           = 99.
init_value       = 100.25
unit_grid = hstack((linspace(0  , .4 , 100, endpoint=False),
                    linspace(.4 , .8 , 200, endpoint=False),
                    linspace(.8 , .9 , 200, endpoint=False),
                    linspace(.9 , 1.1, 400, endpoint=False),
                    linspace(1.1, 1.2, 200, endpoint=False),
                    linspace(1.2, 1.6, 200, endpoint=False),
                    linspace(1.6, 2  , 100, endpoint=False),
                    linspace(2  , 5  , 100)))

# lambda currying
# optionT := AmericanPut with all parameters fixed except *time_to_maturity*
optionT = lambda t: AmericanPut(rate, sigma, strike, init_value, t, unit_grid=unit_grid)

# now fill in time_to_maturity
# call solve(-1) explicitly to ensure solver to run fully implicit scheme
a1 = optionT(1./12)
a1.solve(-1)
a2 = optionT(2./12)
a2.solve(-1)
a3 = optionT(3./12)
a3.solve(-1)
a6 = optionT(6./12)
a6.solve(-1)
a12 = optionT(1.)
a12.solve(-1)

# compute greeks
g1 = Greeks(a1)
g2 = Greeks(a2)
g3 = Greeks(a3)
g6 = Greeks(a6)
g12 = Greeks(a12)

strikes = a1.S[1:-1]

def plot_delta():
    data = {'delta (T=1m)' : g1.delta('forward'),
            'delta (T=2m)' : g2.delta('forward'),
            'delta (T=3m)' : g3.delta('forward'),
            'delta (T=6m)' : g6.delta('forward'),
            'delta (T=1y)' : g12.delta('forward')}
    df = pd.DataFrame(data, index=strikes)
    df = df[(df.index >= 40) & (df.index < 200)]

    df.plot()
    plt.title('Delta\n(r={}, sigma={}, strike={}, S0={})'.format(rate, sigma, strike, init_value))
    plt.xlabel('strikes')
    plt.ylabel('value')
    plt.show()

def plot_gamma():
    data = {'gamma (T=1m)' : g1.gamma(),
            'gamma (T=2m)' : g2.gamma(),
            'gamma (T=3m)' : g3.gamma(),
            'gamma (T=6m)' : g6.gamma(),
            'gamma (T=1y)' : g12.gamma()}
    df = pd.DataFrame(data, index=strikes)
    df = df[(df.index >= 40) & (df.index < 200)]

    df.plot()
    plt.title('Gamma\n(r={}, sigma={}, strike={}, S0={})'.format(rate, sigma, strike, init_value))
    plt.xlabel('strikes')
    plt.ylabel('value')
    plt.show()

if __name__ == '__main__':
    import sys
    t = sys.argv[1]
    f = {'delta': plot_delta, 'gamma': plot_gamma}[t]
    f()
