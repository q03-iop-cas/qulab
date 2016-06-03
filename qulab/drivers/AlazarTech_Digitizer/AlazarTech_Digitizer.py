import numpy as np

class Driver(BaseDriver):
    surport_models = ['ATS9870']
    quants = [
        Q('Ext Term', unit='', type=OPTION, options={'50 Ohm' : '0', '1 MOhm' : '1'}),
        Q('A Term', unit='', type=OPTION, options={'50 Ohm' : '0', '1 MOhm' : '1'}),
        Q('B Term', unit='', type=OPTION, options={'50 Ohm' : '0', '1 MOhm' : '1'}),
        Q('Ext Coupling', unit='', type=OPTION, options={'DC' : '0', 'AC' : '1'}),
        Q('A Coupling', unit='', type=OPTION, options={'DC' : '0', 'AC' : '1'}),
        Q('B Coupling', unit='', type=OPTION, options={'DC' : '0', 'AC' : '1'}),

        Q('Trigger Mode', type=OPTION,
            options = {
                'J'           : 0,
                'K'           : 1,
                'J or K'      : 2,
                'J and K'     : 3,
                'J xor K'     : 4,
                'J and not K' : 5,
                'not J and K' : 6,
            })
        Q('J Level', unit='V', type=DOUBLE),
        Q('K Level', unit='V', type=DOUBLE),
        Q('J Slope', type=OPTION, options={'Positive' : 1, 'Negative' : 2}),
        Q('K Slope', type=OPTION, options={'Positive' : 1, 'Negative' : 2}),
        Q('J Source', type=OPTION, options={'ChA' : 0, 'ChB' : 1, 'Ext' : 2, 'Disable' : 3, 'ChC' : 4, 'ChD' : 5}),
        Q('K Source', type=OPTION, options={'ChA' : 0, 'ChB' : 1, 'Ext' : 2, 'Disable' : 3, 'ChC' : 4, 'ChD' : 5}),
    ]

    def __init__(self, **kw):
        BaseDriver.__init__(self, **kw)
        self.systemID = kw['systemID']
        self.boardID  = kw['boardID']
        self.dig = None
        self.configs = {
            'updated' : False,
            'Clock Ref' : 'EXTERNAL_CLOCK_10MHz_REF',
            'Sample Rate' : 'SAMPLE_RATE_1GSPS',
            '' : ''
        }

    def __load_wrapper(self):
        if self.dig is None:
            from AlazarTech_Wrapper import AlazarTechDigitizer
            self.dig = AlazarTechDigitizer(self.systemID, self.boardID)

    def set_configs(self):
        """Set digitizer configuration based on driver settings"""
        if self.configs['updated']:
            return
        # clock configuration
        SourceId = int(self.getCmdStringFromValue('Clock source'))
        if self.getValue('Clock source') == 'Internal':
            # internal
            SampleRateId = int(self.getCmdStringFromValue('Sample rate'),0)
            lFreq = [1E3, 2E3, 5E3, 10E3, 20E3, 50E3, 100E3, 200E3, 500E3,
                     1E6, 2E6, 5E6, 10E6, 20E6, 50E6, 100E6, 200E6, 500E6, 1E9]
            Decimation = 0
        else:
            # 10 MHz ref, use 1GHz rate + divider. NB!! divide must be 1,2,4,10
            SampleRateId = int(1E9)
            lFreq = [1E3, 2E3, 5E3, 10E3, 20E3, 50E3, 100E3, 200E3, 500E3,
                     1E6, 2E6, 5E6, 10E6, 20E6, 50E6, 100E6, 250E6, 500E6, 1E9]
            Decimation = int(round(1E9/lFreq[self.getValueIndex('Sample rate')]))
        self.dig.AlazarSetCaptureClock(SourceId, SampleRateId, 0, Decimation)
        # define time step from sample rate
        self.dt = 1/lFreq[self.getValueIndex('Sample rate')]
        # 
        # configure inputs
        for n in range(2):
            if self.getValue('Ch%d - Enabled' % (n+1)):
                # coupling and range
                Coupling = int(self.getCmdStringFromValue('Ch%d - Coupling' % (n+1)))
                InputRange = int(self.getCmdStringFromValue('Ch%d - Range' % (n+1)))
                Impedance = int(self.getCmdStringFromValue('Ch%d - Impedance' % (n+1)))
                self.dig.AlazarInputControl(n+1, Coupling, InputRange, Impedance)
                # bandwidth limit
                BW = int(self.getValue('Ch%d - Bandwidth limit' % (n+1)))
                self.dig.AlazarSetBWLimit(n+1, BW)
        #
        # configure trigger
        Source = int(self.getCmdStringFromValue('Trig source'))
        Slope = int(self.getCmdStringFromValue('Trig slope'))
        Delay = self.getValue('Trig delay')
        # trig level is relative to full range
        trigLevel = self.getValue('Trig level')
        vAmp = np.array([4, 2, 1, 0.4, 0.2, 0.1, .04], dtype=float)
        if self.getValue('Trig source') == 'Channel 1':
            maxLevel = vAmp[self.getValueIndex('Ch1 - Range')]
        elif self.getValue('Trig source') == 'Channel 2':
            maxLevel = vAmp[self.getValueIndex('Ch2 - Range')]
        elif self.getValue('Trig source') == 'External':
            maxLevel = 5.0
        # convert relative level to U8
        if abs(trigLevel)>maxLevel:
            trigLevel = maxLevel*np.sign(trigLevel)
        Level = int(128 + 127*trigLevel/maxLevel)
        # set config
        self.dig.AlazarSetTriggerOperation(0, 0, Source, Slope, Level)
        #
        # config external input, if in use
        if self.getValue('Trig source') == 'External':
            Coupling = int(self.getCmdStringFromValue('Trig coupling'))
            self.dig.AlazarSetExternalTrigger(Coupling)
        #
        # set trig delay and timeout
        Delay = int(self.getValue('Trig delay')/self.dt)
        self.dig.AlazarSetTriggerDelay(Delay)
        timeout = self.dComCfg['Timeout']
        self.dig.AlazarSetTriggerTimeOut(time=timeout)
        self.configs['updated'] = True

    def performSetValue(self, quant, value, **kw):
        if quant.name not in ['']:
            BaseDriver.performSetValue(quant, value, **kw)
        self.configs['updated'] = False

    def performGetValue(self, quant, **kw):
        self.__load_wrapper()
        self.set_configs()
        pass

    def errors(self):
        self.__load_wrapper()
        ret = []
        try:
            while True:
                e = self.wrapper._error_list.pop(0)
                ret.append(e)
        except IndexError:
            return ret
        return []

    def getTraces(self, samplesPerRecord=1024, repeats=1000, timeout = 10):
        self.__load_wrapper()
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
