import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import datetime
import re
import pytz
from boto3_toolkit import Boto3Utils

class SendEmail:
    def __init__(self,is_html = False):
        self.is_html = is_html
        self.config = Boto3Utils().get_secret(secret_name="GarminSleepStatisticsSecrets")
        ist = pytz.timezone('Asia/Kolkata')
        self.sync_date = datetime.datetime.today().astimezone(ist).strftime('%d-%m-%y')
    
    def send_email(self,  body,rec_email = None,subject = "", file_paths = None):
        rec_email = self.config['REC_EMAIL'] if not rec_email else rec_email
        msg = MIMEMultipart()
        msg['From'] = self.config['BULLETIN_EMAIL_ADDRESS']
        msg['To'] = rec_email
        msg['Subject'] = f"{self.sync_date} {subject.strip()}"
        if not self.is_html:
            msg.attach(MIMEText(body, 'plain'))
        else:            
            msg.attach(MIMEText(body, 'html'))
        if file_paths and isinstance(file_paths,list):
            for file_path in file_paths:
                attachment = open(file_path, 'rb')
                part = MIMEBase('application', 'octet-stream')
                part.set_payload((attachment).read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', "attachment; filename= " + file_path.split("/")[-1])
                msg.attach(part)
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(self.config['BULLETIN_EMAIL_ADDRESS'], self.config['BULLET_EMAIL_ADDRESS_APP_PASSWORD'])
            server.sendmail(self.config['BULLETIN_EMAIL_ADDRESS'], rec_email, msg.as_string())