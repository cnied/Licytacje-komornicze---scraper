import imaplib
import yaml


def login(credentials_path="credentials.yml"):
    with open(credentials_path, "r") as file:
        content = file.read()

    credentials = yaml.safe_load(content)
    user,password = credentials["user"], credentials["password"]
    imap_url = 'imap.gmail.com'
    my_mail = imaplib.IMAP4_SSL(imap_url)
    my_mail.login(user, password)
    my_mail.select('Inbox')
    return my_mail
