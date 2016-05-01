# -*- coding: utf-8 -*-
"""
Created on Fri Jan 08 18:49:24 2016

@author: feihoo87
"""
import numpy as np

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


import time
import numpy as np
from qulab import Application, step
from qulab.data import Index, Column
from qulab.plot import curve, listplot
from qulab.drivers import ATS, AWG


def write_data(awg, points, name='ABS', mk1=None, mk2=None):
    """
    points : a 1D numpy.array which values between -1 and 1.
    mk1, mk2: a string contain only '0' and '1'.
    """
    message = 'WLIST:WAVEFORM:DATA "%s",' % name
    clip = lambda self,x: (16383*(x+1)*0.5).clip(0,16383)
    values = clip(points)
    if mk1 is not None:
        for i in range(min(len(mk1), len(values))):
            if mk1[i] == '1':
                values[i] = values[i] + 0x4000
    if mk2 is not None:
        for i in range(min(len(mk2), len(values))):
            if mk2[i] == '1':
                values[i] = values[i] + 0x8000
    awg.write_binary_values(message, values, datatype=u'H', is_big_endian=False, termination=None, encoding=None)
    
class MyApp(Application):
    __title__   = 'Cavity Spectrum'
    __version__ = 'v0.1'
    
    def set_sweep(self):                
        self.sweep_channel("f", f_range,
                           long_name='Frequency', unit='GHz')
        
    def set_datas(self):
        doc = """
        Output Microwave Amplitude
        """
        self.data.template(
            name="Amplitude", fname='amp_{autoname}.txt',
            cols=[Column('channel A', unit='V'), Column('channel B', unit='V')],
            doc=doc)
        
        doc = """
        Cavity Spectrum
        """
            
        self.data.template(
            name="CavitySpectrum", fname='cs_{autoname}.txt',
            index=[Index('Frequency', unit='GHz')],
            cols=[Column('Amplitude', with_err=True, unit='mV')],
            doc = doc)
            
        self.data.targets("CavitySpectrum")
            
    def set_plots(self):
            
        def get_data(app = self):
            x    = app.data["CavitySpectrum"]['Frequency']
            y, e = app.data["CavitySpectrum"]['Amplitude']
            return x, y
            
        self.plot.add_item(curve("Cavity Spectrum",
                                 "Frequency (GHz)",
                                 "Readout Amplitude (mV)",
                                 get_data),
                           ["CavitySpectrum"])
        
    def init(self):
        self.cfg['ex_mw'] = self.rm.open_resource(ex_mw)
        self.cfg['me_mw'] = self.rm.open_resource(me_mw)
        self.cfg['lo_mw'] = self.rm.open_resource(lo_mw)
        self.cfg['awg']   = AWG(self.rm.open_resource(awg))
        
        WAVEFORM_SIZE, _ = self.cfg['awg'].current_waveforms()
        points1 = "0"*READ_OUT + "1"*ME_LEN + "0"*(WAVEFORM_SIZE-ME_LEN-READ_OUT)
        points2 = "0"*(READ_OUT+TRIGGER_DELAY) + "1"*1000 + "0"*(WAVEFORM_SIZE-1000-READ_OUT-TRIGGER_DELAY)
        self.cfg['awg'].marker_data("trigger", points1, points2)

        self.cfg['ats'] = ATS()
        self.cfg['ats'].init()
        
        self.cfg['ex_mw'].write(":OUTPUT OFF")
        self.cfg['me_mw'].write(":POWER %.8e" % me_power)
        self.cfg['me_mw'].write(":OUTPUT ON")
        self.cfg['lo_mw'].write(":POWER %.8e" % 18)
        self.cfg['lo_mw'].write(":OUTPUT ON")
    
    @step()
    def set_freq(self, f):
        self.cfg['me_mw'].write(":FREQ:CW %.13e" % (f*1e9))
        self.cfg['lo_mw'].write(":FREQ:CW %.13e" % (f*1e9-heterodyne_freq))
        time.sleep(0.01)
        
    @step(follows=["set_freq"])
    def measurement(self):
        ret = self.cfg['ats'].get_IQ(ME_LEN, npoints, heterodyne_freq)
        ch1, ch2 = ret[:,0], ret[:,1]
        self.data["Amplitude"] = {'channel A': ch1, 'channel B': ch2}
        A = 0.5*(ch1+1j*ch2)
        #P1 = 1e3*np.abs(A).mean()
        #e  = 1e3*np.abs(A).std()
        P1 = 1e3*np.abs(A.mean())
        e  = 1e3*A.std()
        self.data["CavitySpectrum"].append(Amplitude = (P1, e))
        
    def final(self):
        self.cfg['me_mw'].write(":OUTPUT OFF")
        self.cfg['lo_mw'].write(":OUTPUT OFF")
        
        self.cfg['me_mw'].close()
        self.cfg['lo_mw'].close()
        self.cfg['ex_mw'].close()
        self.cfg['awg'].close()
        
        
if __name__ == "__main__":
    import sys
    app = MyApp(sys.argv)
    sys.exit(app.run())
    