from AlazarCmd import *
from AlazarError import *
import AlazarApi as API
import numpy as np
import time

class Error(Exception):
    pass

class Wrapper():
    def __init__(self, systemId=1, boardId=1):
        """The init case defines a session ID, used to identify the instrument"""
        # range settings
        self.dRange = {}
        print('Number of systems:', API.AlazarNumOfSystems())
        handle = API.AlazarGetBoardBySystemID(systemId, boardId)
        if handle is None:
            raise Error('Device with system ID=%d and board ID=%d could not be found.' % (systemId, boardId))
        self.handle = handle
        self._error_list = []
        self.MemorySizeInSamples, self.BitsPerSample = self.AlazarGetChannelInfo()

    def callFunc(self, sFunc, *args, **kw):
        """General function caller with restype=status, also checks for errors"""
        # get function from Lib
        func = getattr(API, sFunc)
        # call function
        status = func(*args)
        if status != RETURN_CODE.ApiSuccess:
            self._error_list.append((status, self.getError(status)))
        return status

    def AlazarGetChannelInfo(self):
        MemorySizeInSamples, BitsPerSample = U32(), U8()
        self.callFunc('AlazarGetChannelInfo', self.handle, MemorySizeInSamples, BitsPerSample)
        return MemorySizeInSamples.value, BitsPerSample.value

    def testLED(self):
        import time
        self.callFunc('AlazarSetLED', self.handle, 1)
        time.sleep(0.1)
        self.callFunc('AlazarSetLED', self.handle, 0)

    def getError(self, status):
        """Convert the error in status to a string"""
        # const char* AlazarErrorToText(RETURN_CODE retCode)
        errorText = API.AlazarErrorToText(status)
        return str(errorText)

    #RETURN_CODE AlazarStartCapture( HANDLE h);
    def AlazarStartCapture(self):
        self.callFunc('AlazarStartCapture', self.handle)

    def AlazarWaitAsyncBufferComplete(self, pBuffer, timeout_ms):
        self.callFunc("AlazarWaitAsyncBufferComplete", self.handle,
                      pBuffer, timeout_ms)

    #RETURN_CODE AlazarAbortCapture( HANDLE h);
    def AlazarAbortCapture(self):
        self.callFunc('AlazarAbortCapture', self.handle)

    #RETURN_CODE AlazarSetCaptureClock( HANDLE h, U32 Source, U32 Rate, U32 Edge, U32 Decimation);
    def AlazarSetCaptureClock(self, SourceId, SampleRateId, EdgeId=0, Decimation=0):
        self.callFunc('AlazarSetCaptureClock', self.handle,
                      SourceId, SampleRateId, EdgeId, Decimation)

    #RETURN_CODE AlazarSetTriggerOperation(HANDLE h, U32 TriggerOperation
    #            ,U32 TriggerEngine1/*j,K*/, U32 Source1, U32 Slope1, U32 Level1
    #            ,U32 TriggerEngine2/*j,K*/, U32 Source2, U32 Slope2, U32 Level2);
    def AlazarSetTriggerOperation(self, TriggerOperation=0,
                                  TriggerEngine1=0, Source1=0, Slope1=1, Level1=128,
                                  TriggerEngine2=1, Source2=3, Slope2=1, Level2=128):
        self.callFunc('AlazarSetTriggerOperation', self.handle, TriggerOperation,
                      TriggerEngine1, Source1, Slope1, Level1,
                      TriggerEngine2, Source2, Slope2, Level2)

    #RETURN_CODE AlazarInputControl( HANDLE h, U8 Channel, U32 Coupling, U32 InputRange, U32 Impedance);
    def AlazarInputControl(self, Channel, Coupling, InputRange, Impedance):
        # keep track of input range
        dConv = {
            INPUT_RANGE_PM_20_MV: 0.02,
            INPUT_RANGE_PM_40_MV: 0.04,
            INPUT_RANGE_PM_50_MV: 0.05,
            INPUT_RANGE_PM_80_MV: 0.08,
            INPUT_RANGE_PM_100_MV: 0.1,
            INPUT_RANGE_PM_200_MV: 0.2,
            INPUT_RANGE_PM_400_MV: 0.4,
            INPUT_RANGE_PM_500_MV: 0.5,
            INPUT_RANGE_PM_800_MV: 0.8,
            INPUT_RANGE_PM_1_V: 1.0,
            INPUT_RANGE_PM_2_V: 2.0,
            INPUT_RANGE_PM_4_V: 4.0,
            INPUT_RANGE_PM_5_V: 5.0,
            INPUT_RANGE_PM_8_V: 8.0,
            INPUT_RANGE_PM_10_V: 10.0,
            INPUT_RANGE_PM_20_V: 20.0,
            INPUT_RANGE_PM_40_V: 40.0,
            INPUT_RANGE_PM_16_V: 16.0,
            #INPUT_RANGE_HIFI	=	0x00000020
            INPUT_RANGE_PM_1_V_25: 1.25,
            INPUT_RANGE_PM_2_V_5: 2.5,
            INPUT_RANGE_PM_125_MV: 0.125,
            INPUT_RANGE_PM_250_MV: 0.25
        }
        self.dRange[Channel] = dConv[InputRange]
        self.callFunc('AlazarInputControl', self.handle,
                      Channel, Coupling, InputRange, Impedance)

    #RETURN_CODE AlazarSetExternalTrigger( HANDLE h, U32 Coupling, U32 Range);
    def AlazarSetExternalTrigger(self, Coupling, Range=0):
        self.callFunc('AlazarSetExternalTrigger', self.handle, Coupling, Range)

    def get_input_range(self, max_input):
        input_range = INPUT_RANGE_PM_4_V
        if max_input <= 2.0:
            input_range = INPUT_RANGE_PM_2_V
        if max_input <= 1.0:
            input_range = INPUT_RANGE_PM_1_V
        if max_input <= 0.4:
            input_range = INPUT_RANGE_PM_400_MV
        if max_input <= 0.2:
            input_range = INPUT_RANGE_PM_200_MV
        if max_input <= 0.1:
            input_range = INPUT_RANGE_PM_100_MV
        if max_input <= 0.04:
            input_range = INPUT_RANGE_PM_40_MV
        return input_range

    def init(self, max_ChA=1.0, max_ChB=1.0):
        self.AlazarSetCaptureClock(SourceId=EXTERNAL_CLOCK_10MHz_REF, SampleRateId=SAMPLE_RATE_1GSPS)
        self.AlazarInputControl(CHANNEL_A, DC_COUPLING, self.get_input_range(max_ChA), IMPEDANCE_50_OHM)
        self.AlazarInputControl(CHANNEL_B, DC_COUPLING, self.get_input_range(max_ChB), IMPEDANCE_50_OHM)
        self.AlazarSetExternalTrigger(DC_COUPLING)
        self.AlazarSetTriggerOperation(TriggerOperation=TRIG_ENGINE_OP_J,
                                       TriggerEngine1=TRIG_ENGINE_J, Source1=TRIG_EXTERNAL, Slope1=TRIGGER_SLOPE_POSITIVE, Level1=int(128+127*0.5/5.0),
                                       TriggerEngine2=TRIG_ENGINE_K, Source2=TRIG_DISABLE, Slope2=TRIGGER_SLOPE_POSITIVE, Level2=128)

    #RETURN_CODE  AlazarSetTriggerDelay( HANDLE h, U32 Delay);
    def AlazarSetTriggerDelay(self, Delay=0):
        self.callFunc('AlazarSetTriggerDelay', self.handle, Delay)

    #RETURN_CODE  AlazarSetTriggerTimeOut( HANDLE h, U32 to_ns);
    def AlazarSetTriggerTimeOut(self, time=0.0):
        tick = U32(int(time*1E5))
        self.callFunc('AlazarSetTriggerTimeOut', self.handle, tick)

    #RETURN_CODE AlazarSetRecordSize( HANDLE h, U32 PreSize, U32 PostSize);
    def AlazarSetRecordSize(self, PreSize, PostSize):
        self.nPreSize = int(PreSize)
        self.nPostSize = int(PostSize)
        self.callFunc('AlazarSetRecordSize', self.handle, PreSize, PostSize)

    #RETURN_CODE AlazarSetRecordCount( HANDLE h, U32 Count);
    def AlazarSetRecordCount(self, Count):
        self.nRecord = int(Count)
        self.callFunc('AlazarSetRecordCount', self.handle, Count)

    #U32	AlazarBusy( HANDLE h);
    def AlazarBusy(self):
        # call function, return result
        return bool(API.AlazarBusy(self.handle))

    def AlazarRead(self, Channel, Buffer, ElementSize, Record, TransferOffset, TransferLength):
        self.callFunc('AlazarRead', self.handle,
                      Channel, Buffer, ElementSize,
                      Record, TransferOffset, TransferLength)

    def readTraces(self, Channel, samplesPerRecord=1024, repeats=1000):
        """Read traces, convert to float, average to a single trace"""
        # define sizes
        bitsPerSample = 8
        bytesPerSample = int(np.floor((float(bitsPerSample) + 7.) / 8.0))
        #samplesPerRecord = self.nPreSize + self.nPostSize
        # The buffer must be at least 16 samples larger than the transfer size
        samplesPerBuffer = samplesPerRecord + 16
        dataBuffer = (c_uint8*samplesPerBuffer)()
        # define scale factors
        codeZero = 2 ** (float(bitsPerSample) - 1) - 0.5
        codeRange = 2 ** (float(bitsPerSample) - 1) - 0.5
        voltScale = self.dRange[Channel] /codeRange
        # initialize a scaled float vector
        vData = []
        for n1 in range(repeats):
            self.AlazarRead(Channel, dataBuffer, bytesPerSample, n1+1,
                            -0, samplesPerRecord)
            # convert and scale to float
            vBuffer = voltScale * ((np.array(dataBuffer[:samplesPerRecord]) - codeZero))
            # add to output vector
            vData.append(vBuffer)

        return vData

    def get_Traces(self, samplesPerRecord=1024, repeats=1000, timeout = 10):
        self.AlazarSetRecordSize(0, samplesPerRecord)
        self.AlazarSetRecordCount(repeats)
        self.AlazarStartCapture()

        nTry = timeout/0.05
        while nTry>0 and self.AlazarBusy():
            # sleep for a while to save resources, then try again
            time.sleep(0.05)
            nTry -= 1
        # check if timeout occurred
        if nTry <= 0:
            self.AlazarAbortCapture()
            raise Exception('Acquisition timed out')

        return (self.readTraces(CHANNEL_A, samplesPerRecord, repeats),
                self.readTraces(CHANNEL_B, samplesPerRecord, repeats))
