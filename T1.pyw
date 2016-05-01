# -*- coding: utf-8 -*-
"""
Created on Fri Jan 08 18:49:24 2016

@author: feihoo87
"""
import numpy as np

#{{{ settings }}}
ex_mw = "TCPIP::10.122.7.101::INSTR"
lo_mw = "TCPIP::10.122.7.104::INSTR"
me_mw = "TCPIP::10.122.7.103::INSTR"
awg   = "TCPIP::10.122.7.100::INSTR"
me_freq  = 9.2825
me_power = 3
ex_freq  = 7.637
ex_power = 15
PI_LEN = 42
heterodyne_freq = 50e6
READ_OUT = 40000
ME_LEN   = 1000
TRIGGER_DELAY = 180
t_range = np.linspace(0,20000,401)   # ns
npoints = 50000
#}}}

import time
import numpy as np
from qulab import Application, step
from qulab.data import Index, Column
from qulab.plot import curve
from qulab.drivers import ATS, AWG


class MyApp(Application):
    __title__   = 'T1'
    __version__ = 'v0.1'
    
    def t_range(self):
        for t in t_range:
            yield t
    
    def set_sweep(self):                
        self.sweep_channel("t", self.t_range,
                           long_name='Time', unit='ns')
        
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
            name="T1", fname='T1_{autoname}.txt',
            index=[Index('Time', unit='ns')],
            cols=[Column('Amplitude', with_err=True, unit='mV')],
            doc = doc)
            
        self.data.targets("T1")
            
    def set_plots(self):
        
        def get_data(app = self):
            x    = app.data["T1"]['Time']
            y, e = app.data["T1"]['Amplitude']
            return x, y
            
        self.plot.add_item(curve("T1",
                                 "Time (ns)",
                                 "Readout Amplitude (mV)",
                                 get_data),
                           ["T1"])
        
    def init(self):
        self.cfg['ex_mw'] = self.rm.open_resource(ex_mw)
        self.cfg['me_mw'] = self.rm.open_resource(me_mw)
        self.cfg['lo_mw'] = self.rm.open_resource(lo_mw)
        self.cfg['awg']   = AWG(self.rm.open_resource(awg))
        
        self.cfg['WAVEFORM_SIZE'], _ = self.cfg['awg'].current_waveforms()
        points1 = "0"*READ_OUT + "1"*ME_LEN + "0"*(self.cfg['WAVEFORM_SIZE']-ME_LEN-READ_OUT)
        points2 = "0"*(READ_OUT+TRIGGER_DELAY) + "1"*ME_LEN + "0"*(self.cfg['WAVEFORM_SIZE']-ME_LEN-READ_OUT-TRIGGER_DELAY)
        self.cfg['awg'].marker_data("trigger", points1, points2)

        self.cfg['ats'] = ATS()
        self.cfg['ats'].init()
        
        self.cfg['ex_mw'].write(":FREQ:CW %.13e" % (ex_freq*1e9))
        self.cfg['ex_mw'].write(":POWER %.8e" % ex_power)
        self.cfg['ex_mw'].write(":OUTPUT ON")
        
        self.cfg['me_mw'].write(":POWER %.8e" % me_power)
        self.cfg['me_mw'].write(":FREQ:CW %.13e" % (me_freq*1e9))
        self.cfg['me_mw'].write(":OUTPUT ON")
        
        self.cfg['lo_mw'].write(":FREQ:CW %.13e" % (me_freq*1e9-heterodyne_freq))
        self.cfg['lo_mw'].write(":POWER %.8e" % 18)
        self.cfg['lo_mw'].write(":OUTPUT ON")
    
    @step()
    def set_time(self, t):
        points = np.array([0]*int(READ_OUT-t-PI_LEN) + [1]*int(PI_LEN) + [0]*int(self.cfg['WAVEFORM_SIZE']-READ_OUT+t))
        mk = "0"*(READ_OUT-t-PI_LEN) + "1"*PI_LEN + "0"*(self.cfg['WAVEFORM_SIZE']-READ_OUT+t)
        self.cfg['awg'].write_data(points, "MW", mk, mk)
        time.sleep(0.01)
        
    @step(follows=["set_time"])
    def measurement(self):
        ret = self.cfg['ats'].get_IQ(ME_LEN, npoints, heterodyne_freq)
        ch1, ch2 = ret[:,0], ret[:,1]
        self.data["Amplitude"] = {'channel A': ch1, 'channel B': ch2}
        A = 0.5*(ch1+1j*ch2)
        #P1 = 1e3*np.abs(A).mean()
        #e  = 1e3*np.abs(A).std()
        P1 = 1e3*np.abs(A.mean())
        e  = 1e3*A.std()
        self.data["T1"].append(Amplitude = (P1, e))
        
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
    