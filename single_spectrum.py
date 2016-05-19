# -*- coding: utf-8 -*-
import numpy as np
#{{{
counter_addr = 'GPIB1:13'
ex_mw_addr = 'TCPIP:10.122.7.101'
npoints = 5000
freqs = np.linspace(5.9,6.1,201)*1e9
#}}}

from qulab import OpenLab

Lab = OpenLab()
ex_mw = Lab.open_instr(ex_mw_addr)

PI = Lab.load_script('switch_current')
PI.setValue('counter_addr', counter_addr)
PI.setValue('npoints', npoints)

table_header = '''
+-----------+---------+-----------+---------+
| Frequency |    P    | Down Bond | Up Bond |
+-----------+---------+-----------+---------+
|    GHz    |         |           |         |
+-----------+---------+-----------+---------+
'''

for f in freqs:
    ex_mw.setValue('Frequency', f)
    P, down_bond, up_bond = PI.get('P', 'down_bond', 'up_bond')
    Lab.save([1e-9*f, P, down_bond, up_bond], header=table_header)
