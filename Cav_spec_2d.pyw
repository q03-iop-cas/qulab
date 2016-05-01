# -*- coding: utf-8 -*-
"""
Created on Fri Jan 08 18:49:24 2016

@author: feihoo87
"""

from guidata.dataset.datatypes import DataSet
from guidata.dataset.dataitems import (FloatItem, IntItem, StringItem)
                             
heterodyne_freq = 50e6
READ_OUT = 20000
ME_LEN   = 500
TRIGGER_DELAY = 180


import time
import numpy as np
from qulab import Application, step
from qulab.data import Index, Column
from qulab.plot import image
from qulab.drivers import ATS, AWG


class MyApp(Application):
    __title__   = 'Cavity Spectrum 2D'
    __version__ = 'v0.1'
    
    def set_sweep(self):
        self.sweep_channel("p", self.cfg['p_range'],
                           long_name='Power', unit='dBm')
        self.sweep_channel("f", self.cfg['f_range'],
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
        Cavity Spectrum var probe power
        """
            
        self.data.template(
            name="CavitySpectrum2D", fname='cs2d_{autoname}.txt',
            index=[Index('Power', unit='dBm'), Index('Frequency', unit='GHz')],
            cols=[Column('Amplitude', with_err=True, unit='mV')],
            doc = doc)
            
        self.data.targets("CavitySpectrum2D")
            
    def set_plots(self):
        
        def get_data(app = self):
            x    = app.data["CavitySpectrum2D"]['Frequency']
            y    = app.data["CavitySpectrum2D"]['Power']
            z, e = app.data["CavitySpectrum2D"]['Amplitude']
            z = 20*np.log10(z)
            return x, y, z.clip(-25,z.max())
            
        self.plot.add_item(image("Cavity Spectrum",
                                 xlabel = "Frequency (GHz)",
                                 ylabel = "Power (dBm)",
                                 zlabel = "20 log(A/1 mV)",
                                 get_data = get_data,
                                 cmap = 'terrain'),
                           ["CavitySpectrum2D"])
                           
    def set_parameters(self):
        
        class Parameters(DataSet):
            ex_mw = StringItem("Excitting Microwave", default="TCPIP::10.122.7.103::INSTR")
            lo_mw = StringItem("LO Microwave", default="TCPIP::10.122.7.102::INSTR")
            me_mw = StringItem("Measurement Microwave", default="TCPIP::10.122.7.101::INSTR")
            awg   = StringItem("AWG", default="TCPIP::10.122.7.100::INSTR")
            #me_power = FloatItem("Measuerment Power (dBm)",
            #                 default=10, min=-135, max=25, step=0.01, slider=True)
                             
            f_range_s = FloatItem("Frequency start (GHz)",
                             default=9.0, min=1, max=20, step=0.01)
            f_range_e = FloatItem("Frequency stop (GHz)",
                             default=9.04, min=1, max=20, step=0.01).set_pos(col=1)
            f_range_n = IntItem("Frequency Num", default=41, min=1, max=100000).set_pos(col=2)
            
            p_range_s = FloatItem("Power start (dBm)",
                             default=-30, min=-130, max=25, step=0.01)
            p_range_e = FloatItem("Power stop (dBm)",
                             default=10.0, min=-130, max=25, step=0.01).set_pos(col=1)
            p_range_n = IntItem("Power Num", default=41, min=1, max=100000).set_pos(col=2)
            
            npoints = IntItem("Number of points", default=1000, min=100, max=100000)
        
        e = Parameters()
        
        if e.edit():
            self.cfg['f_range'] = np.linspace(e.f_range_s, e.f_range_e, e.f_range_n)
            self.cfg['p_range'] = np.linspace(e.p_range_s, e.p_range_e, e.p_range_n)
            self.cfg['ex_mw'] = self.rm.open_resource(e.ex_mw)
            self.cfg['me_mw'] = self.rm.open_resource(e.me_mw)
            self.cfg['lo_mw'] = self.rm.open_resource(e.lo_mw)
            self.cfg['awg']   = AWG(self.rm.open_resource(e.awg))
            self.cfg['npoints'] = e.npoints
            
        self.cfg['ats'] = ATS()
        
    def init(self):
        WAVEFORM_SIZE, _ = self.cfg['awg'].current_waveforms()
        points1 = "0"*READ_OUT + "1"*ME_LEN + "0"*(WAVEFORM_SIZE-ME_LEN-READ_OUT)
        points2 = "0"*(READ_OUT+TRIGGER_DELAY) + "1"*ME_LEN + "0"*(WAVEFORM_SIZE-ME_LEN-READ_OUT-TRIGGER_DELAY)
        self.cfg['awg'].marker_data("trigger", points1, points2)
        
        self.cfg['ats'].init()
        self.cfg['ex_mw'].write(":OUTPUT OFF")
        #self.cfg['me_mw'].write(":POWER %.8e" % self.cfg['me_power'])
        self.cfg['me_mw'].write(":OUTPUT ON")
        self.cfg['lo_mw'].write(":POWER %.8e" % 18)
        self.cfg['lo_mw'].write(":OUTPUT ON")
    
    @step()
    def set_freq_power(self, f, p):
        self.cfg['me_mw'].write(":FREQ:CW %.13e" % (f*1e9))
        self.cfg['lo_mw'].write(":FREQ:CW %.13e" % (f*1e9-heterodyne_freq))
        self.cfg['me_mw'].write(":POWER %.8e" % p)
        time.sleep(0.01)
        
    @step(follows=["set_freq_power"])
    def measurement(self):
        ret = self.cfg['ats'].get_IQ(ME_LEN, self.cfg['npoints'], heterodyne_freq)
        ch1, ch2 = ret[:,0], ret[:,1]
        self.data["Amplitude"] = {'channel A': ch1, 'channel B': ch2}
        A = 0.5*(ch1+1j*ch2)
        #P1 = 1e3*np.abs(A).mean()
        #e  = 1e3*np.abs(A).std()
        P1 = 1e3*np.abs(A.mean())
        e  = 1e3*A.std()
        self.data["CavitySpectrum2D"].append(Amplitude = (P1, e))
        
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
    