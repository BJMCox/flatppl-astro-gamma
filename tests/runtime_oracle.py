"""Independent SciPy integrals and analytic runtime Jacobians; no FlatPPL calls."""
import math

import numpy as np
from scipy.integrate import quad

POINTS = [[2.1, 1.0, 0.2, 4.0, 1.3, 0.8, 1.25],
          [1.7, 1.0-1e-10, -0.1, 3.0, 0.8, 0.0, 0.9],
          [0.8, 1.0+1e-10, 0.4, 5.0, 2.0, 1.2, 1.1],
          [1.2, 2.7, 0.1, 2.0, 1.5, 0.6, 1.0]]


def oracle(x):
    amplitude, index, curvature, cutoff, power, ebl, scale = x
    loge = math.log(2/1.3)
    differential = amplitude*(2/1.3)**(-index)
    logparabola = differential*math.exp(-curvature*loge**2)
    cutoff_flux = differential*math.exp(-(2/cutoff)**power+(1.3/cutoff)**power)
    integrals, derivatives = [], []
    for moment, offset in [(0,0), (1,1)]:
        flux = lambda e: e**moment*amplitude*(e/1.3)**(-(index+offset))
        integrals.append(quad(flux, .4, 5, epsabs=1e-10, epsrel=2e-13)[0])
        derivatives.append(quad(lambda e: -math.log(e/1.3)*flux(e), .4, 5, epsabs=1e-10, epsrel=2e-13)[0])
    energy = np.array([.5,1,2])
    optical_depth = np.array([.05,.2,.5])
    factors = energy/1.3
    true = 4*np.array([1,2,3])*amplitude*factors**(-index)*np.exp(-ebl*optical_depth)*[.5,.75,1]
    migration = np.array([[.7,.2,0],[.1,.6,.7]])
    source = migration @ true
    values = np.array([differential,logparabola,cutoff_flux,*integrals,math.exp(-.7*ebl),*source,2/cutoff,.5/scale])
    jac = np.zeros((10,7))
    jac[:5,0] = values[:5]/amplitude
    jac[:3,1] = -loge*values[:3]
    jac[1,2] = -loge**2*logparabola
    jac[2,3] = power/cutoff*((2/cutoff)**power-(1.3/cutoff)**power)*cutoff_flux
    jac[2,4] = (-(2/cutoff)**power*math.log(2/cutoff)+(1.3/cutoff)**power*math.log(1.3/cutoff))*cutoff_flux
    jac[3:5,1] = derivatives
    jac[5,5] = -.7*values[5]
    jac[6:8,0] = source/amplitude
    jac[6:8,1] = migration @ (-np.log(factors)*true)
    jac[6:8,5] = migration @ (-optical_depth*true)
    jac[8,3] = -2/cutoff**2
    jac[9,6] = -.5/scale**2
    return values, jac
