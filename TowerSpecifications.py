
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
        self.xB = self.confirm_valid_bounding(xB)
        self.xF = self.confirm_valid_bounding(xF, xB)
        self.xD = self.confirm_valid_bounding(xD, xF)
        self.murphree = self.confirm_valid_bounding(murphree)

    @staticmethod
    def confirm_valid_bounding(value, lowerLimit=0):
        """Verifies the value is properly bounded, and returns a ValueError if not

        Args:
            value:      Value being checked
            lowerLimit: The lower limit permitted for value

        Returns:
            value:      If valid, the original value is returned

        Raises:
            ValueError: If improperly bounded
        """

        if value < lowerLimit:
            raise ValueError
        if 0 < value <= 1:
            return value
        else:
            raise ValueError

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

    def set_reflux_ratio(self, R):
        try:
            R = float(R)
            self.R = float(R)
        except ValueError:
            print("Value Error: Cannot accept provided value")

    def set_murphree_efficiency(self, murphree):
        murphree = self.check_valid_input(murphree)
        if murphree == -1:
            return
        # Confirm valid range
        if 0 < murphree <= 1:
            self.murphree = murphree

    def set_distillate_fraction(self, xD):
        xD = self.check_valid_input(xD)
        if xD == -1:
            return
        # Confirm valid bounding
        if self.xF < xD:
            self.xD = xD

    def set_feed_fraction(self, xF):
        xF = self.check_valid_input(xF)
        if xF == -1:
            return
        # Confirm valid bounding
        if self.xB < xF:
            self.xF = xF

    def set_bottoms_fraction(self, xB):
        xB = self.check_valid_input(xB)
        if xB == -1:
            return
        # Confirm valid bounding
        if xB < self.xF:
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
