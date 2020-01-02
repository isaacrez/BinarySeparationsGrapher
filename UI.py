from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QDoubleValidator, QFont
from PyQt5.QtCore import QCoreApplication, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import BinarySystem
import TowerSpecifications


class Window(QMainWindow):
    """Generates sidebar elements and renders the overall Window display

    Public-Intended Methods:
        None

    Attributes:
        _WINDOW_MINIMUM_WIDTH:          Minimum width permitted for the window
        _WINDOW_MINIMUM_HEIGHT:         Minimum height permitted for the window
        _SIDEBAR_BUTTON_HEIGHT:         Sidebar button's height
        _SIDEBAR_BUTTON_WIDTH:          Sidebar (and sidebar button's) width
        _SIDEBAR_HORIZONTAL_PADDING:    Space between edge and sidebar buttons; SUBTRACTED from button width
        _SIDEBAR_HEIGHT_PADDING:        Space between each button vertically; INDEPENDENT of button height
        _selected_chemicals:            Stores the chemicals currently selected by the two ComboBoxes
        _display_required_steps:        QLabel displaying the required steps to complete the distillation process
        _display_feed_step:             QLabel displaying the optimal feed step for the distillation process
    """

    _WINDOW_MINIMUM_WIDTH = 640
    _WINDOW_MINIMUM_HEIGHT = 400
    _SIDEBAR_BUTTON_HEIGHT = 26
    _SIDEBAR_BUTTON_WIDTH = 120
    _SIDEBAR_HORIZONTAL_PADDING = 6
    _SIDEBAR_HEIGHT_PADDING = 2

    _selected_chemicals = []
    _chemical_combo_boxes = []
    _display_required_steps = None
    _display_feed_step = None

    def __init__(self, binary_system: BinarySystem, tower_specs: TowerSpecifications):
        super(Window, self).__init__()
        self.setGeometry(50, 50, self._WINDOW_MINIMUM_WIDTH, self._WINDOW_MINIMUM_HEIGHT)
        self.setMinimumSize(self._WINDOW_MINIMUM_WIDTH, self._WINDOW_MINIMUM_HEIGHT)
        self.setWindowTitle("Separations Preparation")
        self.setWindowIcon(QIcon('Elroy.png'))
        self.sidebar_x = self._SIDEBAR_BUTTON_WIDTH
        
        self.binary_system = binary_system
        self.tower_specs = tower_specs
        self._selected_chemicals = binary_system.get_current_chemicals()

        self.plot_canvas = PlotCanvas(binary_system, tower_specs, self)
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

        feed_steps = str(self.binary_system.get_feed_step())
        self._display_feed_step = self.make_text_box("Feed stage: " + feed_steps, 12)
        required_steps = str(self.binary_system.get_required_steps())
        self._display_required_steps = self.make_text_box("No. stages: " + required_steps, 13)

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

    def make_text_box(self, txt, offset):
        """Produces a text box for the sidebar

        Args:
            txt:        Text to be displayed in "text_box"
            offset:     Space down the sidebar "text_box" should be displayed

        Returns:
           text_box:    QLabel object containing "txt" and positioned based on "offset"
        """
        text_box = QLabel(txt, self)

        font = QFont("Times", 10)
        text_box.setFont(font)

        text_box.setAlignment(Qt.AlignLeft)
        text_box.setAlignment(Qt.AlignBottom)

        self.set_generic_sidebar_geometry(text_box, offset)
        return text_box

    def make_chemical_combo_boxes(self, offset):
        """Creates a ComboBox to select one of the two chemicals used in the binary distillation system

        Args:
            offset:     Number of buttons above it; determines how far down it displays
        """
        for position, chemical in enumerate(self._selected_chemicals):
            chemical_combo_box = QComboBox(self)
            self._chemical_combo_boxes.append(chemical_combo_box)
            self.set_generic_sidebar_geometry(chemical_combo_box, offset + position)

            self.populate_combo_box(chemical_combo_box)
            self.change_selection(chemical_combo_box, chemical)

            if position == 0:
                chemical_combo_box.activated[str].connect(self.update_top_chemical_selected)
            else:
                chemical_combo_box.activated[str].connect(self.update_bottom_chemical_selected)

    def populate_combo_box(self, combo_box):
        """Populates the given combo box with the chemical options available by the file

        Args:
            combo_box:  PyQT5 Combobox object being populated
        """
        chemicals = self.binary_system.get_all_potential_chemicals()
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
        self.binary_system.set_new_chemicals(self._selected_chemicals)
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
        # "Property Name": [Lower bound - Upper bound - Max decimal places - Initial value]
        config_options = {
            "R":  [0.001, 50.00, 3, self.tower_specs.get_reflux_ratio()],
            "xB": [0.000, 0.998, 3, self.tower_specs.get_xB()],
            "xF": [0.001, 0.999, 3, self.tower_specs.get_xF()],
            "xD": [0.002, 1.000, 3, self.tower_specs.get_xD()],
            "murphree": [0.05, 1.0, 3, self.tower_specs.get_murphree()]
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

    def update_tower_specifications(self, tower_property):
        """Provides the correct function to update, based on the property

        Args:
            tower_property: Property to be updated

        Returns:
            function:   Corresponds to the function that updates tower_property in the TowerSpecifications class
        """
        if tower_property == "R":
            return self.tower_specs.set_reflux_ratio
        if tower_property == "xB":
            return self.tower_specs.set_bottoms_fraction
        if tower_property == "xF":
            return self.tower_specs.set_feed_fraction
        if tower_property == "xD":
            return self.tower_specs.set_distillate_fraction
        if tower_property == "murphree":
            return self.tower_specs.set_murphree_efficiency

    def update_stage_display(self):
        """Refreshes the stage display with the current number of feed and required stages"""
        # Refreshes the number of steps required
        self.binary_system.find_stage_counts(self.tower_specs)

        # Updates feed step display
        feed_steps = str(self.binary_system.get_feed_step())
        self._display_feed_step.setText("Feed stage:\t" + feed_steps)

        # Updates required step display
        required_steps = str(self.binary_system.get_required_steps())
        self._display_required_steps.setText("No. stages:\t" + required_steps)

    def set_generic_sidebar_geometry(self, gui_object, offset):
        """Configures the provided GUI element based on sidebar formatting

        Args:
            gui_object:     GUI object to be sized
            offset:         How far vertically the object should be moved
        """
        button_width = self._SIDEBAR_BUTTON_WIDTH - 2 * self._SIDEBAR_HORIZONTAL_PADDING
        gui_object.resize(button_width, self._SIDEBAR_BUTTON_HEIGHT)
        gui_object.move(self._SIDEBAR_HORIZONTAL_PADDING,
                        offset * (self._SIDEBAR_BUTTON_HEIGHT + self._SIDEBAR_HEIGHT_PADDING))

    def set_text_input_sidebar_geometry(self, text, gui_object, offset):
        """Sizes and positions the GUI object into the sidebar, with a label to its left

        Args:
            text:       Text for the label ADJACENT to the object being rendered
            gui_object: GUI object to be configured; should be a RadioButton or QLineEdit
            offset:     How far vertically the object should be moved
        """
        ratio = 1/5     # Ratio of text-to-form

        txt_width = int(self._SIDEBAR_BUTTON_WIDTH * ratio - self._SIDEBAR_HORIZONTAL_PADDING)
        self.make_sidebar_text_input_label(text, txt_width, offset)

        btn_width = int(self._SIDEBAR_BUTTON_WIDTH * (1 - ratio) - self._SIDEBAR_HORIZONTAL_PADDING)
        gui_object.resize(btn_width, self._SIDEBAR_BUTTON_HEIGHT)
        gui_object.move(self._SIDEBAR_HORIZONTAL_PADDING + txt_width,
                        offset * (self._SIDEBAR_BUTTON_HEIGHT + self._SIDEBAR_HEIGHT_PADDING))

    def make_sidebar_text_input_label(self, text, width, offset):
        """Generates a sidebar text label with the provided text, width, and offset

        Args:
            text:       The text content for the label
            width:      How wide the element is
            offset:     How far down the sidebar the element should be displayed
        """
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
    """Used to render plots generated by the BinarySystem class

    Public-Intended Methods:
        recreate_plot():        Recreates the existing plot
        create_plot(new_type):  Creates a new plot of type "new_type"

    Attributes:
        graph_type:             The current graph type being rendered
    """
    #TODO   Eliminate crashes caused by redrawing
    #       They occur due to the object being deleted (Unsure which object or how/why it is deleted)

    def __init__(self, binary_system: BinarySystem, tower_specs: TowerSpecifications,
                 parent=None, width=5, height=4, graph_type="Txy", dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.binary_system = binary_system
        self.tower_specs = tower_specs

        self.graph_type = None
        self.create_plot(graph_type)

    def recreate_plot(self):
        """Recreates the existing plot; used for updating it when parameters change"""
        self.create_plot(self.graph_type)

    def create_plot(self, new_type):
        """Used to create a new plot of form "new_type" using the BinarySystem class that is then rendered

        Args:
            new_type:   New graph desired from BinarySystem. Can be "Txy", "VLE", or "Distillation"
        """

        self.figure.clf()
        self.figure.suptitle(new_type, fontweight="bold")
        ax = self.figure.add_subplot(111)

        if new_type == "Txy":
            self.binary_system.plot_Txy_diagram(ax)
        elif new_type == "VLE":
            self.binary_system.plot_vapor_liquid_equilibrium_diagram(ax)
        elif new_type == "Distillation":
            self.binary_system.plot_reflux_distillation_diagram(self.tower_specs, ax)
        self.graph_type = new_type

        self.draw()



