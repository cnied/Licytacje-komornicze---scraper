import imaplib
from dotenv import load_dotenv
from src.logger import setup_logger
import os

logger = setup_logger("LOGIN")
load_dotenv(".env")

USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")

def login(USER,PASSWORD):
    logger.info("Logging in to email")
    imap_url = 'imap.gmail.com'
    my_mail = imaplib.IMAP4_SSL(imap_url)
    try:
        my_mail.login(USER, PASSWORD)
    except Exception as e:
        logger.error("Error logging in to email: %s", e)
        return None
    try:
        my_mail.select('Inbox')
    except Exception as e:
        logger.error("Error selecting inbox: %s", e)
        return None
    logger.info("Logged in to email")
    return my_mail
