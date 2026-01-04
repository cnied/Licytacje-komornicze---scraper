import email
import pandas as pd
import re
from login import login



# Search criteria
key = 'FROM'
value1 = 'obwieszczenia@komornik.pl'
email_status = "UNSEEN"

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


regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

def body_regex(body):
   return re.findall(regex, body)
    

rows = []

for msg in msgs:
    for response_part in msg:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            email_from = msg['from']
            email_subject = msg['subject']
            email_body = msg.get_payload(decode=True).decode()
            # print('From : ' + email_from + '\n')
            # print('Subject : ' + email_subject + '\n')
            # print('Body : ' + email_body + '\n')
            rows.append({
                'From': email_from,
                'Subject': email_subject,
                'Body': email_body
            })



df = pd.DataFrame(rows)

if df.empty:
    pass
else:
    df['Links'] = df['Body'].apply(body_regex)
    print(df['Links'])


df.to_csv('emails.csv', index=False)