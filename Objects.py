## By Jordan Jarvis
# Contains initial data collection method and structure for the 
# EEG readings and their label values. Plots the data as it 
# comes in using callbacks
from NerPy import Neuropy
import pandas as pd
from time import sleep
import numpy as np
import multiprocessing as mp
global neuropy
neuropy = Neuropy("COM5",57600) 
import datetime as dt
class dataObject():
    def __init__(self):
        neuropy.start()
        self.queue = mp.Queue()
        self.queueSize = 10
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
        self.threads = []

        neuropy.setCallBack("attention", self.attention_callback)

    def attention_callback(self, attention_value):
        self.attention = neuropy.attention
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
        #print("adding values to queue", self.theta)
        if self.rawValue > 10000:
            rawValue = self.rawValue/10000
        else:
            rawValue = self.rawValue
        self.queue.put([float(self.attention),
        float(self.meditation ),
        float(rawValue ),
        float(self.delta ),
        float(self.theta ),
        float(self.lowAlpha ),
        float(self.highAlpha ),
        float(self.lowBeta ),
        float(self.highBeta ),
        float(self.lowGamma ),
        float(self.midGamma)])
        if self.queue.qsize() > self.queueSize:
            self.queue.pop()
            #print("the queue is full")

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

    def showqueue(self):
        print(self.queue)

    def showGraphThread(self, labels: dict, interval=1000):
        
        graphThread = mp.Process(target=self.showGraph, args=(labels, interval))
        graphThread.start()
        self.threads.append(graphThread)

    def showGraph(self, labels: dict, interval=1000):
        import matplotlib.pyplot as plt
        import matplotlib.animation as animation
        '''Shows specified labels (columns) from the dict on the graph'''
        print("showing graph")
        fig = plt.figure()
        ax1 = fig.add_subplot(1,1,1)

        def animate(i):

            ax1.clear()
            ax1.set_ylabel("Activity Frequencies%")
            ax1.set_xlabel("Readings")
            que = self.get_queue()

            for val in labels:
                
                xs,ys = list(range(0,len(que[val]))),que[val]
                print(val)
                ax1.plot(xs, ys)
            plt.legend(labels, loc='upper left', bbox_to_anchor=(0.25, 0.85))
        ani = animation.FuncAnimation(fig, animate, interval=interval)
        plt.show()
        return ani

def NormalizeData(data):
    return (data - np.min(data)) / (np.max(data) - np.min(data))









if __name__ == '__main__':
    '''Test the objects by showing data'''
    
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    from matplotlib import style
    obj = dataObject()
    #obj.plot()
    import matplotlib.pyplot as plt
    import numpy as np
    
    data = dataObject()
    while data.queue.qsize() < 10:
        sleep(0.2)
    print("live")

    data.showGraphThread({"Attention"}, interval=1000)
    data.showGraph({"Meditation"}, interval=1000)
    while True:
        #game loop
        # for event in pygame.event.get():
        #     if event.type == pygame.QUIT:
        #         neuropy.stop()
        #         running = False
        #         pygame.quit()
        #         exit()
        sleep(0.2)

