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

logger.info('MRT0 Start')

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
awg = Lab.open_instr('AWG', 'TCPIP::10.122.7.100')
mw  = Lab.open_instr('ExMW', 'TCPIP::10.122.7.101')


mask     = lambda wav: ''.join(list(map(lambda x: '0' if x==0 else '1',wav)))
mark_or  = lambda a,b: ''.join(list(map(lambda x,y: '1' if x=='1' or y=='1' else '0',a,b)))
mark_and = lambda a,b: ''.join(list(map(lambda x,y: '0' if x=='0' or y=='0' else '1',a,b)))

from qulab.utils import get_threshold, get_probility

fit_readout = np.poly1d([-50.17857, 37.97214])

threshold = 0.055e-3
READOUT = 110000
READOUT_LEN = 20
n = 5000
vRange = np.arange(5.95, 5.98, 0.0001)*1e9
bais = 0.71

SIZE, _ = awg.get_current_waveforms()
readout = np.array([0]*READOUT + [1]*READOUT_LEN + [-1]*(SIZE-READOUT-READOUT_LEN))
mk = mask(readout)
awg.update_waveform(readout, 'Z', mk, mk)
awg.setValue('Vpp', 2.0, channel=1)
V, flux = bais_wav.set_Phi(bais)
Lab.instr['bais_sour'].setValue('Waveform', bais_wav.gen(2000), freq=4e3)

header = '''{datatype} --- generated by {program} {version} <{time}>

Points for Every Bais : {npoints}

+-----------+-------+-----------+
| Flux Bais | Flux  | Probility |
+-----------+-------+-----------+
| V         | Phi_0 |           |
+-----------+-------+-----------+
'''.format(
    datatype = 'MRT0',
    program = sys.argv[0],
    version = 'v0.1',
    time = datetime.datetime.now(),
    npoints = n
)

readout_vpp = fit_readout(bais)
awg.setValue('Vpp', readout_vpp, channel=1)

x = np.array([1]*READOUT + [0]*(SIZE-READOUT))
mkx = mask(x)
awg.update_waveform(x, 'X', mkx, mkx)
y = np.array([0]*READOUT + [0]*(SIZE-READOUT))
mky = mask(y)
mk = mark_or(mkx, mky)
awg.update_waveform(y, 'Y', mk, mk)

mw.setValue('Output', 'ON')
mw.setValue('Power', -35)

x = []
y = []

Lab.instr['squid_sour'].refresh()
Lab.instr['bais_sour'].refresh()
last = time.clock()

for f in vRange:
    mw.setValue('Frequency', f)
    now = time.clock()
    if now - last > 120:
        Lab.instr['squid_sour'].refresh()
        Lab.instr['bais_sour'].refresh()
        time.sleep(1)
        last = time.clock()
    data = np.array(Lab.instr['counter'].getValue('Datas', count=n))
    data = data[(data>4e-5)*(data<7.3e-5)]
    #threshold = get_threshold(data)
    #P = 1.0*len(data[data > threshold])/len(data)
    P, E, std, (low, high) = get_probility(len(data[data > threshold]), len(data))
    print('Frequency : %f (GHz), Probility : %f, low : %f, high : %f' % (f*1e-9, P, low, high))
    x.append(f)
    y.append(P)
mw.setValue('Output', 'OFF')

import numpy as np
import matplotlib.pyplot as plt

x = np.array(x)
y = np.array(y)

Lab.savetxt('MRT0', np.array([x,y]).T, header=header)
logger.info('MRT0 Finished')

plt.plot(x, y)
plt.show()
