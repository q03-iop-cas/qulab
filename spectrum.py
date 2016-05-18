# -*- coding: utf-8 -*-
import numpy as np
#{{{
counter_addr = 'GPIB1:13'
ex_mw_addr = 'TCPIP:10.122.7.101'
flux_addr = 'GPIB1:11'
npoints = 5000
flux = np.linspace(7,8,21)
#}}}

from qulab import OpenLab

Lab = OpenLab()
fl_sour = Lab.open_instr(flux_addr)

mw = Lab.load_script('single_spectrum')
mw.setValue('counter_addr', counter_addr)
mw.setValue('npoints', npoints)

table_header = '''
+-----------+---------+-----------+---------+
| Frequency |    P    | Down Bond | Up Bond |
+-----------+---------+-----------+---------+
|    GHz    |         |           |         |
+-----------+---------+-----------+---------+
'''

for f in flux:
    fl_sour.setValue('Flux', f)
    freq, P, down_bond, up_bond = mw.recv()
    Lab.save([f, freq, P], header=table_header)
Lab.send_data()
