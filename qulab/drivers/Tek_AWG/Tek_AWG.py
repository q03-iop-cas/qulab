# -*- coding: utf-8 -*-
"""
Created on Fri Jan 22 17:06:24 2016

@author: Administrator
"""
import numpy as np

class Driver(BaseDriver):
    surport_models = ['AWG5014C']

    quants = [
        Q('Vpp', unit='V',
          set_cmd='SOURCE%(channel)d:VOLT %(value)f',
          get_cmd='SOURCE%(channel)d:VOLT?'),

        Q('Offset', unit='V',
          set_cmd='SOURCE%(channel)d:VOLT:OFFS %(value)f',
          get_cmd='SOURCE%(channel)d:VOLT:OFFS?'),

        Q('Volt Low', unit='V',
          set_cmd='SOURCE%(channel)d:VOLT:LOW %(value)f',
          get_cmd='SOURCE%(channel)d:VOLT:LOW?'),

        Q('Volt High', unit='V',
          set_cmd='SOURCE%(channel)d:VOLT:HIGH %(value)f',
          get_cmd='SOURCE%(channel)d:VOLT:HIGH?')
    ]

    def performOpen(self):
        pass

    def performSetValue(self, quant, value, **kw):
        if quant.name == '':
            return
        else:
            return super(Driver, self).performSetValue(quant, value, **kw)

    def performGetValue(self, quant, **kw):
        if quant.name == '':
            return ''
        else:
            return super(Driver, self).performGetValue(quant, **kw)

    def creat_waveform(self, name, length):
        self.write('WLIS:WAV:NEW "%s",%d,INT;' % (name, length))

    def remove_waveform(self, name):
        self.write(':WLIS:WAV:DEL "%s"; *CLS' % name)

    def use_waveform(self, name, ch=1):
        self.write('SOURCE%d:WAVEFORM "%s"' % (ch, name))

    def run_state(self):
        return int(self.query(':AWGC:RST?'))

    def run(self):
        self.write(':AWGC:RUN;')

    def stop(self):
        self.write(':AWGC:STOP;')

    def output_on(self, ch=1):
        self.write(':OUTP%d:STAT 1;' % ch)

    def output_off(self, ch=1):
        self.write(':OUTP%d:STAT 0;' % ch)

    def get_current_waveforms(self):
        current_waveforms = []
        current_waveform_size = 0
        for i in [1,2,3,4]:
            wn = self.query('SOUR%d:WAV?')[1:-2]
            current_waveforms.append(wn)
            if wn != '' and current_waveform_size == 0:
                current_waveform_size = self.query_ascii_values('WLIS:WAV:LENGTH? "%s"' % wn, 'd')[0]
        return current_waveform_size, current_waveforms

    def update_waveform(self, points, name='ABS', mk1=None, mk2=None):
        """
        points : a 1D numpy.array which values between -1 and 1.
        mk1, mk2: a string contain only '0' and '1'.
        """
        message = 'WLIST:WAVEFORM:DATA "%s",' % name
        points = points.clip(-1,1)
        values = (points * 0x1fff).astype(int) + 0x2000
        if mk1 is not None:
            for i in range(min(len(mk1), len(values))):
                if mk1[i] == '1':
                    values[i] = values[i] + 0x4000
        if mk2 is not None:
            for i in range(min(len(mk2), len(values))):
                if mk2[i] == '1':
                    values[i] = values[i] + 0x8000
        self.write_binary_values(message, values, datatype=u'H',
                                 is_big_endian=False,
                                 termination=None, encoding=None)

    def update_marker(self, name, mk1, mk2):
        values = []
        for i in range(len(mk1)):
            d = 0
            if mk1[i] == '1':
                d += 64
            if mk2[i] == '1':
                d += 128
            values.append(d)
        message = 'WLIST:WAVEFORM:MARKER:DATA "%s",' % name
        self.write_binary_values(message, values, datatype=u'B',
                                 is_big_endian=False,
                                 termination=None, encoding=None)
