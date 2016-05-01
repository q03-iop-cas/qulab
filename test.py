# -*- coding: utf-8 -*-
"""
Created on Fri Jan 08 18:49:24 2016

@author: feihoo87
"""
import numpy as np

t_range = np.linspace(0,2000,201)   # ns
f_range = np.linspace(9.015,9.03,121)     # GHz
npoints = 5000


import time
import numpy as np
from qulab import Application, step
from qulab.data import Index, Column
from qulab.plot import image
from qulab.drivers import ATS


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


class MyApp(Application):
    __title__   = 'test (dispersive measurement)'
    __version__ = 'v0.1'
    
    last_t = -1
    
    def set_sweep(self):                
        self.sweep_channel("t", t_range,
                           long_name='Time', unit='ns')
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
        Rabi in dispersive range
        """
            
        self.data.template(
            name="Rabi2D", fname='test_{autoname}.txt',
            index=[Index('Time', unit='ns'), Index('Frequency', unit='GHz')],
            cols=[Column('Amplitude', with_err=True, unit='mV')],
            doc = doc)
            
        self.data.targets("Rabi2D")
            
    def set_plots(self):
        def get_data(app = self):
            x    = app.data["Rabi2D"]['Frequency']
            y    = app.data["Rabi2D"]['Time']
            z, e = app.data["Rabi2D"]['Amplitude']
            return x, y, z
            
        self.plot.add_item(image("Rabi",
                                 "Frequency (GHz)",
                                 "Time (ns)",
                                 get_data),
                           ["Rabi2D"])
        
    def init(self):
        pass
    
    @step()
    def set_time_freq(self, t, f):
        pass
        
    @step(follows=["set_time_freq"])
    def measurement(self):
        ret = np.random.randn(npoints, 4)
        ch1, ch2 = ret[:,0]+1j*ret[:,1], ret[:,2]+1j*ret[:,3]
        self.data["Amplitude"] = {'channel A': ch1, 'channel B': ch2}
        A = 0.5*(ch1+1j*ch2)
        #P1 = 1e3*np.abs(A).mean()
        #e  = 1e3*np.abs(A).std()
        P1 = 1e3*np.abs(A.mean())
        e  = 1e3*A.std()
        self.data["Rabi2D"].append(Amplitude = (P1, e))
        
    def final(self):
        pass
        
        
if __name__ == "__main__":
    import sys
    app = MyApp(sys.argv)
    sys.exit(app.run())
    