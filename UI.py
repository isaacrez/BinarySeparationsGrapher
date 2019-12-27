import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QDoubleValidator, QFont
from PyQt5.QtCore import QCoreApplication, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import BinarySystem as BS
import TowerSpecifications as TS

light_chemical = "ethanol"
heavy_chemical = "n-nonane"
R = 2.5
xB = 0.1
xF = 0.4
xD = 0.95
murphree = 0.95

towSpec = TS.TowerSpecs(R, xB, xF, xD, murphree)
binary_system = BS.BinarySystem(light_chemical, heavy_chemical)


# noinspection PyUnresolvedReferences
class Window(QMainWindow):
    _SIDEBAR_BUTTON_HEIGHT = 26
    _SIDEBAR_BUTTON_WIDTH = 120
    _SIDEBAR_HORIZONTAL_PADDING = 6
    _SIDEBAR_HEIGHT_PADDING = 2
    _selected_chemicals = [light_chemical, heavy_chemical]
    _display_required_steps = None
    _display_feed_step = None

    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(50, 50, 640, 400)
        self.setWindowTitle("Separations Preparation")
        self.setWindowIcon(QIcon('Elroy.png'))
        self.sidebar_x = self._SIDEBAR_BUTTON_WIDTH

        self.plot_canvas = PlotCanvas(self)
        self.plot_canvas.move(self.sidebar_x, 0)

        self.make_sidebar()

        self.show()

    def make_sidebar(self):
        """Hub function for generating all elements of the side bar

        Creates the following:
        1. Exit button
        2. Graph selection buttons
        3. Chemical selection buttons
        4. Tower property forms
        5. Number of stages displayed
        """
        self.make_escape_button(0)

        self.make_graph_change_buttons("Txy", 1)
        self.make_graph_change_buttons("VLE", 2)
        self.make_graph_change_buttons("Distillation", 3)

        self.make_text_box("Chemical Selection", 4)
        self.make_chemical_combo_boxes(5)

        self.make_tower_specification_box(7)

        feed_steps = str(binary_system.get_feed_step())
        self._display_feed_step = self.make_text_box("Feed stage: " + feed_steps, 12)
        required_steps = str(binary_system.get_required_steps())
        self._display_required_steps = self.make_text_box("Required stages: " + required_steps, 13)

        self.update_stage_display()

    def make_escape_button(self, offset):
        """Creates a button that allows the user to terminate the program

        Args:
            offset:         Number of buttons above it; determines how far down it displays
        """
        btn = QPushButton("Quit", self)
        btn.clicked.connect(QCoreApplication.instance().quit)
        self.set_generic_sidebar_geometry(btn, offset)

    def make_graph_change_buttons(self, desired_type, offset):
        """Creates a button to transition between graph types

        Args:
            desired_type:   ID of desired graph (Txy / VLE / Distillation)
            offset:         Number of buttons above it; determines how far down it displays
        """
        btn = QPushButton(desired_type, self)
        btn.clicked.connect(lambda: self.plot_canvas.create_plot(desired_type))
        self.set_generic_sidebar_geometry(btn, offset)

    def make_text_box(self, txt, offset, save_reference=False):
        txt = QLabel(txt, self)

        font = QFont("Times", 9)
        txt.setFont(font)

        txt.setAlignment(Qt.AlignLeft)
        txt.setAlignment(Qt.AlignBottom)

        self.set_generic_sidebar_geometry(txt, offset)
        return txt

    def make_chemical_combo_boxes(self, offset):
        """Creates a ComboBox to select one of the two chemicals used in the binary distillation system

        Args:
            offset:     Number of buttons above it; determines how far down it displays
        """
        for position, chemical in enumerate(self._selected_chemicals):
            chemical_combo_box = QComboBox(self)
            self.set_generic_sidebar_geometry(chemical_combo_box, offset + position)

            self.populate_combo_box(chemical_combo_box)
            self.change_selection(chemical_combo_box, chemical)

            if position == 0:
                chemical_combo_box.activated[str].connect(self.update_top_chemical_selected)
            else:
                chemical_combo_box.activated[str].connect(self.update_bottom_chemical_selected)

    @staticmethod
    def populate_combo_box(combo_box):
        """Populates the given combo box with the chemical options available by the file

        Args:
            combo_box:  PyQT5 Combobox object being populated
        """
        chemicals = binary_system.get_all_potential_chemicals()
        for chemical in chemicals:
            combo_box.addItem(chemical)

    @staticmethod
    def change_selection(selection_box, chemical_name):
        """Sets a given selection box's text to the provided chemical name

        Args:
            selection_box:  Selection box being set
            chemical_name:  Name to set the text to
        """
        index = selection_box.findText(chemical_name)
        selection_box.setCurrentIndex(index)

    def update_top_chemical_selected(self, new_chemical):
        """Checks if a new chemical is in use; if so, reverts to the previous selection, else, update the system

        Args:
            new_chemical:   New chemical name selected
        """
        if new_chemical in self._selected_chemicals:
            self.reset_combo_boxes_selection()
        else:
            self._selected_chemicals[0] = new_chemical
            self.process_valid_chemical_update()

    def update_bottom_chemical_selected(self, new_chemical):
        """Mirrors 'update_top_chemical_selected', but for the second box

        Couldn't create a "generalized" form where the index could be passed through, due to how PyQT5 handles
        event listeners

        Args:
            new_chemical: New chemical name selected
        """
        if new_chemical in self._selected_chemicals:
            self.reset_combo_boxes_selection()
        else:
            self._selected_chemicals[1] = new_chemical
            self.process_valid_chemical_update()

    def process_valid_chemical_update(self):
        """When a chemical selected is valid, the binary system object is updated and the plot redrawn"""
        binary_system.set_new_chemicals(self._selected_chemicals)
        self.update_stage_display()
        self.plot_canvas.recreate_plot()

    def reset_combo_boxes_selection(self):
        """Reverts the combo boxes to the previous selection"""
        for chemical, combo_box in zip(self._selected_chemicals, self._chemical_combo_boxes):
            self.change_selection(combo_box, chemical)

    def make_tower_specification_box(self, offset):
        """Creates user inputs for modifying the TowerSpecifications object

        Args:
            offset:     Number of buttons above it; determines how far down it displays
        """
        # "Property Name": [Lowerbound - Upperbound - Max decimal places - Initial value]
        config_options = {
            "R":  [0.001, 50.00, 3, R],
            "xB": [0.000, 0.998, 3, xB],
            "xF": [0.001, 0.999, 3, xF],
            "xD": [0.002, 1.000, 3, xD],
            "murphree": [0.05, 1.0, 3, murphree]
        }

        for count, spec_name in enumerate(config_options):
            box = QLineEdit(self)
            box.setValidator(self.make_numeric_validator(config_options[spec_name]))
            box.setText(str(config_options[spec_name][3]))
            box.setAlignment(Qt.AlignRight)

            if spec_name != "murphree":
                self.set_text_input_sidebar_geometry(spec_name, box, offset + count)
            else:
                # Create an eta symbol to represent murphree
                self.set_text_input_sidebar_geometry("\u03B7", box, offset + count)

            box.textChanged.connect(self.update_tower_specifications(spec_name))
            box.editingFinished.connect(self.update_stage_display)
            box.editingFinished.connect(self.plot_canvas.recreate_plot)

    @staticmethod
    def make_numeric_validator(properties):
        """Creates a QDoubleValidator object with proper settings

        Args:
            properties: Lower bound, upper bound, and permitted decimal places desired in the validator

        Returns:
            validator:  QDoubleValidator with desired properties
        """
        lower_bound = properties[0]
        upper_bound = properties[1]
        decimal_places = properties[2]
        validator = QDoubleValidator(lower_bound, upper_bound, decimal_places)
        validator.setNotation(QDoubleValidator.StandardNotation)
        return validator

    @staticmethod
    def update_tower_specifications(tower_property):
        """Provides the correct function to update, based on the property

        Args:
            tower_property: Property to be updated

        Returns:
            function:   Corresponds to the function that updates tower_property in the TowerSpecifications class
        """
        if tower_property == "R":
            return towSpec.set_reflux_ratio
        if tower_property == "xB":
            return towSpec.set_bottoms_fraction
        if tower_property == "xF":
            return towSpec.set_feed_fraction
        if tower_property == "xD":
            return towSpec.set_distillate_fraction
        if tower_property == "murphree":
            return towSpec.set_murphree_efficiency

    def update_stage_display(self):
        """Refreshes the stage display with the current number of feed and required stages"""
        # Refreshes the number of steps required
        binary_system.find_stage_counts(towSpec)

        # Updates feed step display
        feed_steps = str(binary_system.get_feed_step())
        self._display_feed_step.setText("Feed stage: " + feed_steps)

        # Updates required step display
        required_steps = str(binary_system.get_required_steps())
        self._display_required_steps.setText("Required stages: " + required_steps)

    def set_generic_sidebar_geometry(self, gui_object, offset):
        button_width = self._SIDEBAR_BUTTON_WIDTH - 2 * self._SIDEBAR_HORIZONTAL_PADDING
        gui_object.resize(button_width, self._SIDEBAR_BUTTON_HEIGHT)
        gui_object.move(self._SIDEBAR_HORIZONTAL_PADDING,
                        offset * (self._SIDEBAR_BUTTON_HEIGHT + self._SIDEBAR_HEIGHT_PADDING))

    def set_text_input_sidebar_geometry(self, text, gui_object, offset):
        ratio = 1/5

        txt_width = self._SIDEBAR_BUTTON_WIDTH * ratio - self._SIDEBAR_HORIZONTAL_PADDING
        self.make_sidebar_text_input_label(text, txt_width, offset)

        btn_width = self._SIDEBAR_BUTTON_WIDTH * (1 - ratio) - self._SIDEBAR_HORIZONTAL_PADDING
        gui_object.resize(btn_width, self._SIDEBAR_BUTTON_HEIGHT)
        gui_object.move(self._SIDEBAR_HORIZONTAL_PADDING + txt_width,
                        offset * (self._SIDEBAR_BUTTON_HEIGHT + self._SIDEBAR_HEIGHT_PADDING))

    def make_sidebar_text_input_label(self, text, width, offset):
        txt = QLabel(text, self)
        txt.setAlignment(Qt.AlignVCenter)
        txt.resize(width, self._SIDEBAR_BUTTON_HEIGHT)
        txt.move(self._SIDEBAR_HORIZONTAL_PADDING,
                 offset * (self._SIDEBAR_BUTTON_HEIGHT + self._SIDEBAR_HEIGHT_PADDING))

    def resizeEvent(self, event):
        """Overrides the default resize event, to adjust the size of the UI accordingly

        Args:
            event:  Required parameter by class being overrode
        """
        self.plot_canvas.resize(self.geometry().width() - self.sidebar_x, self.geometry().height())


class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, graph_type="Txy", dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.graph_type = None
        self.create_plot(graph_type)

    def recreate_plot(self):
        self.create_plot(self.graph_type)

    def create_plot(self, new_type):

        self.figure.clf()
        self.figure.suptitle(new_type, fontweight="bold")
        ax = self.figure.add_subplot(111)

        if new_type == "Txy":
            binary_system.plot_Txy_diagram(ax)
        elif new_type == "VLE":
            binary_system.plot_vapor_liquid_equilibrium_diagram(ax)
        elif new_type == "Distillation":
            binary_system.plot_reflux_distillation_diagram(towSpec, ax)
        self.graph_type = new_type

        self.draw()


def activate_UI():
    app = QApplication([])
    GUI = Window()
    sys.exit(app.exec_())


activate_UI()
