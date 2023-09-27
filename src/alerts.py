import requests
from retry import retry
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import configparser
import logging


logging.basicConfig(
    format='%(asctime)s - %(levelname)s:%(message)s', level=logging.INFO)

config = configparser.ConfigParser()
config.read('config.ini')

url_config = config['api']
url = url_config['url']

smtp_config = config['smtp']
s_email = smtp_config['sender_email']
s_password = smtp_config['sender_password']
r_email = smtp_config['receiver_email']
s_server = smtp_config['smtp_server']
s_port = smtp_config['smtp_port']


@retry()
def send_request():
    """Function for send request"""
    req_url = url
    headers_list = {}
    payload = ""
    response = requests.request(
        "GET", req_url, data=payload,  headers=headers_list, timeout=3)

    return response.json()


def get_content(component):
    """Function to get content from request"""
    data = send_request()

    return data[0][f'{component}']


def set_email_title():
    """Function to set email title"""

    return f"Alert: {get_content('type')} {get_content('level')} {get_content('status')}!!!"


def set_email_summary():
    """Function to set email summary"""

    return f"{set_email_title()}\n\n{get_content('headline')}\n{get_content('description')}"


def send_alert():
    """Function to send email"""
    sender_email = s_email
    sender_password = s_password
    receiver_email = r_email
    subject = set_email_title()
    message = set_email_summary()

    email_message = MIMEMultipart()
    email_message['From'] = sender_email
    email_message['To'] = receiver_email
    email_message['Subject'] = subject

    email_message.attach(MIMEText(message, 'plain'))

    try:
        server = smtplib.SMTP(s_server, s_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, email_message.as_string())
        server.quit()
        logging.info('Email sent successfully!')
    except Exception as err:
        logging.error(err)


if __name__ == '__main__':
    send_alert()