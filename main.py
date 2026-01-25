import email
from typing_extensions import Dict
import pandas as pd
import re
import sys
import os
from src.login import login
from src.scraper import fetch_auction_data
from src.table_creation import create_tables_if_not_exists
from src.db_connect import db_login
from src.logger import setup_logger
from src.email_parser import fetch_email,parse_email_body,body_regex
from src.db_fulfill import processed_links_list,update_processed_links,list_links_from_db
from src.db_connect import db_login
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
        df['UID'] = df['UID'].astype(str)


    




    #print(df)

    # Process auction links
    create_tables_if_not_exists(conn, error)
    lista_linkow = list_links_from_db(conn)

    logger.info("Starting processing of links...")
    if lista_linkow is None:
        logger.info("All links already processed.")
        sys.exit()

    
    df = pd.DataFrame(lista_linkow)
    print(df)


    for link in lista_linkow:
        logger.info("Processing link %s", link)
        update_processed_links(link, conn)
        fetch_auction_data(link, conn)


if __name__ == "__main__":
    main()
