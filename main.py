from MainWindow import MainWindow
from PyQt5.QtWidgets import QApplication

import os


folder_path = 'Output'
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

app = QApplication([])

win = MainWindow()
win.show()

app.exec()