# -*- coding: utf-8 -*-
from qulab import Application
from qulab.record import Template

class AmplitudeApp(Application):
    __title__ = 'Microwave Amplitude'
    __version__ = 'v1.0'

    def discription(self):
        self.instruments = {
            'ATS' : ATS(),
            'Me MW' : MWSource(),
            'Lo MW' : MWSource()
        }

        self.paramenters = [
            dict(name='HeterodyneFreq', unit='Hz', value=50e6),
            dict(name='RecordLength', unit='', value=1000),
            dict(name='Repeats', unit='', value=1000)
        ]

        AmplitudeDoc = '''
        The IQ value of output microwave.

        The output microwave is send to the RF port of an IQ-Mixer.
        Signals come from the IQ ports of the IQ-mixer.
        '''

        template = Template(
            index=[],
            cols=[
                dict(name='I', unit='V', with_err=False),
                dict(name='Q', unit='V', with_err=False)
            ],
            fname='amp_{autoname}.txt',
            doc=AmplitudeDoc
        )

        self.record_templates = [
            ('Amplitude', template)
        ]

        self.plots = [
            ListPoints(self.data['Amplitude']['I'], self.data['Amplitude']['Q'])
        ]

    def prepare(self):
        self.ins['ATS'].setValue('Sample rate', 1e9)
        self.ins['ATS'].setValue('Reference clock', 'Ext')
        self.ins['ATS'].setValue('Channel A Range', 1)
        self.ins['ATS'].setValue('Channel B Range', 1)
        self.ins['ATS'].setValue('Trigger', 'Ext')

        t = np.arange(0, self.P('RecordLength'), 1) * 1e-9
        self.Exp = np.exp(1j*2*np.pi*self.P('HeterodyneFreq')*t)

    def measurement(self):
        ch1, ch2 = self.ins['ATS'].get_Traces(self.P('RecordLength'), self.P('Repeats'))
        I, Q = (ch1[:,:n]*self.Exp).mean(axis=1), (ch2[:,:n]*self.Exp).mean(axis=1)
        return I, Q
