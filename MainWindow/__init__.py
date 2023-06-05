from modules import EmailAccountTable
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QTableWidgetItem,
)
from datetime import datetime
from threads import GetSentEmailsThread

import os


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi('ui/MainWindow.ui', self)

        self.pushButton.clicked.connect(self.handle_get)
        self.pushButton_2.clicked.connect(self.handle_stop)
        self.pushButton_3.clicked.connect(self.handle_output)
        self.pushButton_4.clicked.connect(self.handle_choose_file)

    def task_finished(self) -> None:
        self.pushButton.setEnabled(True)
        self.pushButton_2.setEnabled(False)
        self.plainTextEdit_2.setEnabled(True)

        self.pushButton_2.setText('Stop')

    def handle_get(self) -> None:
        self.lineEdit_2.setText(str(0))
        self.lineEdit_3.setText(str(0))
        self.lineEdit_5.setText(str(0))

        self.plainTextEdit_2.setPlainText('')
        self.plainTextEdit_2.setEnabled(False)

        self.pushButton.setEnabled(False)
        self.pushButton_2.setEnabled(True)

        self.getter = GetSentEmailsThread(self)
        self.getter.finished.connect(self.task_finished)
        self.getter.updateSentEmail.connect(self.plainTextEdit_2.insertPlainText)
        self.getter.updateSuccessfulLoginCount.connect(self.lineEdit_2.setText)
        self.getter.updateFailedLoginCount.connect(self.lineEdit_3.setText)
        self.getter.updateSendtEmailCount.connect(self.lineEdit_5.setText)
        self.getter.start()

    def handle_stop(self) -> None:
        self.pushButton_2.setText('Stop...')
        self.getter.stop()

    def handle_output(self) -> None:
        os.startfile('Output')

    def handle_choose_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Chọn tệp tin",
            directory="",
            filter="Text Files (*.txt)"
        )

        if not file_path:
            return
        
        table = EmailAccountTable(self.tableWidget)
        table.clear()

        with open(file_path, encoding='utf-8') as input:
            self.output_folder_path = f'Output/{datetime.now().strftime("%d-%m-%Y - %H-%M-%S")}'

            os.makedirs(self.output_folder_path)

            with open(f'{self.output_folder_path}/emails.txt', 'a', encoding='utf-8') as output:
                for account in input.readlines():
                    account = account.strip()

                    output.write(f'{account}\n')

                    email, email_pwd = account.strip().split(':')
                    
                    row = table.add_row(0, QTableWidgetItem(email))
                    table.update_email_pwd(row, email_pwd)
        
        self.lineEdit_4.setText(file_path)
        self.lineEdit.setText(str(table.table.rowCount()))