from PyQt5.QtCore import QAbstractTableModel, Qt

class ScheduleModel(QAbstractTableModel):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
     
    def rowCount(self, parent=None):
        return 1# len(self.data)

    def columnCount(self, parent=None):
        return 4  # Schedule, Time, Path, Actions

    def data(self, index, role):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return self.data[row]['type']
            elif col == 1:
                return self.data[row]['time']
            elif col == 2:
                return self.data[row]['path']
            elif col == 3:
                return ""  # Empty string for the button column

        return None

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section == 0:
                    return "Schedule"
                elif section == 1:
                    return "Time"
                elif section == 2:
                    return "Path"
                elif section == 3:
                    return "Actions"

        return None
