# Python 3 Core Libraries
import smtplib
import ssl
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

# Python 3 Project Libraries

# Python 3 Third Party Libraries

message_offline = """
Subject: Bot Is Offline!

{} number {} is down and is being automatically restarted.
"""

message_captcha = """
Subject: Stuck at Captcha!

{} number {} needs captcha solved!
"""

message_temp_ban = """
Subject: Temp Ban!

{} number {} has been temporarily banned!
"""


def send_email(config, reason, bot_name, bot_id):

    if reason == "captcha":
        message_body = message_captcha.format(bot_name.capitalize() + "_" + bot_id, bot_name.capitalize(), bot_id)
    elif reason == "offline":
        message_body = message_offline.format(bot_name.capitalize() + "_" + bot_id, bot_name.capitalize(), bot_id)
    elif reason == "temp_ban":
        message_body = message_temp_ban.format(bot_name.capitalize() + "_" + bot_id, bot_name.capitalize(), bot_id)
    else:
        return

    try:
        message = MIMEMultipart("alternative")

        message['From'] = formataddr(
            (str(Header(config["email"]["email_text_from"], 'utf-8')), config["email"]["email_address_from"]))

        message["Subject"] = config["email"]["subject"]

        email_message = message_body

        body = MIMEText(email_message, "plain")
        message.attach(body)
        toaddrs = config["email"]["address_list"]

        context = ssl.create_default_context()
        with smtplib.SMTP(config["email"]["smtp_hostname"], config["email"]["smtp_port"]) as server:
            server.starttls(context=context)
            server.login(config["email"]["smtp_username"], config["email"]["smtp_password"])
            server.sendmail(config["email"]["email_address_from"], toaddrs, message.as_string())
            server.quit()
            server.close()

    except smtplib.SMTPException as e:
        print(e)
