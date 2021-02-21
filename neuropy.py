# Copyright (c) 2013, sahil singh
# Updated to work with python3.8, autodetection added,
# and callback fixes, by Jordan Jarvis.
##

import serial
import time
import sys
from threading import Thread

# Byte codes
CONNECT = '\xc0'
DISCONNECT = '\xc1'
AUTOCONNECT = '\xc2'
SYNC = '\xaa'
EXCODE = '\x55'
POOR_SIGNAL = '\x02'
ATTENTION = '\x04'
MEDITATION = '\x05'
BLINK = '\x16'
HEADSET_CONNECTED = '\xd0'
HEADSET_NOT_FOUND = '\xd1'
HEADSET_DISCONNECTED = '\xd2'
REQUEST_DENIED = '\xd3'
STANDBY_SCAN = '\xd4'
RAW_VALUE = '\x80'

class Neuropy(object):
    """NeuroPy libraby, to get data from neurosky mindwave.
    Initialising: object1=NeuroPy("COM6",57600) #windows
    After initialising , if required the callbacks must be set
    then using the start method the library will start fetching data from mindwave
    i.e. object1.start()
    similarly stop method can be called to stop fetching the data
    i.e. object1.stop()
    The data from the device can be obtained using either of the following methods or both of them together:
    Obtaining value: variable1=object1.attention #to get value of attention
    #other variables: attention,meditation,rawValue,delta,theta,lowAlpha,highAlpha,lowBeta,highBeta,lowGamma,midGamma, poorSignal and blinkStrength
    Setting callback:a call back can be associated with all the above variables so that a function is called when the variable is updated. Syntax: setCallBack("variable",callback_function)
    for eg. to set a callback for attention data the syntax will be setCallBack("attention",callback_function)"""
    __attention = 0
    __meditation = 0
    __rawValue = 0
    __delta = 0
    __theta = 0
    __lowAlpha = 0
    __highAlpha = 0
    __lowBeta = 0
    __highBeta = 0
    __lowGamma = 0
    __midGamma = 0
    __poorSignal = 0
    __blinkStrength = 0

    callBacksDictionary = {}  # keep a track of all callbacks

    def __init__(self, port = None, baudRate=57600, devid=None):
        if port == None:
            platform = sys.platform
            if platform == "win32":
                port = "COM6"
            elif platform.startswith("linux") or platform == 'darwin':
                port = "/dev/rfcomm0"

        self.__devid = devid
        self.__serialPort = port
        self.__serialBaudRate = baudRate
        self.__packetsReceived = 0

        self.__parserThread = None
        self.__threadRun = False
        self.__srl = None
        self.__connected = False

    def __del__(self):
        if self.__threadRun == True:
            self.stop()

    def disconnect(self):
        self.__srl.write(DISCONNECT)

    def connect(self):
        if not self.__devid:
            self.__connected = True
            return # Only connect RF devices

        self.__srl.write(''.join([CONNECT, self.__devid.decode('hex')]))

    def start(self):
        # Try to connect to serial port and start a separate thread
        # for data collection
        if self.__threadRun == True:
            print("Mindwave has already started!")
            return

        if self.__srl == None:
            try:
                self.__srl = serial.Serial(
                    self.__serialPort, self.__serialBaudRate)
            except serial.serialutil.SerialException as e:
                print(str(e))
                return
        else:
            self.__srl.open()

        self.__srl.flushInput()

        if self.__devid:
            self.connect();

        self.__packetsReceived = 0
        self.__parserThread = Thread(target=self.__packetParser, args=())
        self.__threadRun = True
        self.__parserThread.start()

    def __packetParser(self):
        "packetParser runs continously in a separate thread to parse packets from mindwave and update the corresponding variables"
        while self.__threadRun:
            p1 = self.__srl.read(1).hex()  # read first 2 packets
            p2 = self.__srl.read(1).hex()
            while (p1 != 'aa' or p2 != 'aa') and self.__threadRun:
                p1 = p2
                p2 = self.__srl.read(1).hex()
            else:
                if self.__threadRun == False:
                    break
                # a valid packet is available
                self.__packetsReceived += 1
                payload = []
                checksum = 0
                payloadLength = int(self.__srl.read(1).hex(), 16)
                for i in range(payloadLength):
                    tempPacket = self.__srl.read(1).hex()
                    payload.append(tempPacket)
                    checksum += int(tempPacket, 16)
                checksum = ~checksum & 0x000000ff
                if checksum == int(self.__srl.read(1).hex(), 16):
                    i = 0

                    while i < payloadLength:
                        code = payload[i]
                        if (code == 'd0'):
                            print("Headset connected!")
                            self.__connected = True
                        elif (code == 'd1'):
                            print("Headset not found, reconnecting")
                            self.connect()
                        elif(code == 'd2'):
                            print("Disconnected!")
                            self.connect()
                        elif(code == 'd3'):
                            print("Headset denied operation!")
                        elif(code == 'd4'):
                            if payload[2] == 0 and not self.__connected:
                                print("Idle, trying to reconnect");
                                self.connect();
                        elif(code == '02'):  # poorSignal
                            i = i + 1
                            self.poorSignal = int(payload[i], 16)
                        elif(code == '04'):  # attention
                            i = i + 1
                            self.attention = int(payload[i], 16)
                        elif(code == '05'):  # meditation
                            i = i + 1
                            self.meditation = int(payload[i], 16)
                        elif(code == '16'):  # blink strength
                            i = i + 1
                            self.blinkStrength = int(payload[i], 16)
                        elif(code == '80'):  # raw value
                            i = i + 1  # for length/it is not used since length =1 byte long and always=2
                            i = i + 1
                            val0 = int(payload[i], 16)
                            i = i + 1
                            self.rawValue = val0 * 256 + int(payload[i], 16)
                            if self.rawValue > 32768:
                                self.rawValue = self.rawValue - 65536
                        elif(code == '83'):  # ASIC_EEG_POWER
                            i = i + 1  # for length/it is not used since length =1 byte long and always=2
                            # delta:
                            i = i + 1
                            val0 = int(payload[i], 16)
                            i = i + 1
                            val1 = int(payload[i], 16)
                            i = i + 1
                            self.delta = val0 * 65536 + \
                                val1 * 256 + int(payload[i], 16)
                            # theta:
                            i = i + 1
                            val0 = int(payload[i], 16)
                            i = i + 1
                            val1 = int(payload[i], 16)
                            i = i + 1
                            self.theta = val0 * 65536 + \
                                val1 * 256 + int(payload[i], 16)
                            # lowAlpha:
                            i = i + 1
                            val0 = int(payload[i], 16)
                            i = i + 1
                            val1 = int(payload[i], 16)
                            i = i + 1
                            self.lowAlpha = val0 * 65536 + \
                                val1 * 256 + int(payload[i], 16)
                            # highAlpha:
                            i = i + 1
                            val0 = int(payload[i], 16)
                            i = i + 1
                            val1 = int(payload[i], 16)
                            i = i + 1
                            self.highAlpha = val0 * 65536 + \
                                val1 * 256 + int(payload[i], 16)
                            # lowBeta:
                            i = i + 1
                            val0 = int(payload[i], 16)
                            i = i + 1
                            val1 = int(payload[i], 16)
                            i = i + 1
                            self.lowBeta = val0 * 65536 + \
                                val1 * 256 + int(payload[i], 16)
                            # highBeta:
                            i = i + 1
                            val0 = int(payload[i], 16)
                            i = i + 1
                            val1 = int(payload[i], 16)
                            i = i + 1
                            self.highBeta = val0 * 65536 + \
                                val1 * 256 + int(payload[i], 16)
                            # lowGamma:
                            i = i + 1
                            val0 = int(payload[i], 16)
                            i = i + 1
                            val1 = int(payload[i], 16)
                            i = i + 1
                            self.lowGamma = val0 * 65536 + \
                                val1 * 256 + int(payload[i], 16)
                            # midGamma:
                            i = i + 1
                            val0 = int(payload[i], 16)
                            i = i + 1
                            val1 = int(payload[i], 16)
                            i = i + 1
                            self.midGamma = val0 * 65536 + \
                                val1 * 256 + int(payload[i], 16)
                        else:
                            pass
                        i = i + 1

    def stop(self):
        # Stops a running parser thread
        if self.__threadRun == True:
            self.__threadRun = False
            self.__parserThread.join()
            self.__srl.close()

    def setCallBack(self, variable_name, callback_function):
        """Setting callback:a call back can be associated with all the above variables so that a function is called when the variable is updated. Syntax: setCallBack("variable",callback_function)
           for eg. to set a callback for attention data the syntax will be setCallBack("attention",callback_function)"""
        self.callBacksDictionary[variable_name] = callback_function

    # setting getters and setters for all variables

    # packets received
    @property
    def packetsReceived(self):
        return self.__packetsReceived

    @property
    def bytesAvailable(self):
        if self.__threadRun:
            return self.__srl.inWaiting()
        else:
            return -1

    # attention
    @property
    def attention(self):
        "Get value for attention"
        return self.__attention

    @attention.setter
    def attention(self, value):
        self.__attention = value
        # if callback has been set, execute the function
        if "attention" in self.callBacksDictionary:
            self.callBacksDictionary["attention"](self.__attention)

    # meditation
    @property
    def meditation(self):
        "Get value for meditation"
        return self.__meditation

    @meditation.setter
    def meditation(self, value):
        self.__meditation = value
        # if callback has been set, execute the function
        if "meditation" in self.callBacksDictionary:
            self.callBacksDictionary["meditation"](self.__meditation)

    # rawValue
    @property
    def rawValue(self):
        "Get value for rawValue"
        return self.__rawValue

    @rawValue.setter
    def rawValue(self, value):
        self.__rawValue = value
        # if callback has been set, execute the function
        if "rawValue" in self.callBacksDictionary:
            self.callBacksDictionary["rawValue"](self.__rawValue)

    # delta
    @property
    def delta(self):
        "Get value for delta"
        return self.__delta

    @delta.setter
    def delta(self, value):
        self.__delta = value
        # if callback has been set, execute the function
        if "delta" in self.callBacksDictionary:
            self.callBacksDictionary["delta"](self.__delta)

    # theta
    @property
    def theta(self):
        "Get value for theta"
        return self.__theta

    @theta.setter
    def theta(self, value):
        self.__theta = value
        # if callback has been set, execute the function
        if "theta" in self.callBacksDictionary:
            self.callBacksDictionary["theta"](self.__theta)

    # lowAlpha
    @property
    def lowAlpha(self):
        "Get value for lowAlpha"
        return self.__lowAlpha

    @lowAlpha.setter
    def lowAlpha(self, value):
        self.__lowAlpha = value
        # if callback has been set, execute the function
        if "lowAlpha" in self.callBacksDictionary:
            self.callBacksDictionary["lowAlpha"](self.__lowAlpha)

    # highAlpha
    @property
    def highAlpha(self):
        "Get value for highAlpha"
        return self.__highAlpha

    @highAlpha.setter
    def highAlpha(self, value):
        self.__highAlpha = value
        # if callback has been set, execute the function
        if "highAlpha" in self.callBacksDictionary:
            self.callBacksDictionary["highAlpha"](self.__highAlpha)

    # lowBeta
    @property
    def lowBeta(self):
        "Get value for lowBeta"
        return self.__lowBeta

    @lowBeta.setter
    def lowBeta(self, value):
        self.__lowBeta = value
        # if callback has been set, execute the function
        if "lowBeta" in self.callBacksDictionary:
            self.callBacksDictionary["lowBeta"](self.__lowBeta)

    # highBeta
    @property
    def highBeta(self):
        "Get value for highBeta"
        return self.__highBeta

    @highBeta.setter
    def highBeta(self, value):
        self.__highBeta = value
        # if callback has been set, execute the function
        if "highBeta" in self.callBacksDictionary:
            self.callBacksDictionary["highBeta"](self.__highBeta)

    # lowGamma
    @property
    def lowGamma(self):
        "Get value for lowGamma"
        return self.__lowGamma

    @lowGamma.setter
    def lowGamma(self, value):
        self.__lowGamma = value
        # if callback has been set, execute the function
        if "lowGamma" in self.callBacksDictionary:
            self.callBacksDictionary["lowGamma"](self.__lowGamma)

    # midGamma
    @property
    def midGamma(self):
        "Get value for midGamma"
        return self.__midGamma

    @midGamma.setter
    def midGamma(self, value):
        self.__midGamma = value
        # if callback has been set, execute the function
        if "midGamma" in self.callBacksDictionary:
            self.callBacksDictionary["midGamma"](self.__midGamma)

    # poorSignal
    @property
    def poorSignal(self):
        "Get value for poorSignal"
        return self.__poorSignal

    @poorSignal.setter
    def poorSignal(self, value):
        self.__poorSignal = value
        # if callback has been set, execute the function
        if "poorSignal" in self.callBacksDictionary:
            self.callBacksDictionary["poorSignal"](self.__poorSignal)

    # blinkStrength
    @property
    def blinkStrength(self):
        "Get value for blinkStrength"
        return self.__blinkStrength

    @blinkStrength.setter
    def blinkStrength(self, value):
        self.__blinkStrength = value
        # if callback has been set, execute the function
        if "blinkStrength" in self.callBacksDictionary:
            self.callBacksDictionary["blinkStrength"](self.__blinkStrength)
