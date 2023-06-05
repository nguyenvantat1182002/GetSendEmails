from .IGetSendEmailsTask import IGetSendEmailsTask
from threads import IGetSentEmailsThread
from queue import Queue
from PyQt5.QtCore import QMutexLocker

import imaplib
import email


class GetSentEmailsTask(IGetSendEmailsTask):
    def __init__(self, parent: IGetSentEmailsThread, email_accounts: Queue):
        super().__init__()

        self.parent = parent
        self.email_accounts = email_accounts

    def run(self) -> None:
        while self.parent.running:
            with QMutexLocker(self.parent.mutex):
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
                self.parent.tableWidget.update_status(row, self.get_string(e))

                with QMutexLocker(self.parent.mutex):
                    self.parent.saveEmail('Email_Error.txt', f'{username}:{password}', -1)

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

                    email_address = email.utils.getaddresses([to_header])[0][-1]
                    
                    with QMutexLocker(self.parent.mutex):
                        self.parent.saveEmail(
                            fileName='Email_Success.txt',
                            email=email_address,
                            state=1
                        )

                        self.parent.updateSentEmail.emit(f'{email_address}\n')


                self.parent.tableWidget.update_status(row, 'done!')
                
                with QMutexLocker(self.parent.mutex):
                    self.parent.saveEmail('Email_Login_Success.txt', f'{username}:{password}', 0)
            except Exception as e:
                self.parent.tableWidget.update_status(row, self.get_string(e))

                with QMutexLocker(self.parent.mutex):
                    self.parent.saveEmail('Email_Error.txt', f'{username}:{password}', -1)

                continue
            finally:
                try:
                    imap_conn.close()
                    imap_conn.logout()
                except:
                    pass