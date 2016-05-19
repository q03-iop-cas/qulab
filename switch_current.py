# -*- coding: utf-8 -*-
import numpy as np
#{{{
counter_addr = 'GPIB1:13'
squid_I_addr = 'GPIB1:20'
npoints = 5000
threshold = 1.2e-4
R = 1.01e6

def waveform(t):
    return 12*t-5
#}}}

from qulab import OpenLab
from qulab.utils import get_probility

Lab = OpenLab()

table_header = '''
+-------------+-------------+----------------+
| Switch time | Switch Volt | Switch current |
+-------------+-------------+----------------+
|      ms     |      V      |       ms       |
+-------------+-------------+----------------+
'''
t = np.linspace(0,1,2000)*0.25e-3
counter = Lab.open_instr(counter_addr)
squid_bais = Lab.open_instr(squid_I_addr)
squid_bais.setValue('Waveform', waveform(t))
t = counter.getValue('Datas')
Lab.save([1e3*t, waveform(t), waveform(t)/R], header=table_header)

N = len(t)
x = len(t[t>threshold])
P, _, _, (down_bond, up_bond) = get_probility(x, N)
