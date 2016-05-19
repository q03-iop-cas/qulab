import numpy as np
from AlazarTech_Wrapper import Wrapper

class Driver(BaseDriver):
    surport_models = ['ATS9870']

    def __init__(self, **kw):
        super(Driver, self).__init__(**kw)
        self.systemID = kw['systemID']
        self.boardID  = kw['boardID']
        self.wrapper = Wrapper(self.systemID, self.boardID)

    def performSetValue(self, quant, value, **kw):
        pass

    def performGetValue(self, quant, **kw):
        pass

    def errors(self):
        ret = []
        try:
            while True:
                e = self.wrapper._error_list.pop(0)
                ret.append(e)
        except IndexError:
            return ret
        return []

    def getTraces(self, samplesPerRecord=1024, repeats=1000, timeout = 10):
        ChA, ChB = [], []
        max = 5000
        loop = int(repeats/max)
        last = repeats % max
        try:
            if last < repeats:
                for i in range(loop):
                    a, b = self.wrapper.get_Traces(samplesPerRecord, max, timeout)
                    ChA.extend(a)
                    ChB.extend(b)
                a, b = self.wrapper.get_Traces(samplesPerRecord, last, timeout)
                ChA.extend(a)
                ChB.extend(b)
        except:
            raise
        return ChA, ChB
