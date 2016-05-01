# -*- coding: utf-8 -*-
"""
Created on Fri Jan 08 18:49:24 2016

@author: feihoo87
"""
import numpy as np

#{{{ settings }}}
ex_mw = "TCPIP::10.122.7.101::INSTR"
ex21_mw = "TCPIP::10.122.7.102::INSTR"
lo_mw = "TCPIP::10.122.7.104::INSTR"
me_mw = "TCPIP::10.122.7.103::INSTR"
awg   = "TCPIP::10.122.7.100::INSTR"
me_freq  = 9.2656
me_power = 3
ex_freq  = 7.637
ex_power = 15
ex21_freq  = 7.3045
ex21_power = 5
heterodyne_freq = 50e6
READ_OUT = 50000
ME_LEN   = 1000
PI_LEN   = 42  # ns
TRIGGER_DELAY = 180
EX_DELAY   = 0
EX21_DELAY = 0
t_range = np.linspace(0,200,101)   # ns
p0_mfreq, p1_mfreq, p2_mfreq = 9.2825, 9.2725, 9.2656 # GHz
npoints = 50000
#}}}

import time
import numpy as np
from qulab import Application, step
from qulab.data import Index, Column
from qulab.plot import curve, listplot
from qulab.drivers import ATS, AWG


class MyApp(Application):
    __title__   = 'Rabi 21'
    __version__ = 'v0.1'
    
    def set_sweep(self):
        self.sweep_channel("t", t_range,
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
            name="Rabi", fname='rabi21_{autoname}.txt',
            index=[Index('Time', unit='ns')],
            cols=[Column('Amplitude', with_err=True, unit='mV')],
            doc = doc)
            
        self.data.targets("Rabi")
            
    def set_plots(self):
        #def get_data(app = self):
        #    ch1 = app.data["Amplitude"]['channel A']
        #    ch2 = app.data["Amplitude"]['channel B']
        #    A = 0.5*(ch1+1j*ch2)*1e3
        #    return np.real(A), np.imag(A)
            
        #self.plot.add_item(listplot("IQ",
        #                         "I (mV)",
        #                         "Q (mV)",
        #                         get_data),
        #                   ["Amplitude"])
                           
        #def get_data(app = self):
        #    ch1 = app.data["Amplitude"]['channel A']
        #    ch2 = app.data["Amplitude"]['channel B']
        #    return np.real(ch1), np.real(ch2)
            
        #self.plot.add_item(listplot("IQ2",
        #                         "I (mV)",
        #                         "Q (mV)",
        #                         get_data),
        #                   ["Amplitude"])
                           
        def get_data(app = self):
            x    = app.data["Rabi"]['Time']
            y, e = app.data["Rabi"]['Amplitude']
            return x, y
            
        self.plot.add_item(curve("Rabi21",
                                 "Time (ns)",
                                 "Readout Amplitude (mV)",
                                 get_data),
                           ["Rabi"])
        
    def init(self):
        self.cfg['ex_mw'] = self.rm.open_resource(ex_mw)
        self.cfg['ex21_mw'] = self.rm.open_resource(ex21_mw)
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
        
        self.cfg['ex21_mw'].write(":FREQ:CW %.13e" % (ex21_freq*1e9))
        self.cfg['ex21_mw'].write(":POWER %.8e" % ex21_power)
        self.cfg['ex21_mw'].write(":OUTPUT ON")
        
        self.cfg['me_mw'].write(":POWER %.8e" % me_power)
        self.cfg['me_mw'].write(":FREQ:CW %.13e" % (me_freq*1e9))
        self.cfg['me_mw'].write(":OUTPUT ON")
        
        self.cfg['lo_mw'].write(":FREQ:CW %.13e" % (me_freq*1e9-heterodyne_freq))
        self.cfg['lo_mw'].write(":POWER %.8e" % 18)
        self.cfg['lo_mw'].write(":OUTPUT ON")
    
    @step()
    def set_time(self, t):
        points = np.array([0]*int(READ_OUT-t-PI_LEN+EX21_DELAY) + [1]*int(t) + [0]*int(self.cfg['WAVEFORM_SIZE']-READ_OUT-EX21_DELAY+PI_LEN))
        #x = np.arange(0, self.cfg['WAVEFORM_SIZE'], 1)
        mk = "0"*(READ_OUT-t-PI_LEN+EX21_DELAY) + "1"*t + "0"*(self.cfg['WAVEFORM_SIZE']-READ_OUT-EX21_DELAY+PI_LEN)
        self.cfg['awg'].write_data(points, "stock", mk, mk)
        
        points = np.array([0]*int(READ_OUT-PI_LEN+EX_DELAY-t) + [1]*int(PI_LEN) + [0]*int(self.cfg['WAVEFORM_SIZE']-READ_OUT-EX_DELAY+t))
        #x = np.arange(0, self.cfg['WAVEFORM_SIZE'], 1)
        mk = "0"*(READ_OUT-PI_LEN+EX_DELAY-t) + "1"*PI_LEN + "0"*(self.cfg['WAVEFORM_SIZE']-READ_OUT-EX_DELAY+t)
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
        self.data["Rabi"].append(Amplitude = (P1, e))
        
    def final(self):
        self.cfg['ex_mw'].write(":OUTPUT OFF")
        self.cfg['ex21_mw'].write(":OUTPUT OFF")
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
    