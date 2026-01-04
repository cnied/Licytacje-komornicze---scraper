import imaplib
import email
import yaml
import pandas as pd
import re

with open("credentials.yml", "r") as file:
    content = file.read()

credentials = yaml.safe_load(content)
user,password = credentials["user"], credentials["password"]
imap_url = 'imap.gmail.com'
my_mail = imaplib.IMAP4_SSL(imap_url)
my_mail.login(user, password)
my_mail.select('Inbox')

key = 'FROM'
value = 'obwieszczenia@komornik.pl'

_,data = my_mail.search(None,key,value)

mailids = data[0].split()

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
df['Links'] = df['Body'].apply(body_regex)
print(df['Links'])


df.to_csv('emails.csv', index=False)