#!/usr/bin/env python

# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText

# Open a plain text file for reading.  For this example, assume that
# the text file contains only ASCII characters.

# Create a text/plain message
msg = MIMEText("OH THIS IS A MESSAGE")


me = 'USCGA BearShop'
you = 'John.W.Hammond@uscga.edu'
msg['Subject'] = 'Your Registration Verification Code'
msg['From'] = me
msg['To'] = you


# Send the message via our own SMTP server, but don't include the
# envelope header.
server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
server.ehlo()
server.login('uscga.bearshop@gmail.com', 'Go Coast Guard')
server.sendmail(me, [you], msg.as_string())
server.quit()