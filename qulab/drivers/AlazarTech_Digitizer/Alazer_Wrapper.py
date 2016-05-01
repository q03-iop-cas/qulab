# -*- coding: utf-8 -*-
"""
Created on Sat Dec 19 16:16:03 2015

@author: Administrator
"""

from AlazarCmd import *
from AlazarApi import *
import numpy as np
import time

class Error(Exception):
    pass

class Wrapper:
    def __init__(self, systemId=1, boardId=1):
        """The init case defines a session ID, used to identify the instrument"""
        # range settings
        self.dRange = {}
        func = getattr(DLL, 'AlazarNumOfSystems')
        func.restype = U32 
        print 'Number of systems:', func()
        func = getattr(DLL, 'AlazarGetBoardBySystemID')
        func.restype = c_void_p
        handle = func(U32(systemId), U32(boardId))
        if handle is None:
            raise Error('Device with system ID=%d and board ID=%d could not be found.' % (systemId, boardId))
        self.handle = handle
        
        
    def testLED(self):
        import time
        self.callFunc('AlazarSetLED', self.handle, U32(1))
        time.sleep(0.1)
        self.callFunc('AlazarSetLED', self.handle, U32(0))


    def callFunc(self, sFunc, *args, **kargs):
        """General function caller with restype=status, also checks for errors"""
        # get function from DLL
        func = getattr(DLL, sFunc)
        func.restype = c_int
        # call function, raise error if needed
        status = func(*args)
        #if 'bIgnoreError' in kargs:
        #    bIgnoreError = kargs['bIgnoreError']
        #else:
        #    bIgnoreError = False
        #if status>512 and not bIgnoreError:
        #    sError = self.getError(status)
        #    raise Error(sError)
        return status

    
    def getError(self, status):
        """Convert the error in status to a string"""
        func = getattr(DLL, 'AlazarErrorToText')
        func.restype = c_char_p 
        # const char* AlazarErrorToText(RETURN_CODE retCode)
        errorText = func(c_int(status))
        return str(errorText)
        
        
    def AlazarBeforeAsyncRead(self, channelMask,         # U32 -- enabled channal mask
                              preTriggerSamples,         # long -- trigger offset
                              samplesPerRecord,          # U32 -- samples per record
                              recordsPerBuffer,          # U32 -- records per buffer
                              recordsPerAcquisition,     # U32 -- records per acquisition
                              flags):                    # U32 -- AutoDMA mode and options
        self.callFunc("AlazarBeforeAsyncRead", self.handle,
                      U32(channelMask), c_long(preTriggerSamples),
                      U32(samplesPerRecord), U32(recordsPerBuffer),
                      U32(recordsPerAcquisition), U32(flags))
                      
                      
    def AlazarPostAsyncBuffer(self,
                              Buffer,            # void* -- buffer pointer
                              BytesPerBuffer):   # U32 -- buffer length in bytes
        self.callFunc("AlazarPostAsyncBuffer", self.handle,
                      byref(Buffer), U32(BytesPerBuffer))
                      
                      
    #RETURN_CODE AlazarStartCapture( HANDLE h);
    def AlazarStartCapture(self):
        self.callFunc('AlazarStartCapture', self.handle)
        
        
    def AlazarWaitAsyncBufferComplete(self, pBuffer, timeout_ms):
        self.callFunc("AlazarWaitAsyncBufferComplete", self.handle,
                      byref(pBuffer), U32(timeout_ms))
                      
                      
    #RETURN_CODE AlazarAbortCapture( HANDLE h);
    def AlazarAbortCapture(self):
        self.callFunc('AlazarAbortCapture', self.handle)


    def AlazarAbortAsyncRead(self):
        self.callFunc('AlazarAbortAsyncRead', self.handle)
        
        
    #RETURN_CODE AlazarSetCaptureClock( HANDLE h, U32 Source, U32 Rate, U32 Edge, U32 Decimation);
    def AlazarSetCaptureClock(self, SourceId, SampleRateId, EdgeId=0, Decimation=0):
        self.callFunc('AlazarSetCaptureClock', self.handle, 
                      U32(SourceId), U32(SampleRateId), U32(EdgeId), U32(Decimation))
                      
                      
    #def AlazarWaitNextAsyncBufferComplete(self,
    #                                      pBuffer, # void* -- buffer to receive data
    #                                      bytesToCopy, # U32 -- bytes to copy into buffer
    #                                      timeout_ms): # U32 -- time to wait for buffer):
    #    return self.callFunc("AlazarWaitNextAsyncBufferComplete", self.handle,
    #                  byref(pBuffer), U32(bytesToCopy), U32(timeout_ms))
    def AlazarWaitNextAsyncBufferComplete(self,
                                          pBuffer, # void* -- buffer to receive data
                                          bytesToCopy, # U32 -- bytes to copy into buffer
                                          timeout_ms): # U32 -- time to wait for buffer):
        func = getattr(DLL, "AlazarWaitNextAsyncBufferComplete")
        func.restype = c_int
        func.argtypes = [HANDLE, c_void_p, U32, U32]
        return func(self.handle, pBuffer, bytesToCopy, timeout_ms)
        
    #RETURN_CODE AlazarSetTriggerOperation(HANDLE h, U32 TriggerOperation
    #            ,U32 TriggerEngine1/*j,K*/, U32 Source1, U32 Slope1, U32 Level1
    #            ,U32 TriggerEngine2/*j,K*/, U32 Source2, U32 Slope2, U32 Level2);
    def AlazarSetTriggerOperation(self, TriggerOperation=0,
                                  TriggerEngine1=0, Source1=0, Slope1=1, Level1=128,
                                  TriggerEngine2=1, Source2=3, Slope2=1, Level2=128):
        self.callFunc('AlazarSetTriggerOperation', self.handle, U32(TriggerOperation),
                      U32(TriggerEngine1), U32(Source1), U32(Slope1), U32(Level1),
                      U32(TriggerEngine2), U32(Source2), U32(Slope2), U32(Level2))
                      
                      
    #RETURN_CODE AlazarInputControl( HANDLE h, U8 Channel, U32 Coupling, U32 InputRange, U32 Impedance);
    def AlazarInputControl(self, Channel, Coupling, InputRange, Impedance):
        # keep track of input range
        #dConv = {12: 4.0, 11: 2.0, 10: 1.0, 7: 0.4, 6: 0.2, 5: 0.1, 2: 0.04}
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
        #self.callFunc('AlazarInputControl', self.handle,
        #              U8(Channel), U32(Coupling), U32(InputRange), U32(Impedance))
        AlazarInputControl(self.handle,
                      Channel, Coupling, InputRange, Impedance)
                      
                      
    #RETURN_CODE AlazarSetExternalTrigger( HANDLE h, U32 Coupling, U32 Range);
    def AlazarSetExternalTrigger(self, Coupling, Range=0):
        self.callFunc('AlazarSetExternalTrigger', self.handle, U32(Coupling), U32(Range))
        
    def AlazarGetChannelInfo(self):
        MemorySizeInSamples, BitsPerSample = U32(), U8()
        AlazarGetChannelInfo(self.handle, MemorySizeInSamples, BitsPerSample)
        return MemorySizeInSamples.value, BitsPerSample.value
        
    def init(self, max_input = 1.0):
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
        
        self.AlazarSetCaptureClock(SourceId=EXTERNAL_CLOCK_10MHz_REF, SampleRateId=SAMPLE_RATE_1GSPS)
        self.AlazarInputControl(CHANNEL_A, DC_COUPLING, input_range, IMPEDANCE_50_OHM)
        self.AlazarInputControl(CHANNEL_B, DC_COUPLING, input_range, IMPEDANCE_50_OHM)
        self.AlazarSetExternalTrigger(DC_COUPLING)
        self.AlazarSetTriggerOperation(TriggerOperation=TRIG_ENGINE_OP_J,
                                       TriggerEngine1=TRIG_ENGINE_J, Source1=TRIG_EXTERNAL, Slope1=TRIGGER_SLOPE_POSITIVE, Level1=int(128+127*0.5/5.0),
                                       TriggerEngine2=TRIG_ENGINE_K, Source2=TRIG_DISABLE, Slope2=TRIGGER_SLOPE_POSITIVE, Level2=128)
                                  
                                  
    def _get_Traces(self, buf, bitsPerSample, recordsPerBuffer, bytesPerHeader):
        codeZero = 2 ** (float(bitsPerSample) - 1) - 0.5
        codeRange = 2 ** (float(bitsPerSample) - 1) - 0.5
        
        lenPerRecord = len(buf) / recordsPerBuffer
        #samplesPerRecord = lenPerRecord - 16
        
        buf = np.array(buf).reshape(recordsPerBuffer, lenPerRecord)
        
        chA = self.dRange[CHANNEL_A]*(buf[0::2, bytesPerHeader:]-codeZero)/codeRange
        chB = self.dRange[CHANNEL_B]*(buf[1::2, bytesPerHeader:]-codeZero)/codeRange
        #chA = self.dRange[CHANNEL_A]*(buf[:recordsPerBuffer/2, bytesPerHeader:]-codeZero)/codeRange
        #chB = self.dRange[CHANNEL_B]*(buf[recordsPerBuffer/2:, bytesPerHeader:]-codeZero)/codeRange
        
        return chA, chB
        
    def get_Traces(self, samplesPerRecord=1024, repeats=1000):
        n = samplesPerRecord
        samplesPerRecord = 1
        while samplesPerRecord < n:
            samplesPerRecord <<= 1
            
        recordsPerBuffer = 100 if repeats > 50 else repeats*2
        recordsPerAcquisition = 5000 if repeats > 2500 else repeats*2
        _, bitsPerSample = self.AlazarGetChannelInfo()
        
        uFlags = ADMA_TRADITIONAL_MODE | ADMA_ALLOC_BUFFERS | ADMA_EXTERNAL_STARTCAPTURE
        
        bytesPerHeader = 0
        BytesPerBuffer = (samplesPerRecord+bytesPerHeader)*recordsPerBuffer
        self.AlazarBeforeAsyncRead(CHANNEL_A | CHANNEL_B,
                                    0, samplesPerRecord, recordsPerBuffer,
                                    recordsPerAcquisition,
                                    uFlags)
        
        Buffer = (c_uint8*BytesPerBuffer)()
    
        ret = ([],[])
    
        Times = 0
    
        time_out_ms = 10
        max_time_out_ms = 1000
    
        self.AlazarStartCapture()
        while Times < repeats:
            try:
                retCode = self.AlazarWaitNextAsyncBufferComplete(Buffer, BytesPerBuffer, time_out_ms)
                if retCode == 579: # ApiWaitTimeout (579)
                    time_out_ms += 1
                    if time_out_ms > max_time_out_ms:
                        self.AlazarAbortAsyncRead()
                        raise Error("Alazer Timeout")
                    continue
                if retCode == 589: # ApiTransferComplete (589)
                    self.AlazarStartCapture()
                    continue
                #if retCode == 589: # ApiBufferOverflow (582) ApiTransferComplete (589)
                #    continue
                if retCode != 512:  # ApiBufferNotReady (573)
                    #print retCode
                    self.AlazarAbortAsyncRead()
                    time.sleep(0.01)
                    self.AlazarBeforeAsyncRead(CHANNEL_A | CHANNEL_B,
                                    0, samplesPerRecord, recordsPerBuffer,
                                    recordsPerAcquisition,
                                    uFlags)
                    self.AlazarStartCapture()
                    continue
                ch1, ch2 = self._get_Traces(Buffer, bitsPerSample, recordsPerBuffer, bytesPerHeader)
                ret[0].extend(list(ch1[:,:n]))
                ret[1].extend(list(ch2[:,:n]))
                Times = len(ret[0])
            except:
                raise
    
        self.AlazarAbortAsyncRead()
    
        return ret
        
        
    def get_IQ(self, samplesPerRecord=1024, repeats=1000, heterodyne_freq=50e6):
        n = samplesPerRecord
        samplesPerRecord = 1
        while samplesPerRecord < n:
            samplesPerRecord <<= 1
            
        recordsPerBuffer = 100 if repeats > 50 else repeats*2
        recordsPerAcquisition = 5000 if repeats > 2500 else repeats*2
        _, bitsPerSample = self.AlazarGetChannelInfo()
        
        uFlags = ADMA_TRADITIONAL_MODE | ADMA_ALLOC_BUFFERS | ADMA_EXTERNAL_STARTCAPTURE
        
        bytesPerHeader = 0
        BytesPerBuffer = (samplesPerRecord+bytesPerHeader)*recordsPerBuffer
        self.AlazarBeforeAsyncRead(CHANNEL_A | CHANNEL_B,
                                    0, samplesPerRecord, recordsPerBuffer,
                                    recordsPerAcquisition,
                                    uFlags)
        
        Buffer = (c_uint8*BytesPerBuffer)()
    
        ret = []
        t = np.arange(0, n, 1) * 1e-9
        Exp = np.exp(1j*2*np.pi*heterodyne_freq*t)
        
        Times = 0
    
        time_out_ms = 10
        max_time_out_ms = 1000
    
        self.AlazarStartCapture()
        while Times < repeats:
            try:
                retCode = self.AlazarWaitNextAsyncBufferComplete(Buffer, BytesPerBuffer, time_out_ms)
                if retCode == 579: # ApiWaitTimeout (579)
                    time_out_ms += 1
                    if time_out_ms > max_time_out_ms:
                        self.AlazarAbortAsyncRead()
                        raise Error("Alazer Timeout")
                    continue
                if retCode == 589: # ApiTransferComplete (589)
                    self.AlazarStartCapture()
                    continue
                #if retCode == 589: # ApiBufferOverflow (582) ApiTransferComplete (589)
                #    continue
                if retCode != 512:  # ApiBufferNotReady (573)
                    #print retCode
                    self.AlazarAbortAsyncRead()
                    time.sleep(0.01)
                    self.AlazarBeforeAsyncRead(CHANNEL_A | CHANNEL_B,
                                    0, samplesPerRecord, recordsPerBuffer,
                                    recordsPerAcquisition,
                                    uFlags)
                    self.AlazarStartCapture()
                    continue
                ch1, ch2 = self._get_Traces(Buffer, bitsPerSample, recordsPerBuffer, bytesPerHeader)
                I, Q = (ch1[:,:n]*Exp).mean(axis=1), (ch2[:,:n]*Exp).mean(axis=1)
                ret.extend(list(np.array([I, Q]).T))
                Times = len(ret)
            except:
                raise
    
        self.AlazarAbortAsyncRead()
    
        return np.array(ret)
    
    #RETURN_CODE  AlazarSetTriggerDelay( HANDLE h, U32 Delay);
    def AlazarSetTriggerDelay(self, Delay=0):
        self.callFunc('AlazarSetTriggerDelay', self.handle, U32(Delay))
    

    #RETURN_CODE  AlazarSetTriggerTimeOut( HANDLE h, U32 to_ns);
    def AlazarSetTriggerTimeOut(self, time=0.0):
        tick = U32(int(time*1E5))
        self.callFunc('AlazarSetTriggerTimeOut', self.handle, tick)


    #RETURN_CODE AlazarSetRecordSize( HANDLE h, U32 PreSize, U32 PostSize);
    def AlazarSetRecordSize(self, PreSize, PostSize):
        self.nPreSize = int(PreSize)
        self.nPostSize = int(PostSize)
        self.callFunc('AlazarSetRecordSize', self.handle, U32(PreSize), U32(PostSize))


    #RETURN_CODE AlazarSetRecordCount( HANDLE h, U32 Count);
    def AlazarSetRecordCount(self, Count):
        self.nRecord = int(Count)
        self.callFunc('AlazarSetRecordCount', self.handle, U32(Count))
        

    #U32	AlazarBusy( HANDLE h);
    def AlazarBusy(self):
        # get function from DLL
        func = getattr(DLL, 'AlazarBusy')
        func.restype = U32
        # call function, return result
        return bool(func(self.handle))
    
    def AlazarRead(self, Channel, Buffer, ElementSize, Record, TransferOffset, TransferLength):
        self.callFunc('AlazarRead', self.handle,
                      U32(Channel), byref(Buffer), c_int(ElementSize),
                      c_long(Record), c_long(TransferOffset), U32(TransferLength))


    def _readTraces(self, Channel, samplesPerRecord=1024, repeats=1000):
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
        
    def get_Traces2(self, samplesPerRecord=1024, repeats=1000, timeout = 10):
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
            
        return (self._readTraces(CHANNEL_A, samplesPerRecord, repeats),
                self._readTraces(CHANNEL_B, samplesPerRecord, repeats))


