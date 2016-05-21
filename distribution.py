# -*- coding: utf-8 -*-
from qulab import open_lab

Lab=open_lab()

c = Lab.open_instr('counter','GPIB1::13')
data=c.getValue('Datas',count=1000)

s='''My test

switch current distribution
'''

Lab.savetxt('test',data, header=s)

import matplotlib.pyplot as plt
plt.hist(data,bins=60)
plt.show()
