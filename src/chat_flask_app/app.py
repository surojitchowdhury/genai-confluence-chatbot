#from chatbot import chatbot

from flask import Flask, render_template, request, redirect, session

from langchain.indexes import VectorstoreIndexCreator
from langchain.document_loaders import TextLoader
import os
from dotenv import load_dotenv
import pyotp
import time
import base64
import qrcode
import json
import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

load_dotenv()

import glob
import validators

app = Flask(__name__)
app.static_folder = 'static'
app.secret_key = secrets.token_urlsafe(16)

all_files = glob.glob(os.environ['LOCAL_CONFLUENCE_FILES_LOCATION'])
all_loaders = []
for file in all_files:
    all_loaders.append(TextLoader(file))
        
index = VectorstoreIndexCreator().from_loaders(all_loaders)

def sendmail(email_id, file_name, code):
    from_address = os.environ['FROM_EMAIL_ID']
    to_address = email_id

    # Create the root message and fill in the from, to, and subject headers
    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = 'Successful Registration to Confluence AI Chat'
    msgRoot['From'] = from_address
    msgRoot['To'] = to_address
    msgRoot.preamble = 'This is a multi-part message in MIME format for Login information.'

    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want to display.
    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)

    msgText = MIMEText('This is the alternative plain text message for Login information.')
    msgAlternative.attach(msgText)

    # We reference the image in the IMG SRC attribute by the ID we give it below
    msgText = MIMEText(f'<b>Please register on Google Authenticator App using following QR code or manual code</b>.<br><img src="cid:QRCode"><br>Manual Code for Setup: {code}', 'html')
    msgAlternative.attach(msgText)

    # This example assumes the image is in the current directory
    fp = open(file_name, 'rb')
    msgImage = MIMEImage(fp.read())
    fp.close()

    # Define the image's ID as referenced above
    msgImage.add_header('Content-ID', 'QRCode')
    msgRoot.attach(msgImage)


    mail = smtplib.SMTP('smtp.gmail.com', 587)
    mail.ehlo()
    mail.starttls()
    mail.login(from_address, os.environ['EMAIL_APP_PASSWORD'])
    mail.sendmail(from_address,to_address, msgRoot.as_string())

    mail.close()

def get_ai_reply(query):
    op = index.query_with_sources(query[:4096])
    if '\n' in op['sources']:
        files = op['sources'].split('\n')
    else:
        files = op['sources'].split(',')
    source_links = []
    for file_name in files:
        if not validators.url(file_name):
            print("Not valid URL, checking from file")
            try:
                with open(file_name.strip(), 'r') as file:
                    data = file.read().replace('\n', '')
                    source_links.append(data.split('source_page_webui:')[1])
            except Exception:
                pass
        else:
             print("valid URL: ", file_name)
             source_links.append(file_name)
    
    print("Source links: ", source_links)  
    if len(source_links)==0:  
        responses = op['answer'] 
    else:
        responses = op['answer'] + '\n\n Sources: \n\n' + '\n'.join(source_links)
    
    return responses



@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

@app.route("/invalid_login")
def invalid_login():
    return render_template("invalid_login.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/success_register")
def success_register():
    messages = session['messages']  
    return render_template("success_register.html", messages=json.loads(messages))

@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    return str(get_ai_reply(userText))

@app.route("/loginValidation", methods=['GET', 'POST'])
def validate_login():
    email = request.values.get('email')
    totp = request.values.get('totp')
    print("email: ", email)
    print("totp: ", totp)
    code = base64.b32encode(bytearray(email, 'ascii')).decode('utf-8')
    totp_gen = pyotp.TOTP(code)
    print("generated totp: ", totp_gen.now())
    if totp_gen.now() == totp:
        return redirect("/chatbot")
    else:
        return redirect("/invalid_login")

@app.route("/register_complete", methods=['GET', 'POST'])
def register_complete():
    email = request.values.get('email')
    print("email: ", email)
    code = base64.b32encode(bytearray(email, 'ascii')).decode('utf-8')
    qr_details = pyotp.totp.TOTP(code).provisioning_uri(name=email, issuer_name='AIChat-Confluence')

    #Creating an instance of qrcode
    qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=1)
    qr.add_data(qr_details)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    file_name = f'./static/images/qrcode001_{email}.png'
    img.save(file_name)
    messages = json.dumps({"code":code, "file_name": file_name })
    session['messages'] = messages

    if '@company.com' in email:
        sendmail(email, file_name, code)
    return redirect("/success_register")


if __name__ == "__main__":
    app.run()