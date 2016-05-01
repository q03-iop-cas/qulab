# -*- coding: utf-8 -*-
"""
Created on Fri Jan 22 17:06:24 2016

@author: Administrator
"""
import numpy as np

def get_current_waveforms(awg):
    current_waveforms = []
    current_waveform_size = 0
    
    for i in [1,2,3,4]:
        wn = awg.query("SOUR1:WAVEFORM?")[1:-2]
        current_waveforms.append(wn)
        if wn != '' and current_waveform_size == 0:
            current_waveform_size = awg.query_ascii_values('WLIST:WAVEFORM:LENGTH? "%s"' % wn, 'd')[0]
    return current_waveform_size, current_waveforms

def set_volt(awg, ch, vpp=None, offs=None, low=None, high=None):
    """设置电压
    
    vpp  : 设置电压峰峰值
    offs : 设置直流偏压
    """
    if ch not in [1,2,3,4]:
        return
    if vpp != None:
            awg.write("SOURCE%d:VOLT %f" % (ch, vpp))
    if offs != None:
            awg.write("SOURCE%d:VOLT:OFFS %f" % (ch, offs))
    if low != None:
            awg.write("SOURCE%d:VOLT:LOW %f" % (ch, low))
    if high != None:
            awg.write("SOURCE%d:VOLT:HIGH %f" % (ch, high))
            
def new_waveform(awg, name, length):
    awg.write('WLIST:WAVEFORM:NEW "%s",%d,INTEGER' % 
                        (name, length))

def write_data(awg, points, name='ABS', mk1=None, mk2=None):
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
    awg.write_binary_values(message, values, datatype=u'H', is_big_endian=False, termination=None, encoding=None)
    
def marker_data(awg, name, mk1, mk2):
    values = []
    for i in range(len(mk1)):
        d = 0
        if mk1[i] == '1':
            d += 64
        if mk2[i] == '1':
            d += 128
        values.append(d)
    message = 'WLIST:WAVEFORM:MARKER:DATA "%s",' % name
    awg.write_binary_values(message, values, datatype=u'B', is_big_endian=False, termination=None, encoding=None)
    
class AWG:
    def __init__(self, ins):
        self.ins = ins
        
    def current_waveforms(self):
        current_waveform_size, current_waveforms = get_current_waveforms(self.ins)
        return current_waveform_size, current_waveforms
        
    def set_volt(self, ch, vpp=None, offs=None, low=None, high=None):
        return set_volt(self.ins, ch, vpp=None, offs=None, low=None, high=None)
        
    def new_waveform(self, name, length):
        return new_waveform(self.ins, name, length)
        
    def write_data(self, points, name='ABS', mk1=None, mk2=None):
        return write_data(self.ins, points, name, mk1, mk2)
        
    def marker_data(self, name, mk1, mk2):
        return marker_data(self.ins, name, mk1, mk2)
        
    def use_shape(self, name, ch=1):
        self.ins.write("SOURCE%d:WAVEFORM \"%s\"" % (ch, name))
        
    def close(self):
        self.ins.close()
    
if __name__ == "__main__":
    import visa
    rm = visa.ResourceManager()
    awg = rm.open_resource('TCPIP::10.122.7.100')
    print awg.ask("WLIST:SIZE?")
    print awg.ask('WLIST:WAVEFORM:LENGTH? "%s"' % 'Guasse')
    t = np.linspace(-100,100,100000)
    points = np.exp(-0.5*t**2)
    print len(points)
    write_data(awg, points, 'Guasse')
    print awg.ask('SYST:ERR?')
    
