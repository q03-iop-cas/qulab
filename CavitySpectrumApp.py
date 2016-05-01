# -*- coding: utf-8 -*-
"""
Created on Fri Jan 08 18:49:24 2016

@author: feihoo87
"""
import numpy as np

#{{{ settings }}}
ex_mw = "TCPIP::10.122.7.102::INSTR"
lo_mw = "TCPIP::10.122.7.104::INSTR"
me_mw = "TCPIP::10.122.7.103::INSTR"
awg   = "TCPIP::10.122.7.100::INSTR"
me_power = 3
heterodyne_freq = 50e6
READ_OUT = 50000
ME_LEN   = 1000
TRIGGER_DELAY = 180
f_range = np.linspace(9.26,9.30,101)   # GHz
npoints = 5000
#}}}

import numpy as np
from qulab import Application
from AmplitudeApp import AmplitudeApp

class CavitySpectrumApp(Application):
    __title__   = 'Cavity Spectrum'
    __version__ = 'v0.1'

    def discription(self):
        self.instruments = {}
        self.parameters = []
        self.sweeps  = []
        self.plots   = {}
        self.records = {}

    def set_freq(self, f):
        self.ins['Me MW'].setValue('Frequency', f)
        self.ins['Lo MW'].setValue('Frequency', f-self.P('Heterodyne Freq'))

    def prepare(self):
        self.amp_app = AmplitudeApp(parent=self)

    def measurement(self):
        I, Q = self.amp_app.measurement()
        return I, Q


if __name__ == "__main__":
    import sys
    app = MyApp(sys.argv)
    sys.exit(app.run())
