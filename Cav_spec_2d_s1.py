# -*- coding: utf-8 -*-
"""
Created on Fri Jan 08 18:49:24 2016

@author: feihoo87
"""
import numpy as np

ex_mw = "TCPIP::10.122.7.103::INSTR"
lo_mw = "TCPIP::10.122.7.102::INSTR"
me_mw = "TCPIP::10.122.7.101::INSTR"
awg   = "TCPIP::10.122.7.100::INSTR"
me_power = 10
heterodyne_freq = 50e6
ex_freq  = 5.764
ex_power = 20
PI_LEN = 337
READ_OUT = 20000
ME_LEN   = 1000
TRIGGER_DELAY = 180
f_range = np.linspace(9,9.04,41)   # GHz
p_range = np.linspace(-30,10,41)      # dBm
npoints = 1000


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
    __title__   = 'Cavity Spectrum 2D'
    __version__ = 'v0.1'
    
    def set_sweep(self):
        self.sweep_channel("p", p_range,
                           long_name='Power', unit='dBm')
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
        Cavity Spectrum var probe power for state 1 prepared
        """
            
        self.data.template(
            name="CavitySpectrum2DS1", fname='cs2ds1_{autoname}.txt',
            index=[Index('Power', unit='dBm'), Index('Frequency', unit='GHz')],
            cols=[Column('Amplitude', with_err=True, unit='mV')],
            doc = doc)
            
        self.data.targets("CavitySpectrum2DS1")
            
    def set_plots(self):
        
        def get_data(app = self):
            x    = app.data["CavitySpectrum2DS1"]['Frequency']
            y    = app.data["CavitySpectrum2DS1"]['Power']
            z, e = app.data["CavitySpectrum2DS1"]['Amplitude']
            z = 20*np.log10(z)
            return x, y, z.clip(-25,z.max())
            
        self.plot.add_item(image("Cavity Spectrum for State |1>",
                                 xlabel = "Frequency (GHz)",
                                 ylabel = "Power (dBm)",
                                 zlabel = "20 log(A/1 mV)",
                                 get_data = get_data,
                                 cmap = 'terrain'),
                           ["CavitySpectrum2DS1"])
        
    def init(self):
        self.cfg['ex_mw'] = self.rm.open_resource(ex_mw)
        self.cfg['me_mw'] = self.rm.open_resource(me_mw)
        self.cfg['lo_mw'] = self.rm.open_resource(lo_mw)
        self.cfg['awg']   = self.rm.open_resource(awg)
        
        WAVEFORM_SIZE = self.cfg['awg'].query_ascii_values('WLIST:WAVEFORM:LENGTH? "MW"', 'd')[0]
        points1 = "0"*READ_OUT + "1"*ME_LEN + "0"*(WAVEFORM_SIZE-ME_LEN-READ_OUT)
        points2 = "0"*(READ_OUT+TRIGGER_DELAY) + "1"*ME_LEN + "0"*(WAVEFORM_SIZE-ME_LEN-READ_OUT-TRIGGER_DELAY)
        marker_data(self.cfg['awg'], "trigger", points1, points2)

        self.cfg['ats'] = ATS()
        self.cfg['ats'].init()
        
        self.cfg['ex_mw'].write(":FREQ:CW %.13e" % (ex_freq*1e9))
        self.cfg['ex_mw'].write(":POWER %.8e" % ex_power)
        self.cfg['ex_mw'].write(":OUTPUT ON")
        points = "0"*(READ_OUT-PI_LEN) + "1"*PI_LEN + "0"*(WAVEFORM_SIZE-READ_OUT)
        marker_data(self.cfg['awg'], "MW", points, points)
        
        self.cfg['me_mw'].write(":POWER %.8e" % me_power)
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
        ret = self.cfg['ats'].get_IQ(ME_LEN, npoints, heterodyne_freq)
        ch1, ch2 = ret[:,0], ret[:,1]
        self.data["Amplitude"] = {'channel A': ch1, 'channel B': ch2}
        A = 0.5*(ch1+1j*ch2)
        P1 = 1e3*np.abs(A).mean()
        e  = 1e3*np.abs(A).std()
        self.data["CavitySpectrum2DS1"].append(Amplitude = (P1, e))
        
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
    
