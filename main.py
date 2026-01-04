import email
import pandas as pd
import re
import sys
import ast
import time
from login import login
from bs4withAI import fetch_auction_data, ai_response


# Search criteria
key = 'FROM'
value1 = 'komornik@test.com'
email_status = "SEEN"

# Login to email
my_mail = login("credentials.yml")

# Search for unread emails
_,data = my_mail.search(None,key,value1,email_status)

# Splitting the data to get mail ids
mailids = data[0].split()
print(f"Number of unread emails from {value1}:", len(mailids))


# Initialize list to hold fetched messages
msgs = []

for i in mailids:
    typ,data = my_mail.fetch(i,'(RFC822)')
    msgs.append(data)

#print(msgs)


MY_SYNTAX = r'https://licytacje\.komornik\.pl/Notice/Details'
regex = MY_SYNTAX + r'/\d+'

def body_regex(body):
    if not body:
        return []
    all_links = re.findall(regex, body)
    unique_links = list(dict.fromkeys(all_links))
    return unique_links

rows = []

for msg in msgs:
    for response_part in msg:
        if isinstance(response_part, tuple):

            msg = email.message_from_bytes(response_part[1])
            email_from = msg['from']
            email_subject = msg['subject']
            
            email_body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        payload = part.get_payload(decode=True)
                        if payload:
                            email_body = payload.decode(errors='ignore')
                            break 
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    email_body = payload.decode(errors='ignore')

            rows.append({
                'From': email_from,
                'Subject': email_subject,
                'Body': email_body
            })




df = pd.DataFrame(rows)

if df.empty:
    print("No emails found.")
else:
    df['Links'] = df['Body'].apply(body_regex)
    df['Timestamp'] = pd.Timestamp.now()
    df['Processed'] = False
   #print(df['Links'])

cols = [col for col in ['Subject', 'Links', 'Timestamp', 'Processed'] if col in df.columns]
if cols:
    df[cols].to_csv('emails.csv', index=True, encoding='utf-8-sig')



if __name__ == "__main__":
    print("Starting processing of links...")
    if df['Links'].empty:
        print("No links to process. Brak linków do przetworzenia.")
        sys.exit()
    else:
        for index,row in df.iterrows():
            links = row['Links']
            for link in links:
                print(f"Processing link: {link}")
                soup = fetch_auction_data(link)
                if not soup.get('elicytacje_links'):
                    print("No elicytacje links found, searching with AI")
                    auction_data = ai_response(soup['text'])
                    print(auction_data)
                    time.sleep(2)
                else:
                    print("Elicytacje links found, need to check data on another site")

