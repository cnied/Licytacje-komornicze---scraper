import email
import pandas as pd
import re
import sys
import os
from src.login import login
from src.bs4withAI import fetch_auction_data
from src.table_creation import create_tables_if_not_exists
from src.db_connect import db_login
from src.logger import setup_logger
from src.email_parser import fetch_email,parse_email_body,body_regex
from dotenv import load_dotenv


load_dotenv(".env")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")


def main():
    logger = setup_logger("MAIN")
    logger.info("Starting the application")

    conn, error = db_login()

    # Search criteria
    mail_from = 'licytacje1@komornikid.pl'

    # Login to email
    my_mail = login(USER,PASSWORD)

    # Select inbox
    my_mail.select("INBOX")

    # Search for SEEN emails FROM specific sender (using UID)
    # Initialize list to hold fetched messages
    msgs = fetch_email(my_mail,mail_from)
   
    rows = []

    for raw_email, uid in msgs:
        msg = email.message_from_bytes(raw_email)
        email_from = msg['from']
        email_subject = msg['subject']

        email_body = parse_email_body(msg)

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

    logger.info("Starting processing of links...")
    if 'Links' not in df.columns:
        logger.error("No links to process.")
        sys.exit()

    for index, row in df.iterrows():
        logger.info("Processing row %s/%s with UID: %s", index+1, len(df), row['UID'])
        links = row['Links']
        for link in links:
            logger.info("Processing link: %s, Processing UID: %s", link, row['UID'])
            fetch_auction_data(link,conn)


if __name__ == "__main__":
    main()
