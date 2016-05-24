# -*- coding: utf-8 -*-
from qulab import open_lab
import os, sys
import time, datetime
import numpy as np
import logging
from scipy.interpolate import interp1d

Lab = open_lab()

logger = logging.getLogger('main')

c = Lab.open_instr('Counter', 'GPIB1::17')
c.setValue('Mode', 'count')
print(c.getValue('A Slope'))
