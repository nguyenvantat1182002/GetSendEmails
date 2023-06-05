from PyQt5.QtCore import QThread, QMutex, pyqtSignal
from queue import Queue
from MainWindow import IMainWindow
from PyQt5.QtWidgets import (
    QSpinBox,
    QPlainTextEdit,
    QLineEdit,
    QLabel
)
from modules import EmailAccountTable


class IGetSentEmailsThread(QThread):
    updateSentEmail = pyqtSignal(str)
    updateSendtEmailCount = pyqtSignal(str)
    updateSuccessfulLoginCount = pyqtSignal(str)
    updateFailedLoginCount = pyqtSignal(str)

    def __init__(self, mainWindow: IMainWindow):
        super().__init__()

        self.main_window = mainWindow
        self.spinBox: QSpinBox = self.main_window.spinBox # threads
        self.plainTextEdit_2: QPlainTextEdit = self.main_window.plainTextEdit_2 # output
        self.tableWidget = EmailAccountTable(self.main_window.tableWidget)
        self.lineEdit_2: QLineEdit = self.main_window.lineEdit_2
        self.lineEdit_3: QLineEdit = self.main_window.lineEdit_3
        self.lineEdit_5: QLineEdit = self.main_window.lineEdit_5

        self.mutex = QMutex()
        self.running = True

    def get_email_accounts(self) -> Queue:
        q = Queue()

        for row in range(self.tableWidget.table.rowCount()):
            email = self.tableWidget.table.item(row, 0).text()
            email_pwd = self.tableWidget.table.item(row, 1).text()
            
            q.put([row, email, email_pwd])
        
        return q
    
    def updateValue(self, label: QLabel) -> str:
        return str(int(label.text()) + 1)
    
    def saveEmail(self, fileName: str, email: str, state: int) -> None:
        with open(f'{self.main_window.output_folder_path}/{fileName}', 'a', encoding='utf-8') as file:
            match state:
                case -1:
                    self.updateFailedLoginCount.emit(self.updateValue(self.lineEdit_3))
                case 0:
                    self.updateSuccessfulLoginCount.emit(self.updateValue(self.lineEdit_2))
                case 1:
                    self.updateSendtEmailCount.emit(self.updateValue(self.lineEdit_5))

            file.write(f'{email}\n')