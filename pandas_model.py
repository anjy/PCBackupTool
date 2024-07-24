from PyQt5.QtCore import  QAbstractTableModel, Qt

# Pandas 데이터 모델
class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._data = data
       

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1] + 1

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            if index.column() < self._data.shape[1]:
                return str(self._data.iat[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section < self._data.shape[1]:
                    return str(self._data.columns[section])
                elif section == self._data.shape[1]:
                    return "Action"
            elif orientation == Qt.Vertical:
                return str(section)
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemFlags(QAbstractTableModel.flags(self, index))
