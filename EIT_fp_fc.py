# -*- coding: utf-8 -*-
"""
Created on Fri Jan 08 18:49:24 2016

@author: feihoo87
"""
import numpy as np

#{{{  settings }}}
ex_mw = "TCPIP::10.122.7.102::INSTR"
ex21_mw = "TCPIP::10.122.7.101::INSTR"
lo_mw = "TCPIP::10.122.7.104::INSTR"
me_mw = "TCPIP::10.122.7.103::INSTR"
awg   = "TCPIP::10.122.7.100::INSTR"
me_power = 3
ex_freq  = 7.637
ex21_freq = 7.3052
ex_power = 15
ex21_power = 0
heterodyne_freq = 50e6
READ_OUT = 50000
ME_LEN   = 1000
PI_LEN   = 100
TRIGGER_DELAY = 180
fc_range = np.linspace(1.65, 1.655, 101)   # GHz
fp_range = np.linspace(9.282,  9.283, 11)            # GHz
#fp_range = np.linspace(7.628,  7.648, 201)            # GHz
p0_mfreq, p1_mfreq, p2_mfreq = 9.2825, 9.2725, 9.2656 # GHz
npoints = 1000
#}}}


import time
import numpy as np
from qulab import Application, step
from qulab.data import Index, Column
from qulab.plot import image
from qulab.drivers import ATS, AWG


class MyApp(Application):
    __title__   = 'EIT var fp & fc (dispersive measurement)'
    __version__ = 'v0.1'
    
    last_t = -1
    
    def set_sweep(self):
        self.sweep_channel("fc", fc_range,
                           long_name='Coupler Frequency', unit='GHz')
        self.sweep_channel("fp", fp_range,
                           long_name='Probe Frequency', unit='GHz')
        
    def set_datas(self):
        doc = """
        EIT var probe frequency and coupler frequency
        """
            
        self.data.template(
            name="ATS_fp_fc", fname='EIT_fp_fc_{autoname}.txt',
            index=[Index('Probe Frequency', unit='GHz'), Index('Coupler Frequency', unit='GHz')],
            cols=[Column('P0', with_err=True, unit='mV')],
            doc = doc)
            
        self.data.targets("ATS_fp_fc")
        self.data_manager.save_raw = False
            
    def set_plots(self):
        def get_data(app = self):
            x    = app.data["ATS_fp_fc"]['Probe Frequency']
            y    = app.data["ATS_fp_fc"]['Coupler Frequency']
            z, e = app.data["ATS_fp_fc"]['P0']
            return x, y, z
            
        self.plot.add_item(image("EIT P0",
                                 "Probe Frequency (GHz)",
                                 "Coupler Frequency (GHz)",
                                 get_data),
                           ["ATS_fp_fc"])
        
    def init(self):
        self.cfg['ex21'] = self.rm.open_resource(ex21_mw)
        self.cfg['ex_mw'] = self.rm.open_resource(ex_mw)
        self.cfg['me_mw'] = self.rm.open_resource(me_mw)
        self.cfg['lo_mw'] = self.rm.open_resource(lo_mw)
        self.cfg['awg']   = AWG(self.rm.open_resource(awg))
        
        self.cfg['WAVEFORM_SIZE'], _ = self.cfg['awg'].current_waveforms()
        points1 = "1"*READ_OUT + "1"*ME_LEN + "1"*(self.cfg['WAVEFORM_SIZE']-ME_LEN-READ_OUT)
        points2 = "1"*(READ_OUT+TRIGGER_DELAY) + "1"*ME_LEN + "1"*(self.cfg['WAVEFORM_SIZE']-ME_LEN-READ_OUT-TRIGGER_DELAY)
        self.cfg['awg'].marker_data("trigger", points1, points2)

        self.cfg['ats'] = ATS()
        self.cfg['ats'].init(max_input = 0.2)
        
        self.cfg['ex21'].write(":FREQ:CW %.13e" % (ex21_freq*1e9))
        self.cfg['ex21'].write(":POWER %.8e" % ex21_power)
        self.cfg['ex21'].write(":OUTPUT OFF")
        
        self.cfg['ex_mw'].write(":FREQ:CW %.13e" % (ex_freq*1e9))
        self.cfg['ex_mw'].write(":POWER %.8e" % ex_power)
        self.cfg['ex_mw'].write(":OUTPUT ON")
        
        self.cfg['me_mw'].write(":POWER %.8e" % me_power)
        #self.cfg['me_mw'].write(":FREQ:CW %.13e" % (me_freq*1e9))
        self.cfg['me_mw'].write(":OUTPUT ON")
        
        points = np.array([1]*int(READ_OUT) + [1]*int(self.cfg['WAVEFORM_SIZE']-READ_OUT))
        mk = "1"*READ_OUT + "1"*(self.cfg['WAVEFORM_SIZE']-READ_OUT)
        self.cfg['awg'].write_data(points, "MW", mk, mk)
        self.cfg['awg'].write_data(points, "stock", mk, mk)
        
        #self.cfg['lo_mw'].write(":FREQ:CW %.13e" % (me_freq*1e9-heterodyne_freq))
        self.cfg['lo_mw'].write(":POWER %.8e" % 18)
        self.cfg['lo_mw'].write(":OUTPUT ON")
    
    @step()
    def set_freq(self, fp, fc):
        self.cfg['ex_mw'].write(":FREQ:CW %.13e" % (fc*1e9))
        self.cfg['me_mw'].write(":FREQ:CW %.13e" % (fp*1e9))
        self.cfg['lo_mw'].write(":FREQ:CW %.13e" % (fp*1e9-heterodyne_freq))
        time.sleep(0.01)
        
    @step(follows=["set_freq"])
    def measurement(self):
        ret = self.cfg['ats'].get_IQ(ME_LEN, npoints, heterodyne_freq)
        ch1, ch2 = ret[:,0], ret[:,1]
        A = 0.5*(ch1+1j*ch2)
        P0 = 1e3*np.abs(A.mean())
        e0  = 1e3*A.std()
        
        self.data["ATS_fp_fc"].append(P0 = (P0, e0))
        
    def final(self):
        self.cfg['ex_mw'].write(":OUTPUT OFF")
        self.cfg['ex21'].write(":OUTPUT OFF")
        self.cfg['me_mw'].write(":OUTPUT OFF")
        self.cfg['lo_mw'].write(":OUTPUT OFF")
        
        self.cfg['me_mw'].close()
        self.cfg['lo_mw'].close()
        self.cfg['ex_mw'].close()
        self.cfg['ex21'].close()
        self.cfg['awg'].close()
        
        
if __name__ == "__main__":
    import sys
    app = MyApp(sys.argv)
    sys.exit(app.run())
    