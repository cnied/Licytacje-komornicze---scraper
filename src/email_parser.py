import re
from .logger import setup_logger

logger = setup_logger("EMAIL_PARSE")

MY_SYNTAX = r'https://licytacje\.komornik\.pl/Notice/Details'
regex = MY_SYNTAX + r'/\d+'

def elicytacje_regex(body):
    """Wyciąga ID z linków elicytacje.komornik.pl/items/"""
    elicytacje_pattern = r'/items/(\d+)'
    return list(dict.fromkeys(re.findall(elicytacje_pattern, body or "")))

def body_regex(body):
    if not body:
        return []
    all_links = re.findall(regex, body)
    unique_links = list(dict.fromkeys(all_links))
    return unique_links



def fetch_email(my_mail,mail_from):

# Search for SEEN emails FROM specific sender (using UID)
    status, data = my_mail.uid(
        'search',
        None,
        'SEEN',
        'FROM',
        mail_from
    )

    mailids = data[0].split()
    logger.info("Number of unread emails from %s : %s", mail_from, len(mailids))
    #print(mailids)


    # Initialize list to hold fetched messages
    msgs = []

    for i in mailids:
        uid = i.decode('ascii')
        typ, data = my_mail.uid('fetch', uid, '(BODY.PEEK[])')
        #print(data)
        if data is None or not data or len(data) == 0:
            logger.error("No data for UID: %s", uid)
            continue
        if data[0] is None:
            logger.error("No email content for UID: %s", uid)
            continue
        raw_email = data[0][1] + ("UID: " + uid + "\n").encode('utf-8')
        msgs.append((raw_email, uid))
        logger.info("UID %s, Length: %s", uid, len(raw_email))
    
    return msgs


def parse_email_body(msg):
    email_body = ""
    for part in msg.walk():
            content_type = part.get_content_type()
            if content_type in ["text/plain", "text/html"]:
                payload = part.get_payload(decode=True)
                if payload:
                    email_body = payload.decode('utf-8', errors='ignore')
                    break
    return email_body