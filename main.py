from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import BinarySystem as BS
import TowerSpecifications as TS


biSys = BS.BinarySystem("n-butane", "n-heptane")
towSpec = TS.TowerSpecs(0.5, 0.1, 0.4, 0.95, 0.3)


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.left = 50
        self.top = 50
        self.title = 'Separations Diagram Generator'
        self.width = 640
        self.height = 400
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        m = PlotCanvas(self, width=5, height=4)
        m.move(140, 0)

        # USE DOCKWIDGET
        QDockWidget("Welp...", self)
        

        self.show()


class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, type="Txy", dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot(type)

    def plot(self, type):
        ax = self.figure.add_subplot(111)
        if type == "Txy":
            biSys.plot_Txy_diagram(ax)
        elif type == "VLE":
            biSys.plot_vapor_liquid_equilibrium_diagram(ax)
        elif type == "Distillation":
            biSys.plot_reflux_distillation_diagram(towSpec, ax)
        self.draw()


def update_graph():
    alert = QMessageBox()
    alert.setText('We need more pylons first!')
    alert.exec()


app = QApplication([])
ex = App()
exit(app.exec_())
