import sys
from PyQt5.QtWidgets import QApplication

import UI
import BinarySystem as BS
import TowerSpecifications as TS

# Initial System Conditions
light_chemical = "ethanol"
heavy_chemical = "n-nonane"
R = 2.5
xB = 0.1
xF = 0.4
xD = 0.95
murphree = 0.95
# Objects for generating plots
tower_specs = TS.TowerSpecs(R, xB, xF, xD, murphree)
binary_system = BS.BinarySystem(light_chemical, heavy_chemical)


def activate_UI():
    """Activates the UI"""
    app = QApplication([])
    UI.Window(binary_system, tower_specs)
    sys.exit(app.exec_())


activate_UI()