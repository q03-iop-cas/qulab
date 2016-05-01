# -*- coding: utf-8 -*-
"""
Created on Fri Mar 25 12:43:16 2016

@author: Administrator
"""
import numpy as np
import visa
from qulab.drivers import ATS, AWG

heterodyne_freq = 50e6
ME_LEN   = 20000
npoints = 1000

rm = visa.ResourceManager()

ats = ATS()
awg = AWG(rm.open_resource("TCPIP::10.122.7.100::INSTR"))

ats.init(0.2)


dt = 1
t = np.linspace(0, ME_LEN-1, ME_LEN) * dt
f = -heterodyne_freq*1e-9
#N = ME_LEN
Exp = np.exp(-2j*np.pi*(f*t+0.885))
hat = 2*np.abs(f)/np.sqrt(2*np.pi)*np.exp(-0.5*(f*(t-t.mean()))**2)
        
def fft_convolve(a, b, n, N):
    A = np.fft.fft(a, N)
    B = np.fft.fft(b, N)
    return np.fft.ifft(A*B)[:n]
            
n1 = 2*ME_LEN-1
n2 = 2**(int(np.log2(n1))+1)
                   
C = np.zeros(ME_LEN, dtype=complex)
        
loop = npoints / 100
        
for k in range(loop):
    ch1, ch2 = ats.get_Traces2(samplesPerRecord=ME_LEN, repeats=100)
    for i in range(100):
        A = fft_convolve(Exp*ch1[i], hat, n1, n2)[ME_LEN/2-1:2*ME_LEN-1-ME_LEN/2]
        B = fft_convolve(Exp*ch2[i], hat, n1, n2)[ME_LEN/2-1:2*ME_LEN-1-ME_LEN/2]
        C += A+1j*B
        #C += ch1[i]+1j*ch2[i]
        print k, i
            
C /= npoints
        
#P1 = 1e3*np.abs(C)

import matplotlib.pyplot as plt
plt.plot(t, np.real(C))
plt.plot(t, np.imag(C))
plt.show()

