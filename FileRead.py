
class FileRead:
    """Used to read a delimited value file (i.e. CSV) of numbers and permits excess spacing for readability

    Public-Intended Methods:
        get_data():  Returns the attribute "data"

    Attributes:
        file_name:  string; file address
        delimiter:  character; character separating values in the provided file
        header:     Boolean; indicates whether a header is present or not in the file
        data:       dictionary; the first row value is the KEY, the VALUE is the list of remaining row values
    """

    def __init__(self, file_name, delimiter, header=False):
        self.file_name = file_name
        self.delimiter = delimiter
        self.header = header
        self.data = {}
        self.read_CSV()

    def get_data(self):
        """Public facing method for retrieving read data from the file

        Returns:
            data:   Parsed data file as a dictionary
        """
        return self.data

    def get_keys(self):
        """Public facing method for only retrieving keys

        Returns:
            keys:   Parsed data keys
        """
        return self.data.keys()

    def read_CSV(self):
        """Handles overall process of reading CSV file

        Opens the file, skips the header if necessary, and then processes the file line-by-line until complete
        """
        file = open(self.file_name, "r")
        self.data = {}
        self.header_adjustment(file)
        self.process_line_by_line(file)

    def header_adjustment(self, file):
        """Checks if a header is present, and skips a line if so

        Args:
            file: The file currently being read
        """
        if self.header:
            file.readline()

    def process_line_by_line(self, file):
        """Parses a file line into a key-value pair and stores this pairing in "data"

        Args:
            file: The file currently being read
        """
        for line in file:
            element = self.cut_by_delimiter(line)
            identifier = element[0]
            self.data[identifier] = element[1:]

    def cut_by_delimiter(self, line):
        """Separates the line by the set delimiter

        Args:
            line:       Line currently being adjusted

        Returns:
            elements:   List of separated elements
        """
        start = 0
        elements = []

        while start != len(line)-1:
            if start != 0:
                start = self.trim_excess_spaces(line, start + 1)
            stop = self.find_next_nearest_delimiter(line, start)

            if start == 0:
                elements.append(line[start:stop])
            else:
                elements.append(float(line[start:stop]))

            start = stop

        return elements

    @staticmethod
    def trim_excess_spaces(line, index):
        """Trims away excess spaces from the left-hand-side

        Args:
            line:   Current line being parsed
            index:  Initial starting index

        Returns:
            index:  New initial starting index, skipping over spaces

        """
        while line[index] == " ":
            index += 1
        return index

    def find_next_nearest_delimiter(self, line, index):
        """Identifies the index of the next delimiter

        Args:
            line:   Current line being parsed
            index:  Initial starting index

        Returns:
            index:  Index of the next delimiter

        """
        while line[index] != self.delimiter and index < len(line)-1:
            index += 1
        return index
