# -*- coding: utf-8 -*-
from qulab import open_lab
import os, sys
import time, datetime
import numpy as np
import logging
from scipy.interpolate import interp1d

Lab = open_lab()

class SQUID_Bais():
    def __init__(self):
        self.t = np.array([0,5.1, 5.6, 8.5, 9.4, 9.8,  10])
        self.y = np.array([0,  0, 1.5, 2.1,  -1,   0,   0])

    def gen(self, n):
        t = np.linspace(0,1,n+1)
        x = (self.t-self.t[0])/(self.t[-1]-self.t[0])
        return interp1d(x, self.y)(t[:-1])

    def set_zero(self, v):
        for i in [0, 1, 5, 6]:
            self.y[i] = v

wav = SQUID_Bais()

logger = logging.getLogger('main')

logger.info('QubitStep Start')

Lab.open_instr('counter', 'GPIB1::13')
Lab.instr['counter'].set_timeout(25)
Lab.open_instr('squid_sour', 'GPIB1::20')
Lab.instr['squid_sour'].setValue('Waveform', value=wav.gen(2000))
Lab.instr['squid_sour'].setValue('Frequency', 4e3)
Lab.instr['squid_sour'].set_trigger('EXT')
time.sleep(1)
data=Lab.instr['counter'].getValue('Datas',count=10000)

import matplotlib.pyplot as plt
plt.hist(np.array(data)*1e3,bins=60)
plt.show()
