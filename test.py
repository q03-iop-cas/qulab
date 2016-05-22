# -*- coding: utf-8 -*-
from qulab import open_lab
import os, sys
import time, datetime
import numpy as np
import logging
from scipy.interpolate import interp1d

Lab = open_lab()

logger = logging.getLogger('main')


READOUT = 110000
READOUT_LEN = 20
awg = Lab.open_instr('AWG', 'TCPIP::10.122.7.100')
#awg.set_timeout(5)
size, _ = awg.get_current_waveforms()

mask     = lambda wav: ''.join(list(map(lambda x: '0' if x==0 else '1',wav)))
mark_or  = lambda a,b: ''.join(list(map(lambda x,y: '1' if x=='1' or y=='1' else '0',a,b)))
mark_and = lambda a,b: ''.join(list(map(lambda x,y: '0' if x=='0' or y=='0' else '1',a,b)))

t = np.arange(0,size,1)

readout = np.array([0]*READOUT + [1]*READOUT_LEN + [-1]*(size-READOUT-READOUT_LEN))
mk = mask(readout)
awg.update_waveform(readout, 'Z', mk, mk)
awg.setValue('Vpp', 2.0, channel=1)

readout = np.array([0]*READOUT + [1]*READOUT_LEN + [-1]*(size-READOUT-READOUT_LEN))
mk = mask(readout)
awg.update_waveform(readout, 'X', mk, mk)
awg.setValue('Vpp', 2.0, channel=2)

readout = np.array([0]*READOUT + [1]*READOUT_LEN + [-1]*(size-READOUT-READOUT_LEN))
mk = mask(readout)
awg.update_waveform(readout, 'Y', mk, mk)
awg.setValue('Vpp', 2.0, channel=3)
