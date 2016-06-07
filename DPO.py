# -*- coding: utf-8 -*-
from qulab.driver import InstrumentManager
import numpy as np

im = InstrumentManager()
im.add_instr('ATS','ATS9870::SYSTEM1::1::INSTR')
im.add_instr('AWG', 'TCPIP::10.122.7.100')

SIZE, _ = im['AWG'].get_current_waveforms()
t = np.linspace(-20,20, SIZE)
wav = np.exp(-t*t/2)*np.sin(2*np.pi*t)
#im['AWG'].update_waveform(wav, 'X')

im['ATS'].setValue('Trigger Mode', 'J')
im['ATS'].setValue('J Source', 'ChA')
im['ATS'].setValue('J Slope', 'Negative')
im['ATS'].setValue('J Level', -0.1)
im['ATS'].setValue('A Range', 2.5)
chA, chB = im['ATS'].getTraces(samplesPerRecord=1500, repeats=100)

import matplotlib.pyplot as plt

chA, chB = np.array(chA), np.array(chB)
plt.plot(chA.mean(axis=0))
plt.plot(chB.mean(axis=0))
plt.show()
