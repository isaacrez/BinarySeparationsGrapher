
class TowerSpecs:
    """Used to compactly store and convert tower-specifications

    Public-Intended Methods:
        get_operating_line_parameters():    Used to get operating line parameters
        get_tower_specifications():         Used to compactly retrieve tower information

    Attributes:
        R:          float; Reflux ratio (distillate exiting / condensing back into the tower) (problem space name)
        xB:         float; the light fraction in the bottoms (problem space name)
        xF:         float; the light fraction in the feed (problem space name)
        xD:         float; the light fraction in the distillate (problem space name)
        murphree:   float; Murphree efficiency of each stage

    """
    def __init__(self, R, xB, xF, xD, murphree=1):
        self.R = R
        self.xB = self.set_initial_values(0, xB)
        self.xF = self.set_initial_values(self.xB + 0.001, xF, self.xB + 0.001)
        self.xD = self.set_initial_values(self.xF + 0.001, xD, self.xF + 0.001)
        self.murphree = self.set_initial_values(1, murphree)

    def set_initial_values(self, default, value, lower_limit=0):
        """Ensures the initial values are properly bounded from lower_limit < value <= 1; if not, sets them to default

        Args:
            default:            Value will default to this if given improper bounds
            value:              Value to test for validity
            lower_limit:        The lower acceptable limit for this value

        Returns:
            value / default:    The value to be used by the system
        """
        if self.confirm_valid_bounding(value, lower_limit):
            return value
        else:
            return default

    @staticmethod
    def confirm_valid_bounding(value, lower_limit=0):
        """Verifies the value is properly bounded, and returns a ValueError if not

        Args:
            value:      Value being checked
            lower_limit: The lower limit permitted for value

        Returns:
            value:      If valid, the original value is returned

        Raises:
            ValueError: If improperly bounded
        """

        if value < lower_limit:
            return False
        if value <= 1:
            return True
        else:
            return False

    def get_operating_line_parameters(self):
        """Creates the operating line for both the stripping and rectifying sections

        Uses the equation for the rectifying line, m = R / (R + 1) and b = xD / (R + 1).  The stripping section is a
        straight line from (xB, xB) to the point (xF, m * xF + b), or the point where the rectifying line intersects the
        feed line.

        Returns:
            m:  List of slopes, the first being the rectifying, the second the stripping
            b:  List of y-intercepts, the first being the rectifying, the second the stripping
        """
        # Rectifying line
        m = [self.R / (self.R + 1)]
        b = [self.xD / (self.R + 1)]
        # Stripping line
        transition_y = m[0] * self.xF + b[0]
        m.append((transition_y - self.xB) / (self.xF - self.xB))
        b.append(self.xB * (1 - m[1]))
        return [m, b]

    def get_tower_specifications(self):
        """Used to cleanly extract information in a single line

        Returns:
            xB:         The light fraction in the bottoms
            xF:         The light fraction in the feed
            xD:         The light fraction in the distillate
            murphree:   Murphree efficiency of each stage
        """
        return self.xB, self.xF, self.xD, self.murphree

    def get_reflux_ratio(self):
        return self.R

    def get_xB(self):
        return self.xB

    def get_xF(self):
        return self.xF

    def get_xD(self):
        return self.xD

    def get_murphree(self):
        return self.murphree

    def set_reflux_ratio(self, R):
        try:
            R = float(R)
            self.R = float(R)
        except ValueError:
            print("Value Error: Cannot accept provided value")

    def set_murphree_efficiency(self, murphree):
        murphree = self.check_valid_input(murphree)
        if self.confirm_valid_bounding(murphree):
            self.murphree = murphree

    def set_distillate_fraction(self, xD):
        xD = self.check_valid_input(xD)
        if self.confirm_valid_bounding(xD, self.xF):
            self.xD = xD

    def set_feed_fraction(self, xF):
        xF = self.check_valid_input(xF)
        if self.confirm_valid_bounding(xF, self.xB):
            self.xF = xF

    def set_bottoms_fraction(self, xB):
        xB = self.check_valid_input(xB)
        if self.confirm_valid_bounding(xB):
            self.xB = xB

    @staticmethod
    def check_valid_input(str_value):
        """Confirms the given string input can safely be converted to a float; returns -1 if not.

        Args:
            str_value:  The string provided to confirm validity

        Returns:
            flt_value:  The provided value converted to a string
        """
        try:
            flt_value = float(str_value)
            return flt_value
        except ValueError:
            print("ValueError: Cannot convert a string of length ", len(str_value), " to float.")
            return -1
