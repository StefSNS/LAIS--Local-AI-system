import smtplib, imaplib, email, json, os

def _get_config():
    path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(path):
        return json.load(open(path))["email"]
    return None

def send(to,subj,body):
    c = _get_config()
    if not c: return "Error: config.json not found"
    with smtplib.SMTP_SSL(c["smtp"],465) as s: s.login(c["user"],c["app_password"]); s.sendmail(c["user"],to,f"Subject:{subj}\n\n{body}")
    return "sent"
def inbox(n=5):
    c = _get_config()
    if not c: return "Error: config.json not found"
    m=imaplib.IMAP4_SSL(c["imap"]); m.login(c["user"],c["app_password"]); m.select()
    _,d=m.search(None,"ALL"); ids=d[0].split()[-n:]; return [{"subj":email.message_from_bytes(m.fetch(i,"(RFC822)")[1][0][1])["Subject"]} for i in ids]
