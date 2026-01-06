import email
import pandas as pd
import re
import sys
import time
from login import login
from bs4withAI import fetch_auction_data
from table_creation import create_tables_if_not_exists
from db_connect import db_login


conn,error = db_login()

# Search criteria
value1 = 'licytacje1@komornikid.pl'

# Login to email
my_mail = login("credentials.yml")

# Select inbox
my_mail.select("INBOX")

# Search for UNSEEN emails FROM specific sender (using UID)
status, data = my_mail.uid(
    'search',
    None,
    'SEEN',
    'FROM', 
    value1
)

#print("data:", data)

mailids = data[0].split()
print(f"Number of unread emails from {value1}: {len(mailids)}")
#print(mailids)

# Initialize list to hold fetched messages
msgs = []


for i in mailids:
    uid = i.decode('ascii')
    typ, data = my_mail.uid('fetch', uid, '(BODY.PEEK[])')
    if data is None or not data or len(data) == 0:
        print("No data for UID:", uid)
        continue
    if data[0] is None:
        print("No email content for UID:", uid)
        continue
    raw_email = data[0][1] + ("UID: " + uid + "\n").encode('utf-8')
    #print(data[0][1])
    msgs.append((raw_email,uid))
    print(f"UID {uid}, Length: {len(raw_email)}")




MY_SYNTAX = r'https://licytacje\.komornik\.pl/Notice/Details'
regex = MY_SYNTAX + r'/\d+'

def body_regex(body):
    if not body:
        return []
    all_links = re.findall(regex, body)
    unique_links = list(dict.fromkeys(all_links))
    return unique_links

rows = []


for raw_email,uid in msgs:
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
    print(f"✓ Parsed: {email_subject[:50]}, UID: {uid}")  # Debug





df = pd.DataFrame(rows)

if df.empty:
    print("No emails found.")
else:
    df['Links'] = df['Body'].apply(body_regex)
    df['Timestamp'] = pd.Timestamp.now()
    df['Processed'] = False
    df['UID'] = df['UID'].astype(str)
   #print(df['Links'])

cols = [col for col in ['Subject', 'Links', 'Timestamp', 'Processed', 'UID'] if col in df.columns]
if cols:
    df[cols].to_csv('emails.csv', index=True, encoding='utf-8-sig')


print(df)


if __name__ == "__main__":
    create_tables_if_not_exists(conn,error)

    print("Starting processing of links...")
    if 'Links' not in df.columns:
        print("No links to process. Brak linków do przetworzenia.")
        sys.exit()
    else:
        for index,row in df.iterrows():
            print(f"Processing row {index+1}/{len(df)} with UID: {row['UID']}")
            links = row['Links']
            for link in links:
                print(f"Processing link: {link}, Processing UID: {row['UID']}")
                data = fetch_auction_data(link)

                


