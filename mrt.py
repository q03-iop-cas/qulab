# -*- coding: utf-8 -*-
from qulab import open_lab
import os, sys
import time, datetime
import numpy as np
import logging
from scipy.interpolate import interp1d

Lab = open_lab()

def V2Phi(V):
    x = [-4.235,-0.458,3.314]
    y = [-0.5,0.5,1.5]
    f = np.poly1d(np.polyfit(x,y,2))
    return f(V)

def Phi2V(p):
    x = [-4.235,-0.458,3.314]
    y = [-0.5,0.5,1.5]
    r = np.polyfit(x,y,2)
    r[2] = r[2] - p
    sol = np.roots(r)
    return np.round((sol[(sol > -5)*(sol < 5)])[0], 3)

class SQUID_Bais():
    def __init__(self):
        self.t = np.array([0,  5, 5.5, 8.5,   9, 9.8,  10])
        self.y = np.array([0,  0, 1.5, 2.1,  -1,   0,   0])

    def gen(self, n):
        t = np.linspace(0,1,n+1)
        x = (self.t-self.t[0])/(self.t[-1]-self.t[0])
        return interp1d(x, self.y)(t[:-1])

    def set_zero(self, v):
        for i in [0, 1, 5, 6]:
            self.y[i] = v

class Flux_Bais():
    def __init__(self):
        self.t = np.array([0, 0.1,   2, 4.5, 4.6,   9, 9.5, 10])
        self.y = np.array([0,   0, 0.7, 0.7, 0.5, 0.5,   0,  0])
        self.y2 = np.array(list(map(Phi2V, self.y)))

    def gen(self, n):
        t = np.linspace(0,1,n+1)
        x = (self.t-self.t[0])/(self.t[-1]-self.t[0])
        f = interp1d(x, self.y2)
        def func(t):
            if t < x[1] or t > x[2]:
                return f(t)
            else:
                high = f(x[2])
                low = f(x[0])
                return (high-low)*0.5*(1-np.cos(np.pi*(t-x[1])/(x[2]-x[1]))) + low
        return np.array(list(map(func, t)))

    def set_Phi(self, p):
        phiV = Phi2V(p)
        for i in [2, 3]:
            self.y2[i] = phiV
        return phiV, V2Phi(phiV)

squid_wav = SQUID_Bais()
bais_wav = Flux_Bais()

logger = logging.getLogger('main')

logger.info('MRT Start')

Lab.open_instr('counter', 'GPIB1::13')
Lab.instr['counter'].set_timeout(25)
Lab.open_instr('squid_sour', 'GPIB1::20')
#Lab.instr['squid_sour'].setValue('Waveform', value=squid_wav.gen(2000))
#Lab.instr['squid_sour'].setValue('Frequency', 4e3)
Lab.instr['squid_sour'].set_trigger('EXT')
Lab.open_instr('bais_sour', 'GPIB1::11')
#Lab.instr['bais_sour'].setValue('Waveform', value=bais_wav.gen(2000))
#Lab.instr['bais_sour'].setValue('Frequency', 4e3)
Lab.instr['bais_sour'].set_trigger('EXT')

from qulab.utils import get_threshold, get_probility

n = 5000
fluxRange = np.arange(0.7,0.8,0.005)

header = '''{datatype} --- generated by {program} {version} <{time}>

Flux Bais Range : from {Fstart} to {Fstop} step {Fstep}
Points for Every Bais : {npoints}

+-----------+-------+-----------+
| Flux Bais | Flux  | Probility |
+-----------+-------+-----------+
| V         | Phi_0 |           |
+-----------+-------+-----------+
'''.format(
    datatype = 'MRT',
    program = sys.argv[0],
    version = 'v0.1',
    time = datetime.datetime.now(),
    Fstart = fluxRange[0],
    Fstop  = fluxRange[-1],
    Fstep  = fluxRange[1]-fluxRange[0],
    npoints = n
)

v = []
x = []
y = []
for f in fluxRange:
    V, flux = bais_wav.set_Phi(f)
    Lab.instr['bais_sour'].setValue('Waveform', bais_wav.gen(2000), freq=4e3)
    Lab.instr['squid_sour'].refresh()
    #Lab.instr['bais_sour'].refresh()
    time.sleep(1)
    data = np.array(Lab.instr['counter'].getValue('Datas', count=n))
    data = data[(data>0.125e-3)*(data<0.25e-3)]
    #threshold = get_threshold(data)
    threshold = 0.167e-3
    #P = 1.0*len(data[data > threshold])/len(data)
    P, E, std, (low, high) = get_probility(len(data[data > threshold]), len(data))
    print('Flux : %f (%f V), Probility : %f, low : %f, high : %f' % (flux, V, P, low, high))
    v.append(V)
    x.append(flux)
    y.append(P)

import numpy as np
import matplotlib.pyplot as plt

x = np.array(x)
y = np.array(y)

Lab.savetxt('MRT', np.array([v,x,y]).T, header=header)
logger.info('MRT Finished')

plt.plot(x, y)
plt.show()
