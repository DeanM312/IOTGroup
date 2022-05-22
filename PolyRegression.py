import numpy as np
import matplotlib.pyplot as plt

class PolyRegression:
    def __init__(self):
        pass

    def getModel(self, x, y):
        return np.poly1d(np.polyfit(x, y, 3))

    def savePlot(self, name, x, y, model):
        line = np.linspace(min(x), max(x) + 10, 100)
        plt.clf()
        plt.axis([min(line), max(line), 0, 50])
        plt.scatter(x, y)
        plt.plot(line, model(line))
        plt.savefig(name + '.png')

    def predict(self, x, y, name):
        model = self.getModel(x, y)
        self.savePlot('fig', x, y, model)
