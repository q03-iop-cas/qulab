# -*- coding: utf-8 -*-
from qulab import open_lab

Lab=open_lab()

ats = Lab.open_instr('ATS','ATS9870::SYSTEM1::1::INSTR')
awg = Lab.open_instr('AWG', 'TCPIP::10.122.7.100')

import numpy as np

SIZE, _ = awg.get_current_waveforms()
t = np.linspace(-20,20, SIZE)
wav = np.exp(-t*t/2)*np.sin(2*np.pi*t)
#awg.update_waveform(wav, 'X')

ats.setValue('Trigger Mode', 'J')
ats.setValue('J Source', 'ChA')
ats.setValue('J Slope', 'Negative')
ats.setValue('J Level', -0.5)
ats.setValue('A Range', 2.5)
chA, chB = ats.getTraces(samplesPerRecord=2000, pre=1000, repeats=100)

import matplotlib.pyplot as plt

#chA, chB = np.array(chA), np.array(chB)
plt.plot(chA.mean(axis=0))
plt.plot(chB.mean(axis=0))
plt.show()