from time import sleep

neuropy = Neuropy("COM5",57600) 
import datetime as dt
class dataObject():
    def __init__(self):
        neuropy.start()
        self.queue = []
        self.queueSize = 100
        self.attention = 0
        self.meditation = 0
        self.rawValue = 0
        self.delta = 0
        self.theta = 0
        self.lowAlpha = 0
        self.highAlpha = 0
        self.lowBeta = 0
        self.highBeta = 0
        self.lowGamma = 0
        self.midGamma = 0
        self.poorSignal = 0
        self.blinkStrength = 0


        neuropy.setCallBack("attention", self.attention_callback)

    def plot(self):
        while len(self.queue) == 0:
            sleep(0.2)
        style.use('fivethirtyeight')

        fig = plt.figure()
        ax1 = fig.add_subplot(1,1,1)
        def animate(i):
            ax1.clear()
            ax1.plot(self.queue[:][11], self.queue[:][0])
        ani = animation.FuncAnimation(fig, animate, interval=1000)
        plt.show()

    def attention_callback(self, attention_value):
        self.attention = attention_value
        self.meditation = neuropy.meditation
        self.rawValue = neuropy.rawValue
        self.delta = neuropy.delta
        self.theta = neuropy.theta
        self.lowAlpha = neuropy.lowAlpha
        self.highAlpha = neuropy.highAlpha
        self.lowBeta = neuropy.lowBeta
        self.highBeta = neuropy.highBeta
        self.lowGamma = neuropy.lowGamma
        self.midGamma = neuropy.midGamma
        self.add_to_queue()
    
    def add_to_queue(self):
        print("adding values to queue", self.theta)
        self.queue.append([int(self.attention),
        int(self.meditation ),
        int(self.rawValue ),
        int(self.delta ),
        int(self.theta ),
        int(self.lowAlpha ),
        int(self.highAlpha ),
        int(self.lowBeta ),
        int(self.highBeta ),
        int(self.lowGamma ),
        int(self.midGamma),
        dt.datetime.now().strftime('%H:%M:%S.%f')])
        if len(self.queue) > self.queueSize:
            self.queue.pop(0)
            print("the queue is full")

    

    
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import keyboard
obj = dataObject()
#obj.plot()
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 10)
print(x)
for i in range(1, 6):
    plt.plot(x, i * x + i, label='$y = {i}x + {i}$'.format(i=i))
x = [3,5,1,4,6,7]
i=1
plt.plot([1,2,3,4,5,6],x)
f = 1
while f !=0:
    sleep(0.5)
    if keyboard.is_pressed('1'):
        print ('Option 1\n')
        break
fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)

def animate(i):

    xs,ys = list(range(0,len(np.array(obj.queue)[:,0]))),np.array(obj.queue)[:,0].astype(np.float)


    ax1.clear()
    ax1.plot(xs, ys)
x,y = list(range(0,len(np.array(obj.queue)[:,0]))),np.array(obj.queue)[:,0].astype(np.float)
print(x,y)
plt.plot(x,y)

plt.legend(loc='best')
ani = animation.FuncAnimation(fig, animate, interval=1000)
plt.show()
while True:
    #game loop
    # for event in pygame.event.get():
    #     if event.type == pygame.QUIT:
    #         neuropy.stop()
    #         running = False
    #         pygame.quit()
    #         exit()
    sleep(0.2)

