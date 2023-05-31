from typing import Any
from modules import EmailAccountTable
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QMainWindow,
    QSpinBox,
    QPlainTextEdit,
    QFileDialog,
    QTableWidgetItem,
    QLineEdit,
)
from PyQt5.QtCore import QThread, QThreadPool, QRunnable, pyqtSignal
from queue import Queue
from datetime import datetime

import threading
import time
import imaplib
import os
import email


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

        self.plainTextEdit_2.setPlainText('')
        self.plainTextEdit_2.setEnabled(False)

        self.pushButton.setEnabled(False)
        self.pushButton_2.setEnabled(True)

        self.getter = GetSentEmailsThread(self)
        self.getter.insertPlainText.connect(self.plainTextEdit_2.insertPlainText)
        self.getter.finished.connect(self.task_finished)
        self.getter.setSuccess.connect(self.lineEdit_2.setText)
        self.getter.setFailed.connect(self.lineEdit_3.setText)
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


class GetSentEmailsThread(QThread):
    insertPlainText = pyqtSignal(str)
    setSuccess = pyqtSignal(str)
    setFailed = pyqtSignal(str)

    def __init__(self, main_window: MainWindow) -> None:
        super().__init__()

        self.main_window = main_window
        self.spinBox: QSpinBox = self.main_window.spinBox # threads
        self.plainTextEdit_2: QPlainTextEdit = self.main_window.plainTextEdit_2 # output
        self.tableWidget = EmailAccountTable(self.main_window.tableWidget)
        self.lineEdit_2: QLineEdit = self.main_window.lineEdit_2
        self.lineEdit_3: QLineEdit = self.main_window.lineEdit_3
        
        self.lock = threading.Lock()
        self.running = True

    def run(self) -> None:
        thread_count = self.spinBox.value()

        pool = QThreadPool()
        pool.setMaxThreadCount(thread_count)

        email_accounts = self.get_email_accounts()

        for _ in range(thread_count):
            task = GetSentEmailsTask(self, email_accounts)
            pool.start(task)

            time.sleep(.5)
        
        pool.waitForDone()

    def stop(self) -> None:
        self.running = False

    def set_output(self, value: str) -> None:
        self.insertPlainText.emit(f'{value}\n')

    def get_email_accounts(self) -> Queue:
        q = Queue()

        for row in range(self.tableWidget.table.rowCount()):
            email = self.tableWidget.table.item(row, 0).text()
            email_pwd = self.tableWidget.table.item(row, 1).text()
            
            q.put([row, email, email_pwd])
        
        return q
    
    def save_email_account(self, filename: str, value: str) -> None:
        with open(f'{self.main_window.output_folder_path}/{filename}', 'a', encoding='utf-8') as file:
            file.write(f'{value}\n')
    
    def is_success(self, email: str) -> None:
        self.setSuccess.emit(
            str(int(self.lineEdit_2.text()) + 1)
        )

        self.save_email_account('Email_Success.txt', email)

    def is_failed(self, email: str) -> None:
        self.setFailed.emit(
            str(int(self.lineEdit_3.text()) + 1)
        )

        self.save_email_account('Email_Error.txt', email)


class GetSentEmailsTask(QRunnable):
    def __init__(self, parent: GetSentEmailsThread, email_accounts: Queue):
        super().__init__()

        self.parent = parent
        self.email_accounts = email_accounts

    def get_imap_server(self, email: str) -> str:
        with open('imap.list') as  f:
            lines = f.readlines()
            lines = list(map(lambda x: x.strip(), lines))

        email_domain = email.split('@')[-1]

        for x in lines:
            try:
                items = x.split('|')
                domain = items[1]
                server = items[2]

                if email_domain == domain:
                    return server
            except:
                continue
            
        return None
    
    def get_string(self, value: Any) -> str:
        return str(value).encode('utf-8').decode("utf-8").strip("b'")
    
    def get_sent_box(self, conn: imaplib.IMAP4_SSL) -> str:
        _, mailbox_list = conn.list()

        for mailbox in mailbox_list:
            mailbox_name = self.get_string(mailbox)
            items = list(filter(lambda x: len(x.strip()) > 0, mailbox_name.split('"')))
            mailbox_name = items[-1]

            if not 'Sent' in mailbox_name:
                continue

            return mailbox_name
        
        return None

    def run(self) -> None:
        while self.parent.running:
            with self.parent.lock:
                if self.email_accounts.empty():
                    break

                row, username, password = self.email_accounts.get()
                self.email_accounts.task_done()

                imap_server = self.get_imap_server(username)

            if not imap_server:
                self.parent.tableWidget.update_status(row, 'không lấy imap server.')
                continue
            
            try:
                imap_conn = imaplib.IMAP4_SSL(imap_server)
                imap_conn.login(username, password)
            except Exception as e:
                with self.parent.lock:
                    self.parent.is_failed(username)

                self.parent.tableWidget.update_status(row, self.get_string(e))
                continue

            try:
                mailbox = self.get_sent_box(imap_conn)
                if not mailbox:
                    continue

                imap_conn.select(mailbox)

                _, data = imap_conn.search(None, "ALL")
                ids = data[0].split()

                for email_id in ids:
                    if not self.parent.running:
                        break

                    _, data = imap_conn.fetch(email_id, "(BODY[HEADER.FIELDS (TO)])")
                    headers = email.message_from_bytes(data[0][1])
                    to_header = headers.get("To")

                    if not to_header:
                        continue
                    
                    with self.parent.lock:
                        self.parent.set_output(email.utils.getaddresses([to_header])[0][-1])

                with self.parent.lock:
                    self.parent.is_success(username)

                self.parent.tableWidget.update_status(row, 'done!')
            except Exception as e:
                with self.parent.lock:
                    self.parent.is_failed(username)

                self.parent.tableWidget.update_status(row, str(e).encode('utf-8').decode("utf-8").strip("b'"))
                continue
            finally:
                try:
                    imap_conn.close()
                    imap_conn.logout()
                except:
                    pass