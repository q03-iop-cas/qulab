# -*- coding: utf-8 -*-
from qulab.driver import InstrumentManager
import time
import numpy as np
import logging
import logging.handlers
from scipy.interpolate import interp1d

threshold = 0.000355
#waveform = interp1d([],[])

logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)
socketHandler = logging.handlers.SocketHandler('localhost',\
                logging.handlers.DEFAULT_TCP_LOGGING_PORT)
socketHandler.setLevel(logging.DEBUG)
#logger.addHandler(ch)
logger.addHandler(socketHandler)

logger.info('QubitStep Start')
im = InstrumentManager()
im.add_instr('counter', 'GPIB1::13')
im['counter'].set_timeout(25)
im.add_instr('squid_sour', 'GPIB1::20')
im.add_instr('bais_sour', 'GPIB1::11')
im['bais_sour'].DC(0)

from qulab.utils import get_threshold

n = 50000
vRange = np.arange(-0.42,-0.35, 0.001)
x = []
y = []
for v in vRange:
    im['bais_sour'].setValue('Offset', v)
    #print(v)
    time.sleep(0.01)
    data = np.array(im['counter'].getValue('Datas', count=n))
    threshold = get_threshold(data)
    P = 1.0*len(data[data > threshold])/len(data)
    print('Flux : %f V, Probility : %f' % (v, P))
    x.extend([v for i in range(n)])
    y.extend(list(data))

import numpy as np
import matplotlib.pyplot as plt

x = np.array(x)
y = np.array(y)

x = x[y > 0.00031]
y = y[y > 0.00031]
np.savetxt('QubitStep_%s.txt'%time.strftime("%Y%m%d%H%M%S"), np.array([x,y]).T)
logger.info('QubitStep Finished')

plt.hist2d(x, y, bins=[len(vRange),201])
plt.show()
