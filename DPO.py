# -*- coding: utf-8 -*-
from qulab.driver import InstrumentManager

im = InstrumentManager()
im.add_instr('ATS','ATS9870::SYSTEM1::1::INSTR')
im['ATS'].getTraces()
