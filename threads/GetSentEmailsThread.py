from .IGetSentEmailsThread import IGetSentEmailsThread
from PyQt5.QtCore import QThreadPool
from .tasks import GetSentEmailsTask
from MainWindow import IMainWindow

import time


class GetSentEmailsThread(IGetSentEmailsThread):
    def __init__(self, mainWindow: IMainWindow):
        super().__init__(mainWindow)

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