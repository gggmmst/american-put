from pde import AmericanPut

class GreeksException(Exception):
    pass

class Greeks(object):

    def __init__(self, pricer):
        self.pricer = pricer
        # compute dS
        self.S = S = pricer.S
        self.dS = dS = S[1:]-S[:-1]
        self.dS_minus_half = dS[:-1]
        self.dS_plus_half = dS[1:]
        # compute dU
        self.U = U = pricer.soln
        self.dU = dU = U[1:]-U[:-1]
        self.dU_minus_half = dU[:-1]
        self.dU_plus_half = dU[1:]

    def delta(self, position='central'):
        try:
            d = dict(central  = lambda : self.dU / self.dS,
                     forward  = lambda : self.dU_plus_half / self.dS_plus_half,
                     backward = lambda : self.dU_minus_half / self.dS_minus_half)[position]
        except KeyError:
            errmsg = "delta position argument must be one of ['central', 'forward', 'backward']"
            raise GreeksException(errmsg)
            print errmsg        # XXX log.error instead of stdout print
        else:
            return d()

    def gamma(self):
        d1 = self.delta('forward')
        d2 = self.delta('backward')
        c  = .5 * (self.dS_plus_half + self.dS_minus_half)
        return (d1-d2)/c

##
## quick test
##

def test():

    # BS parameters
    rate             = .01
    sigma            = .3
    strike           = 100.
    init_value       = 100.
    time_to_maturity = 1.

    # compute option object
    option = AmericanPut(rate, sigma, strike, init_value, time_to_maturity)
    option.solve(-1)    # use fully implicit scheme

    # compute greeks
    g = Greeks(option)
    print g.delta('forward')
    print g.gamma()

if __name__ == '__main__':
    test()
