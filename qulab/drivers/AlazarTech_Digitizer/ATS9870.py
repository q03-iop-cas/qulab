class Driver(BaseDriver):
    def __init__(self, systemID, boardID, **kw):
        super(ATS9870, self).__init__(**kw)
        self.digitizer = Wrapper(systemID, boardID)

    def performGetValue(self, quant):
        if quant.name == 'SampleRate':
            return 1e9
        else:
            return quant.getValue()

    def performSetValue(self, quant, value):
        if quant.name not in {}:
            quant.setValue(value)
        else:
            pass

    def getTraces(self):
        chA, chB = self.digitizer.get_Traces()
        return chA, chB
