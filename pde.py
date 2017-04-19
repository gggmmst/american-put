#!/usr/bin/python

from itertools import izip
from numpy import (
    arange,
    array,
    fmax,
    hstack,
    linspace,
    ones,
    unique,
    zeros,
)
import numpy
from scipy.sparse.linalg import dsolve
from scipy import sparse
from scipy.interpolate import interp1d


_abs = numpy.abs
_diags = sparse.diags
_spsolve = dsolve.spsolve


##########################################

class AmericanPut(object):

    # symbol | meaning
    # ------ | -------
    # sigma  | constant volatility of underlying
    # r      | risk-free rate
    # T      | time to maturity
    # K      | strike value
    # S0     | underlying initial value
    # N      | a value indirectly determine timestep sizes (see details)
    # S      | a vector, S-grid
    # theta  | Crank-Nicolson scheme (theta = .5), implicit scheme (theta = 0.)
    # tol    | tolerance level

    tol       = 1e-6
    N         = 100           # TODO hard coded value
    _payoff   = None
    _values   = None
    _soln     = None

    # default unit grid
    unit_grid = unique(hstack((linspace(0  , .4 , 20),     # coarser grid when far away from strike
                               linspace(.4 , .8 , 50),
                               linspace(.8 , .9 , 75),
                               linspace(.9 , 1.1, 200),    # finer grid centered around strike
                               linspace(1.1, 1.2, 75),
                               linspace(1.2, 1.6, 50),
                               linspace(1.6, 2  , 20),
                               linspace(2  , 10 , 50))))   # throw in a few far-far-away points, just in case


    def __init__(self, rate, sigma, strike, init_value, time_to_maturity, *a, **kw):
        self.r     = rate
        self.sigma = sigma
        self.K     = strike
        self.S0    = init_value
        self.T     = time_to_maturity
        if kw.has_key('unit_grid'):
            self.unit_grid = kw['unit_grid']
        self.S     = self._grid(strike)


    @property
    def payoff(self):
        if self._payoff is None:
            self._payoff = fmax(self.K-self.S, 0.)
        return self._payoff


    def _grid(self, strike):
        return strike * self.unit_grid


    def _alpha_beta(self, sigma, r, S):
        Sm  = S[:-2]            # S-minus
        Sc  = S[1:-1]           # S-center
        Sp  = S[2:]             # S-plus
        x   = sigma*sigma*Sc*Sc # sigma*sigma*S[i]*S[i]
        Spm = Sp-Sm             # S[i+1]-S[i-1]
        Scm = Sc-Sm             # S[i]-S[i-1]
        Spc = Sp-Sc             # S[i+1]-S[i]

        alpha_central  = x/Scm/Spm - r*Sc/Spm
        beta_central   = x/Spc/Spm + r*Sc/Spm
        alpha_forward  = x/Scm/Spm
        beta_forward   = x/Spc/Spm + r*Sc/Spc
        alpha_backward = x/Scm/Spm - r*Sc/Scm
        beta_backward  = x/Spc/Spm

        # applying the following 2 schemes for alpha/beta's:
        # - upstream weighting scheme
        # - positive cofficient scheme (use central differencing as much as possible)
        z = izip(alpha_central, beta_central, alpha_forward, beta_forward, alpha_backward, beta_backward)
        for (ac, bc, af, bf, ab, bb) in z:
            if (ac>=0) and (bc>=0):
                yield ac, bc
            else:
                if (af>=0) and (bf>=0):
                    yield af, bf
                else:
                    yield ab, bb


    def _M(self, theta, dtau, r, alpha, beta, penalty):
        """
        build left (L) and right (R) matrices of the system
        L = [I + (1-theta)*M + P]
        R = [I - theta*M]
        """
        # shortcuts
        a = alpha
        b = beta

        u    = (1-theta)*dtau
        ml_l = hstack((-u*a, 0))
        ml_m = 1 + hstack((u*r, u*(a+b+r), 0)) + penalty
        ml_u = hstack((0, -u*b))

        v    = theta*dtau
        mr_l = hstack((v*a, 0))
        mr_m = 1 - hstack((v*r, v*(a+b+r), 0))
        mr_u = hstack((0, v*b))

        L = _diags([ml_l, ml_m, ml_u], offsets=[-1, 0, 1])
        R = _diags([mr_l, mr_m, mr_u], offsets=[-1, 0, 1])

        return L, R


    def _solve_space_axis(self, U0, theta, dtau):

        U1 = U0.copy()

        r           = self.r
        payoff      = self.payoff
        tol         = self.tol
        err         = 1. + tol
        large       = 1. / tol
        alpha, beta = map(array, zip(*self._alpha_beta(self.sigma, self.r, self.S)))

        while err >= tol:       # Newton's iterative method: find best estimate for options value at time n

            # penalty (diagonal) vector
            penalty = array([large if v < x else 0. for (v, x) in zip(U1, payoff)])

            # Left and Right matrices for the linear system
            L, R = self._M(theta, dtau, r, alpha, beta, penalty)

            # solve linear system, solution is the estimate of the option values on S-axis
            u = _spsolve(L, (R*U0)+(penalty*payoff))

            # compute (worst) error
            e = abs(u-U1)/fmax(1.,abs(u))
            err = e.max()

            # update estimated values
            U1, u = u, None

        return U1


    def _solve_time_axis(self, rannacher_steps=-1):

        ##
        ## rannacher smoothing(implicit at first, then crank-nicolson), variable timesteps
        ##

        U0              = self.payoff.copy()
        T               = self.T
        rannacher_steps = 2
        tau             = 0.
        dtau            = T/float(self.N)
        D               = 1.
        dnorm           = .1
        n               = 1

        while tau < T:

            tau += dtau
            theta = .5 if n > rannacher_steps else 0
            U1 = self._solve_space_axis(U0, theta, dtau)

            if tau >= T:
                break
            else:
                e = _abs(U1-U0)/fmax(D, fmax(_abs(U1), _abs(U0)))
                emax = e.max()
                dtau *= dnorm/emax
                dtau = min(dtau, self.T-tau)
                n += 1
                U0, U1 = U1, None

        return U1


    def solve(self):
        U = self._solve_time_axis()
        self._values = interp1d(self.S, U, kind='linear')
        # self._soln = zip(self.S, U)
        self._soln = U


    def value_at(self, underlying):
        if self._values is None:
            self.solve()
        return self._values(underlying)


    @property
    def values(self):
        if self._values is None:
            self.solve()
        return self._values


    @property
    def soln(self):
        if self._soln is None:
            self.solve()
        return self._soln


##########################################


def main():

    rate             = .05
    sigma            = .3
    strike           = 100.
    init_value       = 100.
    time_to_maturity = 1.

    option = AmericanPut(rate, sigma, strike, init_value, time_to_maturity)

    # print option.soln
    print option.value_at(strike * .97)
    print option.value_at(strike)
    print option.value_at(strike * 1.03)


if __name__ == '__main__':
    main()
