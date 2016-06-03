# -*- coding: utf-8 -*-
import numpy as np

class Driver(BaseDriver):
    surport_models = ['E8257D']

    quants = [
        Q('Frequency', unit='Hz', type=DOUBLE,
          set_cmd=':FREQ %(value).13e',
          get_cmd=':FREQ?'),

        Q('Power', unit='dBm', type=DOUBLE,
          set_cmd=':POWER %(value).8e',
          get_cmd=':POWER?'),

        Q('Output', unit='', type=OPTION,
          set_cmd=':OUTP %(option)s', options=[('OFF', 'OFF'), ('ON', 'ON')]),
    ]
