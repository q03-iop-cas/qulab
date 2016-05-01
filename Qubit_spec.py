# -*- coding: utf-8 -*-
"""
Created on Fri Jan 08 18:49:24 2016

@author: feihoo87
"""
import numpy as np

ex_mw = "TCPIP::10.122.7.101::INSTR"
lo_mw = "TCPIP::10.122.7.104::INSTR"
me_mw = "TCPIP::10.122.7.103::INSTR"
awg   = "TCPIP::10.122.7.100::INSTR"
me_freq  = 9.2825
me_power = 3
ex_power = 0
heterodyne_freq = 50e6
READ_OUT = 50000
ME_LEN   = 1000
TRIGGER_DELAY = 180
f_range = np.linspace(7.62,7.65,301)   # GHz
npoints = 50000


import time
import numpy as np
from qulab import Application, step
from qulab.data import Index, Column
from qulab.plot import curve
from qulab.drivers import ATS, AWG


class MyApp(Application):
    __title__   = 'Qubit Spectrum'
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
            name="QubitSpectrum", fname='qs_{autoname}.txt',
            index=[Index('Frequency', unit='GHz')],
            cols=[Column('Amplitude', with_err=True, unit='mV')],
            doc = doc)
            
        self.data.targets("QubitSpectrum")
            
    def set_plots(self):
        
        def get_data(app = self):
            x    = app.data["QubitSpectrum"]['Frequency']
            y, e = app.data["QubitSpectrum"]['Amplitude']
            return x, y
            
        self.plot.add_item(curve("Qubit Spectrum",
                                 "Frequency (GHz)",
                                 "Readout Amplitude (mV)",
                                 get_data),
                           ["QubitSpectrum"])
        
    def init(self):
        self.cfg['ex21'] = self.rm.open_resource("TCPIP::10.122.7.104::INSTR")
        self.cfg['ex_mw'] = self.rm.open_resource(ex_mw)
        self.cfg['me_mw'] = self.rm.open_resource(me_mw)
        self.cfg['lo_mw'] = self.rm.open_resource(lo_mw)
        self.cfg['awg']   = AWG(self.rm.open_resource(awg))
        
        WAVEFORM_SIZE, _ = self.cfg['awg'].current_waveforms()
        points1 = "0"*READ_OUT + "1"*ME_LEN + "0"*(WAVEFORM_SIZE-ME_LEN-READ_OUT)
        points2 = "0"*(READ_OUT+TRIGGER_DELAY) + "1"*ME_LEN + "0"*(WAVEFORM_SIZE-ME_LEN-READ_OUT-TRIGGER_DELAY)
        points3 = "1"*READ_OUT + "0"*(WAVEFORM_SIZE-READ_OUT)
        self.cfg['awg'].marker_data("trigger", points1, points2)
        self.cfg['awg'].marker_data("MW", points3, points3)

        self.cfg['ats'] = ATS()
        self.cfg['ats'].init(max_input = 0.2)
        
        self.cfg['ex21'].write(":OUTPUT OFF")
        
        self.cfg['ex_mw'].write(":POWER %.8e" % ex_power)
        self.cfg['ex_mw'].write(":OUTPUT ON")
        
        self.cfg['me_mw'].write(":POWER %.8e" % me_power)
        self.cfg['me_mw'].write(":FREQ:CW %.13e" % (me_freq*1e9))
        self.cfg['me_mw'].write(":OUTPUT ON")
        
        self.cfg['lo_mw'].write(":FREQ:CW %.13e" % (me_freq*1e9-heterodyne_freq))
        self.cfg['lo_mw'].write(":POWER %.8e" % 18)
        self.cfg['lo_mw'].write(":OUTPUT ON")
    
    @step()
    def set_freq(self, f):
        self.cfg['ex_mw'].write(":FREQ:CW %.13e" % (f*1e9))
        time.sleep(0.01)
        
    @step(follows=["set_freq"])
    def measurement(self):
        ret = self.cfg['ats'].get_IQ(ME_LEN, npoints, heterodyne_freq)
        ch1, ch2 = ret[:,0], ret[:,1]
        self.data["Amplitude"] = {'channel A': ch1, 'channel B': ch2}
        A = 0.5*(ch1+1j*ch2)
        P1 = 1e3*np.abs(A).mean()
        e  = 1e3*np.abs(A).std()
        self.data["QubitSpectrum"].append(Amplitude = (P1, e))
        
    def final(self):
        self.cfg['ex_mw'].write(":OUTPUT OFF")
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
    