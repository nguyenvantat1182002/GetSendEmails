from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QSpinBox, QPlainTextEdit
from PyQt5.QtCore import QThread, QThreadPool, QRunnable, pyqtSignal
from queue import Queue

import threading
import time
import imaplib
import re


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi('ui/MainWindow.ui', self)

        self.pushButton.clicked.connect(self.handle_get)
        self.pushButton_2.clicked.connect(self.handle_stop)

    def task_finished(self) -> None:
        self.pushButton.setEnabled(True)
        self.pushButton_2.setEnabled(False)

        self.pushButton_2.setText('Stop')

    def handle_get(self) -> None:
        self.plainTextEdit_2.setPlainText('')

        self.pushButton.setEnabled(False)
        self.pushButton_2.setEnabled(True)

        self.getter = GetSentEmailsThread(self)
        self.getter.insertPlainText.connect(self.plainTextEdit_2.insertPlainText)
        self.getter.finished.connect(self.task_finished)
        self.getter.start()

    def handle_stop(self) -> None:
        self.pushButton_2.setText('Stop...')
        self.getter.stop()


class GetSentEmailsThread(QThread):
    insertPlainText = pyqtSignal(str)

    def __init__(self, main_window: MainWindow) -> None:
        super().__init__()

        self.main_window = main_window
        self.spinBox: QSpinBox = self.main_window.spinBox # threads
        self.plainTextEdit: QPlainTextEdit = self.main_window.plainTextEdit # input
        self.plainTextEdit_2: QPlainTextEdit = self.main_window.plainTextEdit_2 # output
        
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
        accounts = self.plainTextEdit.toPlainText().split('\n')
        q = Queue()

        for account in accounts:
            if not account:
                continue

            q.put(account.strip())

        return q


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
            items = x.split('|')
            domain = items[1]
            server = items[2]

            if email_domain == domain:
                return server
            
        return None

    def run(self) -> None:
        while self.parent.running:
            with self.parent.lock:
                if self.email_accounts.empty():
                    break

                account: str = self.email_accounts.get()
                self.email_accounts.task_done()

            email, email_pwd = account.split(':')

            try:
                with self.parent.lock:
                    imap_server = self.get_imap_server(email)

                imap_conn = imaplib.IMAP4_SSL(imap_server)
                imap_conn.login(email, email_pwd)

                imap_conn.select("Sent")

                _, data = imap_conn.search(None, "ALL")
                email_ids = data[0].split()

                for email_id in email_ids:
                    if not self.parent.running:
                        break

                    _, email_data = imap_conn.fetch(email_id, "(BODY[HEADER.FIELDS (TO)])")

                    emails = re.findall(
                        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                        email_data[0][1].decode('utf-8').strip()
                    )
                    
                    with self.parent.lock:
                        self.parent.set_output(emails[0])

                imap_conn.close()
                imap_conn.logout()
            except Exception as e:
                with open('errors.txt', 'w', encoding='utf-8') as f:
                    f.write(f'{str(e)}\n')