import numpy as np

import math
import general_methods as gm
import FileRead as FR


class BinarySystem:
    """Used to generate relevant plots for distilling a binary chemical system

    Public-Intended Methods:
        plot_Txy_diagram():                             Creates a Txy diagram based on the chemicals provided
        plot_vapor_liquid_equilibrium_diagram():        Creates a VLE diagram based on the chemicals provided
        plot_reflux_distillation_diagram(towerSpecs):   Creates a binary-distillation diagram based on chemicals
                                                        provided and tower specifications indicated in "towerSpecs"

    Attributes:
        _PURE_LIGHT_CHEMICAL:   const int; represents the system as purely the light
        _PURE_HEAVY_CHEMICAL:   const int; represents the system as purely the heavy
        light_chemical:         string; name of the light chemical used
        heavy_chemical:         string; name of the heavy chemical used
        antoine_coefficients:   dictionary floats; key: chemical name; value: Antoine coefficients for determining
                                saturated pressure
        temperature_bounds:             list int; indicates temperature boundaries for pure light and pure heavy
        x:                      list floats; liquid mole fractions corresponding to range(temperature_bounds[0], temperature_bounds[1])
        y:                      list floats; vapor mole fractions corresponding to range(temperature_bounds[0], temperature_bounds[1])
    """
    _PURE_LIGHT_CHEMICAL = 1
    _PURE_HEAVY_CHEMICAL = 0
    _MAX_PERMITTED_STEPS = 51
    steps_required = 0
    feed_step = 0

    def __init__(self, light_chemical, heavy_chemical):
        self.light_chemical = light_chemical
        self.heavy_chemical = heavy_chemical
        self.data_source = FR.FileRead("antoineData.csv", ",", True)
        self.antoine_coefficients = self.get_Antoine()
        self.temperature_bounds = self.get_temperature_boundaries()
        self.verify_correct_chemical_labels()
        self.x, self.y = self.get_vapor_liquid_equilibrium_data()

    def set_light_chemical(self, new_chemical):
        """Changes the light chemical in the system and then updates

        Args:
            new_chemical:   The replacement for light_chemical
        """
        self.light_chemical = new_chemical
        self.update_binary_system()

    def set_heavy_chemical(self, new_chemical):
        """Changes the heavy chemical in the system and then updates

        Args:
            new_chemical:   The replacement for heavy_chemical
        """
        self.heavy_chemical = new_chemical
        self.update_binary_system()

    def set_new_chemicals(self, new_chemicals):
        """Changes both chemicals in the system and then updates

        Args:
            new_chemicals:  A list of two chemicals to define the system by
        """
        self.light_chemical = new_chemicals[0]
        self.heavy_chemical = new_chemicals[1]
        self.update_binary_system()

    def get_current_chemicals(self):
        """Returns a list of the current chemicals"""
        return [self.light_chemical, self.heavy_chemical]

    def get_all_potential_chemicals(self):
        """Recovers all the chemicals read from the data file"""
        return self.data_source.get_keys()

    def get_required_steps(self):
        return self.steps_required

    def get_feed_step(self):
        return self.feed_step

    def update_binary_system(self):
        """Reconfigures chemical-specific properties such as VLE and temperature boundaries if a chemical is changed
        """
        self.antoine_coefficients = self.get_Antoine()
        self.temperature_bounds = [200, 1000]
        self.temperature_bounds = self.get_temperature_boundaries()
        self.verify_correct_chemical_labels()
        self.extend_temperature_boundaries()
        self.x, self.y = self.get_vapor_liquid_equilibrium_data()

    def get_temperature_boundaries(self):
        """Determines maximum and minimum useful temperatures

        Solves for the boiling point of each of the compounds in use to determine the upper / lower system temperature
        boundaries

        Returns:
            lower_bound:    Upper temperature boundary, corresponding to pure heavy
            upper_bound:    Lower temperature boundary, corresponding to pure light
        """
        lower_bound = math.floor(self.get_boiling_point(self.light_chemical))
        upper_bound = math.ceil(self.get_boiling_point(self.heavy_chemical))

        return [lower_bound, upper_bound]

    def get_boiling_point(self, chemical):
        """Determines the boiling point of chemical using Antoine's equation:
                ln(Psat) = A - B / (T + C), where Psat = 760 mmHg (1 atm)

        Args:
            chemical: Chemical whose boiling point is desired
        """
        A, B, C = self.antoine_coefficients[chemical]
        T = B / (A - math.log(760)) - C
        return T

    def verify_correct_chemical_labels(self):
        """Ensures the correct labeling of the light and heavy chemicals; flips associated data if this is false

        The lighter chemical by definition has a smaller boiling point, therefore the lower_bound MUST be lower than
        upper_bound, otherwise the assignment was incorrect
        """
        if self.temperature_bounds[1] < self.temperature_bounds[0]:
            temporary = self.light_chemical
            self.light_chemical = self.heavy_chemical
            self.heavy_chemical = temporary

            temporary = self.temperature_bounds[0]
            # The bounds need to be extended in the proper direction; including correcting the original safety extension
            self.temperature_bounds[0] = self.temperature_bounds[1] - 2
            self.temperature_bounds[1] = temporary + 2

    def extend_temperature_boundaries(self):
        """Slightly extends the temperature boundaries to ensure all relevant values are covered
        """
        self.temperature_bounds[0] -= 2
        self.temperature_bounds[1] += 2

    def get_temperature_from_x(self, xDesired):
        """Determines temperature that fulfills the relationship x(T) = xDesired

        Specifies an initial temperature range to search in (defaults to 100 - 800; after uses the solved bounds.)
        Applies bisection method / binary search to reduce temperature range until the x values approximately
        equal xDesired

        Args:
            xDesired:   The target value, such that x(T) = xDesired

        Returns:
            T:          The T-value satisfying the relationship x(T) = xDesired
        """
        T = self.temperature_bounds
        gm.add_midpoint(T)
        tol, err, counter = gm.default_indefinite_iteration_parameters()

        while (tol < err) & (counter < 30):
            T, x = self.reduce_temperature_range(T, xDesired)
            err = abs(x[2] - x[0])
            counter += 1

        return T[1]

    def reduce_temperature_range(self, T, xDesired):
        """Reduces temperature range to approximate the value of T to achieve xDesired

        Applies bisection method / binary search to reduce the range

        Args:
            T:          Temperature range containing the T that solves for x(T) = xDesired
            xDesired:   The desired value temperature should solve for, x(T) = xDesired

        Returns:
            T:          A reduced temperature range, still containing the T that solves for x(T) = xDesired
            x:          The x resulting from the two edges
        """
        x = []
        for T_i in T:
            x.append(self.solve_binary_Raoult_Relation(T_i) - xDesired)
        T = gm.bisection_method(T, x)
        return T, x

    def get_Psat(self, chemical, T):
        """Determines the saturated pressure (Psat) for a chemical at a given temperature, using the Antoine equation

        Uses the Antoine equation, e^(A - B/(T + C)).  A, B, C are Antoine coefficients specified by the chemical
        species.

        Args:
            chemical:   Specifies the desired Antoine coefficients
            T:          Temperature used, in Kelvin

        Returns:
            Psat:       The saturated pressure for the given conditions
        """
        [A, B, C] = self.antoine_coefficients[chemical]
        return math.exp(A - B / (T + C))

    def get_Antoine(self):
        """Finds Antoine coefficients for species of interest and stores them

        Calls FileRead, which parses a CSV into

        Returns:
            antoine_coefficients:   Dictionary, where keys are chemicals and values are Antoine coefficients
                                    antoine_coefficients[chemical] = [A, B, C]
        """
        data = self.data_source.get_data()
        antoine_coefficients = {}

        for currChem in data:
            if currChem == self.light_chemical or currChem == self.heavy_chemical:
                antoine_coefficients[currChem] = data[currChem]
            if len(antoine_coefficients) == 2:
                break
        return antoine_coefficients

    def solve_binary_Raoult_Relation(self, T):
        """Finds the x value that satisfies the binary Raoult's relationship, 760 = lightPsat * x + heavyPsat * (1 - x)

        Uses the temperature to determine the light and heavy Psats.  An initial guess of x = 0.5 is used, and the
        value of x is determined iteratively using Newton's Method.

        Args:
            T:  Determines the light and heavy Psat, which parameterize the equation

        Returns:
            x:  The value of x that satisfies the equation 760 = lightPsat * x + heavyPsat * (1 - x)
        """
        lightPsat = self.get_Psat(self.light_chemical, T)
        heavyPsat = self.get_Psat(self.heavy_chemical, T)

        tol, err, counter = gm.default_indefinite_iteration_parameters()
        x = 0.5
        f_p = lightPsat - heavyPsat

        while (tol < err) & (counter < 100):
            f = lightPsat * x + heavyPsat * (1 - x) - 760
            x_new = x - f / f_p
            err = abs(x - x_new)
            x = x_new
            counter += 1
        return x

    def get_light_chemical_y(self, x, T):
        """Determine the vapor mole fraction (y) of the light component using Raoult's Law

        Uses the relationship y = x*Psat/P, or Raoult's Law for a binary system

        Args:
            x:          Liquid mole fraction of the chemical specified
            T:          Temperature used

        Returns:
            y:          Corresponding vapor liquid mole fraction, y
        """
        Psat = self.get_Psat(self.light_chemical, T)
        return x * Psat / 760

    def get_vapor_liquid_equilibrium_data(self):
        temperatures = range(self.temperature_bounds[0], self.temperature_bounds[1])
        x = []
        y = []

        for T in temperatures:
            x.append(self.solve_binary_Raoult_Relation(T))
            y.append(self.get_light_chemical_y(x[-1], T))

        return [np.flip(np.array(x)), np.flip(np.array(y))]

    def get_effective_vapor_liquid_equilibrium_data(self, towerSpecs):
        _, xF, _, murphree = towerSpecs.get_tower_specifications()
        m, b = towerSpecs.get_operating_line_parameters()
        effVLE = []

        for currX, currY in zip(self.x, self.y):
            if xF < currX:
                currEffVLE = m[0] * currX + b[0]
            else:
                currEffVLE = m[1] * currX + b[1]

            effY = murphree * (currY - currEffVLE) + currEffVLE
            effY = max(effY, currX)
            effVLE.append(effY)

        return np.array(effVLE)

    def plot_Txy_diagram(self, plot_element):
        """Creates a Txy diagram, where temperature is the x-axis and the liquid / vapor fractions are the y-axis

        Axis limits are determined using the initially solved temperature boundaries.  Vapor-Liquid-Equilibrium (VLE)
        data initially solved for is plotted against their corresponding temperatures.

        Args:
            plot_element:   Plot object being updated
        """
        T = range(self.temperature_bounds[0], self.temperature_bounds[1])
        plot_element.plot(T, self.x, '-b', label='Liquid')
        plot_element.plot(T, self.y, '-r', label='Vapor')

        plot_element.axis([self.temperature_bounds[0], self.temperature_bounds[1], 0, 1])
        self.standard_plot_format("Temperature (K)", "Mole fraction", plot_element)

    def plot_vapor_liquid_equilibrium_diagram(self, plot_element):
        """Solves for the liquid and vapor mole fractions at successive increments within the valid temperature range

        Plots the liquid mole fraction (x) v. vapor mole fraction (y)

        Args:
            plot_element:   Plot object being updated
        """
        plot_element.plot(self.x, self.y, '-k', label='Eq. Curve')
        self.plot_diagonal(plot_element)
        plot_element.axis([0, 1, 0, 1])
        self.standard_plot_format("x", "y", plot_element)

    def plot_reflux_distillation_diagram(self, towerSpecs, plot_element):
        """Plots the VLE diagram, OP lines, and McCabe Thiele steps representing a binary distillation

        Uses current VLE information, and generates additional information as necessary.  The OP line and effective VLE
        are determined using TowerSpecs.  The McCabe Thiele steps are determined using the OP, VLE, and effective VLE
        information.

        Args:
            towerSpecs:     TowerSpecs object containing information on the tower configuration
            plot_element:   Plot object being updated

        Returns:
            steps:      Number of discrete stages required to complete the distillation
        """
        m, b = towerSpecs.get_operating_line_parameters()
        xB, xF, xD, murphree = towerSpecs.get_tower_specifications()

        plot_element.plot([xB, xF, xD], [xB, m[0] * xF + b[0], xD], '-b', label="OP")
        plot_element.plot(self.x, self.y, '-k', label='Eq. Curve')
        self.plot_diagonal(plot_element)

        if murphree != 1:
            yEff = self.get_effective_vapor_liquid_equilibrium_data(towerSpecs)
            plot_element.plot(self.x, yEff, '--k', label="Effective Eq.")
            self.plot_McCabe_Thiele_steps(towerSpecs, plot_element, yEff)
        else:
            self.plot_McCabe_Thiele_steps(towerSpecs, plot_element)

        plot_element.axis([0, 1, 0, 1])
        self.standard_plot_format("x", "y", plot_element)

    def find_stage_counts(self, towerSpecs):
        _, _, _, murphree = towerSpecs.get_tower_specifications()
        if murphree != 1:
            yEff = self.get_effective_vapor_liquid_equilibrium_data(towerSpecs)
            self.plot_McCabe_Thiele_steps(towerSpecs, None, yEff)
        else:
            self.plot_McCabe_Thiele_steps(towerSpecs)

    def plot_McCabe_Thiele_steps(self, towerSpecs, plot_element=None, effY=None):
        """Plots the McCabe Thiele steps, which represent the number of discrete stages required

        Iteratively moves from the OP line, horizontally to the equilibrium line, then vertically back to the
        equilibrium line.  This process repeats from an initial state of (xD, xD) until the threshold (xB, xB) is passed
        If an effective VLE is provided, this replaces the equilibrium line except for the final step.

        Args:
            towerSpecs:     TowerSpecs object containing information on the tower configuration
            effY:           If the murphree efficiency != 1, then the effective VLE conditions are used
            plot_element:   Plot object being updated

        Returns:
            steps:      Number of discrete stages required to complete the distillation
        """
        xB, xF, xD, _ = towerSpecs.get_tower_specifications()

        self.feed_step = 1

        found_feed_step = False
        currX = xD
        currY = xD
        steps = 0

        while (xB < currX) and (steps < self._MAX_PERMITTED_STEPS):
            steps += 1
            xEq = np.interp(currY, self.y, self.x)

            # Checks if we're going to the effective equilibrium instead (every step except final)
            if (xB < xEq) and (effY is not None):
                xEq = np.interp(currY, effY, self.x)

            # Checks if we're still inside stepping bounds (and therefore going to the operating line)
            if xB < xEq:
                yOP, state = self.get_yOperating(towerSpecs, xEq)
                if not found_feed_step:
                    found_feed_step = self.update_feed_step(state, steps)

            # Outside the stepping bounds - therefore the diagonal suffices
            else:
                yOP = xEq

            # Plot the step if a diagram is available
            if plot_element is not None:
                plot_element.plot([currX, xEq, xEq], [currY, currY, yOP], '-g')

            currX = xEq
            currY = yOP

        if plot_element is not None:
            plot_element.plot([0], [0], '-g', label='McCabe Thiele')

        if steps == self._MAX_PERMITTED_STEPS:
            self.steps_required = "N/A"
        else:
            self.steps_required = steps

    def update_feed_step(self, state, steps):
        """Determines if updating the feed step is valid, and if applicable, does so

        Args:
            state:  Position of the point
            steps:  The current step

        Returns:
            found:  Whether the feed_step was set this call
        """
        found = False
        if state == "stripping":
            if steps == 0:
                self.feed_step = 1
            else:
                self.feed_step = steps
            found = True
        return found


    @staticmethod
    def plot_diagonal(plot_element):
        """Used to add a diagonal plot

        Args:
            plot_element:   Plot object being updated
        """
        plot_element.plot([0, 1], [0, 1], '--r')

    @staticmethod
    def get_yOperating(towerSpecs, x):
        """Retrieves the y-component of a point on the OP line, provided an x value

        Determines if the point is located in the rectifying, or stripping section.  If out-of-bounds, it defaults to
        the diagonal to provide a clean display when plotted.

        Args:
            towerSpecs:     TowerSpecs object, carries variables with it
            x:              The equilibrium mole fraction

        Returns:
            yOP:        The point (xEq, yOP) on the OP (operating) line
            state:      Either "rectifying" or "stripping" based on the current section
        """
        xB, xF, _, _ = towerSpecs.get_tower_specifications()
        m, b = towerSpecs.get_operating_line_parameters()
        # Stripping section
        if x < xF:
            return x * m[1] + b[1], "stripping"
        # Rectifying section
        elif xB < x:
            return x * m[0] + b[0], "rectifying"
        else:
            return x, "None"

    def standard_plot_format(self, xLabel, yLabel, plot_element):
        """Used to default common desired pyplot parameters and then display

        Args:
            xLabel:         Specifies text for the x-axis label
            yLabel:         Specifies text for the y-axis label
            plot_element:   Plot object being updated
        """
        plot_element.set_xlabel(xLabel)
        plot_element.set_ylabel(yLabel)
        plot_element.set_title(self.light_chemical + " (L) & " + self.heavy_chemical + " (H)")
        plot_element.grid()
        plot_element.legend()
