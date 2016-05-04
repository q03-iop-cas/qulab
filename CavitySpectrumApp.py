# -*- coding: utf-8 -*-
"""
Created on Fri Jan 08 18:49:24 2016

@author: feihoo87
"""
import numpy as np
from qulab import Application
from qulab.record import Template
from AmplitudeApp import AmplitudeApp

class CavitySpectrumApp(Application):
    __title__   = 'Cavity Spectrum'
    __version__ = 'v0.1'

    def discription(self):
        self.instruments = {
            'Me MW' : "TCPIP::10.122.7.103::INSTR",
            'Lo MW' : "TCPIP::10.122.7.104::INSTR",
            'AWG'   : "TCPIP::10.122.7.100::INSTR",
            'ATS'   : "SYST1::1"
        }

        self.parameters = [
            dict(name='HeterodyneFreq', unit='Hz', default=50e6),
            dict(name='ProbePower', unit='dBm', default=0),
            dict(name='ProbeAttenuate', unit='dB', default=0),
            dict(name='ProbeFrequency', unit='Hz', default=np.linspace(9.25,9.35,201), type=VECTOR),
        ]

        self.sweeps  = [
            dict(var='freq', name = 'ProbeFrequency', unit='Hz', before=None, after=None)
        ]

        Doc = '''
        The S21 of cavity.
        '''

        template = Template(
            index=[dict(name='ProbeFrequency', unit='Hz')],
            cols=[
                dict(name='I', unit='V', with_err=False),
                dict(name='Q', unit='V', with_err=False)
            ],
            fname='S21_{autoname}.txt',
            doc=Doc
        )

        self.record_templates = {
            'S21' : template
        }

        self.plots   = {
            Curves(
                title = 'S21',
                xlabel = 'Probe Frequency',
                ylabel = 'Amplitude',
                datas = (self.data['S21'],),
                calc = lambda datas: (datas[0]['ProbeFrequency'],
                                      datas[0]['I'], datas[0]['Q'],
                                      np.abs(datas[0]['I']+1j*datas[0]['Q']))
                labels = ['Real', 'Imag', 'Abs'])
        }

    def set_freq(self, freq):
        self.ins['Me MW'].setValue('Frequency', freq)
        self.ins['Lo MW'].setValue('Frequency', freq-self.P('HeterodyneFreq'))

    def prepare(self):
        self.amp_app = AmplitudeApp(parent=self)

    def measurement(self):
        I, Q = self.amp_app.measurement()
        return I, Q


if __name__ == "__main__":
    import sys
    app = MyApp(sys.argv)
    sys.exit(app.run())
