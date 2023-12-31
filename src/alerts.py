"""Modules allows to send http request, get custom content and send alert if needed"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import configparser
import sys
import requests
from retrying import retry


logging.basicConfig(
    filename="logs/metdata.log",
    format="%(asctime)s - %(levelname)s:%(message)s",
    level=logging.INFO,
)

config = configparser.ConfigParser()
config.read("config.ini")

url_config = config["api"]
url = url_config["url"]

smtp_config = config["smtp"]
s_email = smtp_config["sender_email"]
s_password = smtp_config["sender_password"]
r_email = smtp_config["receiver_email"]
s_server = smtp_config["smtp_server"]
s_port = smtp_config["smtp_port"]


@retry
def send_request():
    """Function for send request"""
    req_url = url
    headers_list = {}
    payload = ""
    response = requests.request(
        "GET", req_url, data=payload, headers=headers_list, timeout=3
    )

    return response.json()


def get_content(component):
    """Function to get content from request"""
    try:
        if send_request() is not None:
            data = send_request()
            logging.info("data fetch success")

            return data[0][f"{component}"]
    except IndexError:
        logging.error("Get content - failed")
        return None


def set_email_title():
    """Function to set email title"""
    if get_content("type") is None:
        logging.error("Set title failed")
        sys.exit()
    else:
        logging.info("Set title success")
        return f"Alert: {get_content('type')} {get_content('level')} \
            {get_content('status')}!!!"


def set_email_summary():
    """Function to set an email summary"""
    if get_content("type") is None:
        logging.error("Set summary failed")
        sys.exit()
    else:
        logging.info("Set summary success")
        headline = get_content("headline")

        if (
            "dublin" in headline.lower()
            or "kildare" in headline.lower()
            or "leinster" in headline.lower()
            or "ireland" in headline.lower()
        ):
            logging.info("Data for selected location - setting content")
            return f"{set_email_title()}\n\n{get_content('headline')}\
                    \n{get_content('description')}"
        else:
            logging.info("Not for selected location")
            sys.exit()


def send_alert():
    """Function to send an email"""
    sender_email = s_email
    sender_password = s_password
    receiver_email = r_email
    subject = set_email_title()
    message = set_email_summary()

    email_message = MIMEMultipart()
    email_message["From"] = sender_email
    email_message["To"] = receiver_email
    email_message["Subject"] = subject

    email_message.attach(MIMEText(message, "plain"))

    try:
        server = smtplib.SMTP(s_server, s_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, email_message.as_string())
        server.quit()
        logging.info("Email sent successfully!")
    except Exception as err:
        logging.error(err)


if __name__ == "__main__":
    send_alert()
