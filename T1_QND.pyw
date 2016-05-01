# -*- coding: utf-8 -*-
"""
Created on Fri Jan 08 18:49:24 2016

@author: feihoo87
"""

ex_mw = "TCPIP::10.122.7.101::INSTR"
lo_mw = "TCPIP::10.122.7.104::INSTR"
me_mw = "TCPIP::10.122.7.103::INSTR"
awg   = "TCPIP::10.122.7.100::INSTR"
me_freq  = 9.2825
me_power = 3
ex_freq  = 7.636
ex_power = 15
PI_LEN = 40
heterodyne_freq = 50e6
READ_OUT = 20000
ME_LEN   = 20000
TRIGGER_DELAY = 180
npoints = 50000


import time
import numpy as np
from qulab import Application, step
from qulab.data import Column
from qulab.plot import curve
from qulab.drivers import ATS, AWG


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
    __title__   = 'T1'
    __version__ = 'v0.1'
    
    def set_sweep(self):                
        self.sweep_channel("n", [1],
                           long_name='n')
        
    def set_datas(self):
        
        doc = """
        Cavity Spectrum
        """
            
        self.data.template(
            name="T1", fname='T1_QND_{autoname}.txt',
            cols=[Column('Time', with_err=False, unit='ns'), Column('Amplitude', with_err=False, unit='mV')],
            doc = doc)
            
        self.data.targets("T1")
            
    def set_plots(self):
        
        def get_data(app = self):
            x = app.data["T1"]['Time']
            y = app.data["T1"]['Amplitude']
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
        
        points = np.array([0]*int(READ_OUT-PI_LEN) + [1]*int(PI_LEN) + [0]*int(self.cfg['WAVEFORM_SIZE']-READ_OUT))
        mk = "0"*(READ_OUT-PI_LEN) + "1"*PI_LEN + "0"*(self.cfg['WAVEFORM_SIZE']-READ_OUT)
        self.cfg['awg'].write_data(points, "MW", mk, mk)
        time.sleep(0.01)
        
    @step()
    def measurement(self):
        
        dt = 1
        t = np.linspace(0, ME_LEN-1, ME_LEN) * dt
        f = -heterodyne_freq*1e-9
        #N = ME_LEN
        Exp = np.exp(-2j*np.pi*f*t)
        hat = 2*np.abs(f)/np.sqrt(2*np.pi)*np.exp(-0.5*(f*(t-t.mean()))**2)
        
        def fft_convolve(a, b, n, N):
            A = np.fft.fft(a, N)
            B = np.fft.fft(b, N)
            return np.fft.ifft(A*B)[:n]
            
        n1 = 2*ME_LEN-1
        n2 = 2**(int(np.log2(n1))+1)
        
        A = np.zeros(ME_LEN, dtype=complex)
        B = np.zeros(ME_LEN, dtype=complex)
        C = np.zeros(ME_LEN, dtype=complex)
        
        loop = npoints / 100
        
        for k in range(loop):
            ch1, ch2 = self.cfg['ats'].get_Traces2(samplesPerRecord=ME_LEN, repeats=100)
            for i in range(100):
                A += ch1[i]
                B += ch2[i]
                A = fft_convolve(Exp*ch1[i], hat, n1, n2)[ME_LEN/2-1:2*ME_LEN-1-ME_LEN/2]
                B = fft_convolve(Exp*ch2[i], hat, n1, n2)[ME_LEN/2-1:2*ME_LEN-1-ME_LEN/2]
                C += A+1j*B
                #C += ch1[i]#+1j*ch2[i]
                print k, i
            
        #A /= npoints
        #B /= npoints
        #C = fft_convolve(Exp*A, hat, n1, n2)[ME_LEN/2-1:2*ME_LEN-1-ME_LEN/2] + 1j*fft_convolve(Exp*B, hat, n1, n2)[ME_LEN/2-1:2*ME_LEN-1-ME_LEN/2]
        C /= npoints
        
        P0 = 1e3*np.abs(C)
        self.data["T1"] = {'Time' : t,'Amplitude' : P0}
        
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
    