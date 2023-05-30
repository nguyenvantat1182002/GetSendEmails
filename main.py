from MainWindow import MainWindow
from PyQt5.QtWidgets import QApplication


app = QApplication([])

win = MainWindow()
win.show()

app.exec()