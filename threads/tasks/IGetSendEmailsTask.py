from PyQt5.QtCore import QRunnable
from typing import Any

import imaplib


class IGetSendEmailsTask(QRunnable):
    def __init__(self) -> None:
        super().__init__()

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