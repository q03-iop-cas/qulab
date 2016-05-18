# -*- coding: utf-8 -*-

#{{{
counter_addr = 'GPIB1:13'
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
counter = Lab.open_instr(counter_addr)
t = counter.getValue('Datas')
Lab.save([1e3*t, waveform(t), waveform(t)/R], header=table_header)

N = len(t)
x = len(t[t>threshold])
P, _, _, (down_bond, up_bond) = get_probility(x, N)
Lab.send(P, down_bond, up_bond)
