import smtplib, imaplib, email, json
c=json.load(open("config.json"))["email"]
def send(to,subj,body):
    with smtplib.SMTP_SSL(c["smtp"],465) as s: s.login(c["user"],c["app_password"]); s.sendmail(c["user"],to,f"Subject:{subj}\n\n{body}")
    return "sent"
def inbox(n=5):
    m=imaplib.IMAP4_SSL(c["imap"]); m.login(c["user"],c["app_password"]); m.select()
    _,d=m.search(None,"ALL"); ids=d[0].split()[-n:]; return [{"subj":email.message_from_bytes(m.fetch(i,"(RFC822)")[1][0][1])["Subject"]} for i in ids]
