import email
import pandas as pd
import re
import sys
from src.login import login
from src.bs4withAI import fetch_auction_data
from src.table_creation import create_tables_if_not_exists
from src.db_connect import db_login
from src.logger import setup_logger




MY_SYNTAX = r'https://licytacje\.komornik\.pl/Notice/Details'
regex = MY_SYNTAX + r'/\d+'

def body_regex(body):
    if not body:
        return []
    all_links = re.findall(regex, body)
    unique_links = list(dict.fromkeys(all_links))
    return unique_links


def main():
    logger = setup_logger()
    logger.info("Starting the application")

    conn, error = db_login()

    # Search criteria
    value1 = 'licytacje1@komornikid.pl'

    # Login to email
    my_mail = login("credentials.yml")

    # Select inbox
    my_mail.select("INBOX")

    # Search for SEEN emails FROM specific sender (using UID)
    status, data = my_mail.uid(
        'search',
        None,
        'SEEN',
        'FROM',
        value1
    )

    mailids = data[0].split()
    print(f"Number of unread emails from {value1}: {len(mailids)}")

    # Initialize list to hold fetched messages
    msgs = []

    for i in mailids:
        uid = i.decode('ascii')
        typ, data = my_mail.uid('fetch', uid, '(BODY.PEEK[])')
        if data is None or not data or len(data) == 0:
            logger.error("No data for UID: %s", uid)
            continue
        if data[0] is None:
            logger.error("No email content for UID: %s", uid)
            continue
        raw_email = data[0][1] + ("UID: " + uid + "\n").encode('utf-8')
        msgs.append((raw_email, uid))
        logger.info("UID %s, Length: %s", uid, len(raw_email))
    rows = []

    for raw_email, uid in msgs:
        msg = email.message_from_bytes(raw_email)
        email_from = msg['from']
        email_subject = msg['subject']

        email_body = ""

        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type in ["text/plain", "text/html"]:
                payload = part.get_payload(decode=True)
                if payload:
                    email_body = payload.decode('utf-8', errors='ignore')
                    break

        rows.append({
            'UID': uid,
            'From': email_from,
            'Subject': email_subject,
            'Body': email_body
        })
        logger.info("Parsed: %s, UID: %s", email_subject[:50], uid)

    df = pd.DataFrame(rows)

    if df.empty:
        logger.error("No emails found.")
    else:
        df['Links'] = df['Body'].apply(body_regex)
        df['Timestamp'] = pd.Timestamp.now()
        df['Processed'] = False
        df['UID'] = df['UID'].astype(str)

    cols = [col for col in ['Subject', 'Links', 'Timestamp', 'Processed', 'UID'] if col in df.columns]
    if cols:
        df[cols].to_csv('emails.csv', index=True, encoding='utf-8-sig')

    #print(df)

    # Process auction links
    create_tables_if_not_exists(conn, error)

    print("Starting processing of links...")
    if 'Links' not in df.columns:
        logger.error("No links to process. Brak linków do przetworzenia.")
        sys.exit()

    for index, row in df.iterrows():
        logger.info("Processing row %s/%s with UID: %s", index+1, len(df), row['UID'])
        links = row['Links']
        for link in links:
            logger.info("Processing link: %s, Processing UID: %s", link, row['UID'])
            fetch_auction_data(link)


if __name__ == "__main__":
    main()