if __name__ == "__main__":    
    Digitizer = Wrapper()
    Digitizer.init()
    
    samplesPerRecord = 1000
    
    ch1, ch2 = Digitizer.get_Traces(samplesPerRecord, 1000)
    
    chA = np.array(ch1[:]).mean(axis=0)
    chB = np.array(ch2[:]).mean(axis=0)
    
    import matplotlib.pyplot as plt
    from matplotlib import animation
    
    #for i in range(60):
    #    plt.plot(ch1[i])
    #plt.plot(chA)
    
    fig = plt.figure(figsize=(16,5))
    ax1 = fig.add_subplot(131)
    
    x = np.linspace(0, len(chA)-1, len(chA))
    
    #lines = []
    
    #for i in range(int(len(ch1)/3)):
    #    line, = ax.plot(x, ch1[i*3])
    #    lines.append(line)
    #line1, = ax.plot(x, ch1[0])
    lineAvgA, = ax1.plot(x,chA)
    lineAvgB, = ax1.plot(x,chB)
    
    ax2 = fig.add_subplot(132)
    Is = [0 for i in range(1000)]
    Qs = [0 for i in range(1000)]
    ax2.set_xlim(-0.2, 0.2)
    ax2.set_ylim(-0.2, 0.2)
    ax2.grid()
    
    iq, = ax2.plot(Is, Qs, '.r', alpha=0.02)
    IQ, = ax2.plot(Is, Qs, '.b', alpha=0.3)
    
    ax3 = fig.add_subplot(133)
    
    ax3.set_xlim(-0.2, 0.2)
    ax3.set_ylim(-0.2, 0.2)
    ax3.grid()
    Is2 = [0 for i in range(1000)]
    Qs2 = [0 for i in range(1000)]
    iq2, = ax3.plot(Is2, Qs2, '.r', alpha=0.02)
    IQ2, = ax3.plot(Is2, Qs2, '.b', alpha=0.3)
    
    
    heterodyne_freq = 50e6
    t = np.arange(0, samplesPerRecord, 1)*1e-9
    Exp = np.exp(1j*2*np.pi*heterodyne_freq*t)
    
    def gen():
        i = 0
        while True:
            yield i
            i = (i+1)%10000
            #if i > 1000:
            #    break
            
    def animate(i):
        ch1, ch2 = Digitizer.get_Traces(samplesPerRecord, 100)
        chA = np.array(ch1[:]).mean(axis=0)
        chB = np.array(ch2[:]).mean(axis=0)
        #for i in range(int(len(ch1)/3)):
        #    lines[i].set_ydata(ch1[3*i])
        lineAvgA.set_ydata(chA)
        lineAvgB.set_ydata(chB)
        
        A = (ch1*Exp).mean(axis=1) + 0j*(ch2*Exp).mean(axis=1)
        
        I, Q = np.real(A), np.imag(A)
        
        Is.extend(list(I))
        Qs.extend(list(Q))
        
        while len(Is) > 3000:
            Is.pop(0)
            Qs.pop(0)
        IQ.set_xdata(np.array(Is[-101:]))
        IQ.set_ydata(np.array(Qs[-101:]))
        iq.set_xdata(Is)
        iq.set_ydata(Qs)
        
        A = ((ch1*Exp).mean(axis=1) + 1j*(ch2*Exp).mean(axis=1))/2
        
        I, Q = np.real(A), np.imag(A)
        
        Is2.extend(list(I))
        Qs2.extend(list(Q))
        
        while len(Is2) > 3000:
            Is2.pop(0)
            Qs2.pop(0)
        IQ2.set_xdata(np.array(Is2[-101:]))
        IQ2.set_ydata(np.array(Qs2[-101:]))
        iq2.set_xdata(Is2)
        iq2.set_ydata(Qs2)
        
        return lineAvgA, lineAvgB, IQ, iq, IQ2, iq2
        
    anim=animation.FuncAnimation(fig, animate, gen(), interval=100)
    plt.show()
    plt.rcParams['animation.ffmpeg_path'] = 'C:/python27/ffmpeg.exe'
    FFwriter = animation.FFMpegWriter()
    #anim.save("test.mp4", writer = FFwriter, fps=30, extra_args=['-vcodec', 'libx264'])
