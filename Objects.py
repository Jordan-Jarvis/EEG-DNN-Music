## By Jordan Jarvis
# Contains initial data collection method and structure for the 
# EEG readings and their label values. Plots the data as it 
# comes in using callbacks
from NerPy import Neuropy
import pandas as pd
from time import sleep
import numpy as np
global neuropy
neuropy = Neuropy("COM5",57600) 
import datetime as dt
class dataObject():
    def __init__(self):
        neuropy.start()
        self.queue = []
        self.queueSize = 30
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
        self.queue.append([float(self.attention),
        float(self.meditation ),
        float(self.rawValue ),
        float(self.delta ),
        float(self.theta ),
        float(self.lowAlpha ),
        float(self.highAlpha ),
        float(self.lowBeta ),
        float(self.highBeta ),
        float(self.lowGamma ),
        float(self.midGamma)])
        if len(self.queue) > self.queueSize:
            self.queue.pop(0)
            print("the queue is full")

    def get_queue(self):
        tmp = np.array(self.queue)
        df = pd.DataFrame({"Attention":tmp[:,0],
            "Meditation":tmp[:,1],
            "RawValue":tmp[:,2],
            "Delta":tmp[:,3],
            "Theta":tmp[:,4],
            "LowAlpha":tmp[:,5],
            "HighAlpha":tmp[:,6],
            "LowBeta":tmp[:,7],
            "HighBeta":tmp[:,8],
            "LowGamma":tmp[:,9],
            "MidGamma":tmp[:,10]
            })
        return df

def NormalizeData(data):
    return (data - np.min(data)) / (np.max(data) - np.min(data))

if __name__ == '__main__':
    '''Test the objects by showing data'''
    
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    from matplotlib import style
    import keyboard
    obj = dataObject()
    #obj.plot()
    import matplotlib.pyplot as plt
    import numpy as np

    f = 1
    while f !=0:
        sleep(0.5)
        if keyboard.is_pressed('1'):
            print ('Option 1\n')
            break
    fig = plt.figure()
    ax1 = fig.add_subplot(1,1,1)
    labels = []
    def animate(i):
        labels = []
        ax1.clear()
        ax1.set_ylabel("Activity Frequencies%")
        ax1.set_xlabel("Readings")
        que = obj.get_queue()
        for i, val in enumerate(que):
            if i %2 == 0:
                continue
            print(que[val])
            labels.append(val)
            xs,ys = list(range(0,len(que[val]))),NormalizeData(que[val])
            ax1.plot(xs, ys)
        plt.legend(labels, loc='upper left', bbox_to_anchor=(0.25, 0.85))



    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
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

