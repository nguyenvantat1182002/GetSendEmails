from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt5.QtCore import QObject, pyqtSignal


class EmailAccountTable(QObject):
    setItem = pyqtSignal(int, int, object)
    removeRow = pyqtSignal(int)
    insertRow = pyqtSignal(int)

    def __init__(self, table: QTableWidget) -> None:
        super().__init__()

        self.table = table

        self.setItem.connect(self.table.setItem)
        self.removeRow.connect(self.table.removeRow)
        self.insertRow.connect(self.table.insertRow)

    def clear(self) -> None:
        while self.table.rowCount() > 0:
            self.removeRow.emit(0)

    def add_row(self, column: int, item: QTableWidgetItem) -> int:
        row = self.table.rowCount()

        self.insertRow.emit(row)
        self.setItem.emit(row, column, item)

        return row
    
    def update_email_pwd(self, row: int, value: str) -> None:
        self.setItem.emit(row, 1, QTableWidgetItem(value))

    def update_status(self, row: int, value: str) -> None:
        self.setItem.emit(row, 2, QTableWidgetItem(value))