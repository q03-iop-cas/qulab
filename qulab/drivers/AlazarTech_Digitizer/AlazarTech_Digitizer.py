import numpy as np
from AlazarCmd import *

class Driver(BaseDriver):
    surport_models = ['ATS9870']
    quants = [
        Q('Clock Source', value='External 10MHz Ref', type=OPTION,
            options=[
                ('Internal', 1),
                ('External', 2),
                ('Medium External', 3),
                ('Slow External', 4),
                ('External AC', 5),
                ('External DC', 6),
                ('External 10MHz Ref', 7),
                ('Internal Div 5', 0x10),
                ('Master', 0x11),
                ('Internal Set VCO', 0x12)
            ]),

        Q('Sample Rate', value='1G', unit='SPS',  type=OPTION,
            options=[
                ('1k',    SAMPLE_RATE_1KSPS),   ('2k',    SAMPLE_RATE_2KSPS),
                ('5k',    SAMPLE_RATE_5KSPS),   ('10k',   SAMPLE_RATE_10KSPS),
                ('20k',   SAMPLE_RATE_20KSPS),  ('50k',   SAMPLE_RATE_50KSPS),
                ('100k',  SAMPLE_RATE_100KSPS), ('200k',  SAMPLE_RATE_200KSPS),
                ('500k',  SAMPLE_RATE_500KSPS), ('1M',    SAMPLE_RATE_1MSPS),
                ('2M',    SAMPLE_RATE_2MSPS),   ('5M',    SAMPLE_RATE_5MSPS),
                ('10M',   SAMPLE_RATE_10MSPS),  ('20M',   SAMPLE_RATE_20MSPS),
                ('25M',   SAMPLE_RATE_25MSPS),  ('50M',   SAMPLE_RATE_50MSPS),
                ('100M',  SAMPLE_RATE_100MSPS), ('125M',  SAMPLE_RATE_125MSPS),
                ('160M',  SAMPLE_RATE_160MSPS), ('180M',  SAMPLE_RATE_180MSPS),
                ('200M',  SAMPLE_RATE_200MSPS), ('250M',  SAMPLE_RATE_250MSPS),
                ('400M',  SAMPLE_RATE_400MSPS), ('500M',  SAMPLE_RATE_500MSPS),
                ('800M',  SAMPLE_RATE_800MSPS), ('1G',    SAMPLE_RATE_1GSPS),
                ('1200M', SAMPLE_RATE_1200MSPS),('1500M', SAMPLE_RATE_1500MSPS),
                ('1600M', SAMPLE_RATE_1600MSPS),('1800M', SAMPLE_RATE_1800MSPS),
                ('2G',    SAMPLE_RATE_2GSPS),
            ]),

        Q('Trigger Delay', value=0, unit='s', type=DOUBLE),
        Q('Trigger Timeout', value=1, unit='s', type=DOUBLE),

        Q('A Term', value='50 Ohm', type=OPTION, options=[('1 MOhm', 1), ('50 Ohm', 2), ('75 Ohm', 4), ('300 Ohm', 8)]),
        Q('B Term', value='50 Ohm', type=OPTION, options=[('1 MOhm', 1), ('50 Ohm', 2), ('75 Ohm', 4), ('300 Ohm', 8)]),
        Q('Ext Coupling', value='DC', type=OPTION, options=[('DC', 2), ('AC', 1)]),
        Q('A Coupling', value='DC', type=OPTION, options=[('DC', 2), ('AC', 1)]),
        Q('B Coupling', value='DC', type=OPTION, options=[('DC', 2), ('AC', 1)]),
        Q('A Range', value=1, unit='V', type=DOUBLE),
        Q('B Range', value=1, unit='V', type=DOUBLE),
        Q('A Bandwidth limit', value='Disable', type=OPTION, options=[('Disable', 0), ('Enable', 1)]),
        Q('B Bandwidth limit', value='Disable', type=OPTION, options=[('Disable', 0), ('Enable', 1)]),

        Q('Trigger Mode', type=OPTION,
            options = [
                ('J',            0),
                ('K',            1),
                ('J or K',       2),
                ('J and K',      3),
                ('J xor K',      4),
                ('J and not K',  5),
                ('not J and K',  6),
            ]),
        Q('J Level', value=0.1, unit='V', type=DOUBLE),
        Q('K Level', value=0.1, unit='V', type=DOUBLE),
        Q('J Slope', value='Positive', type=OPTION, options=[('Positive', 1), ('Negative', 2)]),
        Q('K Slope', value='Positive', type=OPTION, options=[('Positive', 1), ('Negative', 2)]),
        Q('J Source', value='External', type=OPTION, options=[('ChA', 0), ('ChB', 1), ('External', 2), ('Disable', 3), ('ChC', 4), ('ChD', 5)]),
        Q('K Source', value='Disable', type=OPTION, options=[('ChA', 0), ('ChB', 1), ('External', 2), ('Disable', 3), ('ChC', 4), ('ChD', 5)]),
    ]

    def __init__(self, **kw):
        BaseDriver.__init__(self, **kw)
        self.systemID = kw['systemID']
        self.boardID  = kw['boardID']
        self.dig = None
        self.config_updated = False
        self.dt = 1E-9

    def __load_wrapper(self):
        if self.dig is None:
            from AlazarTech_Wrapper import AlazarTechDigitizer
            self.dig = AlazarTechDigitizer(self.systemID, self.boardID)

    def set_configs(self):
        """Set digitizer configuration based on driver settings"""
        if self.config_updated:
            return
        # clock configuration
        SourceId = self.getCmdOption('Clock Source')
        SampleRateId = self.getCmdOption('Sample Rate')
            # 10 MHz ref, use 1GHz rate + divider. NB!! divide must be 1,2,4,10
            #SampleRateId = int(1E9)
            #Decimation = int(round(1E9/lFreq[self.getValueIndex('Sample Rate')]))
        self.dig.AlazarSetCaptureClock(SourceId, SampleRateId)
        # define time step from sample rate
        lFreq = [1E3, 2E3, 5E3, 10E3, 20E3, 50E3, 100E3, 200E3, 500E3,
                 1E6, 2E6, 5E6, 10E6, 20E6, 25E6, 50E6, 100E6, 125E6, 160E6,
                 180E6, 200E6, 250E6, 400E6, 500E6, 800E6, 1E9, 1.2E9, 1.5E9,
                 1.6E9, 1.8E9, 2E9]
        self.dt = 1/lFreq[self.getValueIndex('Sample Rate')]
        #
        # configure inputs
        for ch in ['A', 'B']:
            chIds = {'A': CHANNEL_A, 'B': CHANNEL_B}
            chId = chIds[ch]
            Coupling = self.getCmdOption('%s Coupling' % ch)
            InputRange = self.dig.get_input_range(self.getValue('%s Range' % ch))
            Impedance = self.getCmdOption('%s Term' % ch)
            self.dig.AlazarInputControl(chId, Coupling, InputRange, Impedance)
            # bandwidth limit
            BW = self.getValue('%s Bandwidth limit' % ch)
            self.dig.AlazarSetBWLimit(chId, BW)
        Coupling = self.getCmdOption('Ext Coupling')
        self.dig.AlazarSetExternalTrigger(Coupling)
        #
        # configure trigger
        Mode = self.getCmdOption('Trigger Mode')
        JSource = self.getCmdOption('J Source')
        KSource = self.getCmdOption('J Source')
        JSlope = self.getCmdOption('J Slope')
        KSlope = self.getCmdOption('K Slope')
        JLevel, KLevel = 0, 0

        # convert relative level to U8
        for egn in ['J', 'K']:
            sour = self.getValue('%s Source' % egn)
            trigLevel = self.getValue('%s Level' % egn)
            Amp = {
                INPUT_RANGE_PM_4_V : 4.0, INPUT_RANGE_PM_2_V : 2.0,
                INPUT_RANGE_PM_1_V : 1.0, INPUT_RANGE_PM_400_MV : 0.4,
                INPUT_RANGE_PM_200_MV : 0.2, INPUT_RANGE_PM_100_MV : 0.1,
                INPUT_RANGE_PM_40_MV : 0.04
            }
            if sour == 'ChA':
                maxLevel = Amp[self.dig.get_input_range(self.getValue('A Range'))]
            elif sour == 'ChB':
                maxLevel = Amp[self.dig.get_input_range(self.getValue('B Range'))]
            elif sour == 'External':
                maxLevel = 5.0
            if abs(trigLevel)>maxLevel:
                trigLevel = maxLevel*np.sign(trigLevel)
            Level = int(128 + 127*trigLevel/maxLevel)
            if egn == 'J':
                JLevel = Level
            else:
                KLevel = Level
        # set config
        self.dig.AlazarSetTriggerOperation(Mode,
                                       TRIG_ENGINE_J, JSource, JSlope, JLevel,
                                       TRIG_ENGINE_K, KSource, KSlope, KLevel)
        #
        # set trig delay and timeout
        Delay = int(self.getValue('Trigger Delay')/self.dt)
        self.dig.AlazarSetTriggerDelay(Delay)
        timeout = self.getValue['Trigger Timeout']
        self.dig.AlazarSetTriggerTimeOut(time=timeout)
        self.config_updated = True

    def performSetValue(self, quant, value, **kw):
        if quant.name not in ['']:
            BaseDriver.performSetValue(quant, value, **kw)
        self.config_updated = False

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
