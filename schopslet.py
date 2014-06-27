#!/usr/bin/python2
# coding: utf-8

from argparse import ArgumentParser
import atexit
import csv
import email.charset
from email.encoders import encode_quopri
from email.mime.text import MIMENonMultipart
from getpass import getpass
import logging
import os
import re
from smtplib import SMTP
import sys

import sqlite3

"""
`schopslet` is a script that uses SMTP to send automated e-mails to people.
It is originally intended for automating the sending e-mails to debtors, but
can be used for any purpose.
"""

DEFAULT_CONFIG_FILE = u'conf.py'

def prompt(prompt, func=raw_input):
    """
    Prompt the user for input.
    """
    try:
        return func(prompt)
    except KeyboardInterrupt:
        sys.exit(130)

def write_email(debtors_database):
    """
    Write the emails to send by using the data provided by `debtors_database`.
    """
    queue = []

    # define email charset
    charset = email.charset.Charset('utf-8')
    charset.body_encoding = email.charset.QP

    cur = debtors_database.cursor()
    cur.execute('SELECT email, name FROM debtors')
    for debtor in cur.fetchall():
        to_addr, name = debtor
        cur.execute('''SELECT amount, description FROM debts
            WHERE debtor_email=?''', (debtor[0], ))
        rows = cur.fetchall()
        debt_lines = [CONFIG['debt_line'] %
            {'amount': row[0], 'description': row[1]} for row in rows]

        payload = CONFIG['email_template'] % {'name': name, 'debt_lines': u'\n'.join(debt_lines)}

        msg = MIMENonMultipart('text', 'plain')
        msg['To'] = to_addr
        msg['From'] = CONFIG['from_addr']
        msg['Subject'] = CONFIG['email_subject']
        msg.set_payload(payload, charset=charset)        
    
        queue.append(msg)
    return queue
 
def csv_read(debtors_database):
    """
    `csv_read` reads the CSV file provided in `CONFIG['debtors_file]` and
    inserts eacht record into `debtors_database`.
    """
    cur = debtors_database.cursor()
    fh = open(CONFIG['debtors_file'])
    reader = csv.reader(fh)

    lineno = 0
    for line in reader:
        lineno += 1
        csv_record = dict(zip(
            ['name', 'email', 'description', 'amount'], line))
        if (not re.match(r'\b[A-Z0-9._%+-]+@(?:[A-Z0-9-]+\.)+[A-Z]{2,4}\b',
                csv_record['email'], re.IGNORECASE)):
            if lineno == 1:
                logging.info("first line in CSV-file does not contain a valid "
                    "email adress (but contains '%s'), assuming file header" % csv_record['email'])
            else:
                logging.warning("line %(lineno)d in CSV-file does not contain "
                    "a valid email adress (but contains '%(email)s'), ignoring line" %
                    {'lineno': lineno, 'email': csv_record['email']})
            continue
        cur.execute('''INSERT OR IGNORE INTO debtors VALUES (?, ?)''',
            (csv_record['email'], csv_record['name']))
        cur.execute('''INSERT INTO debts VALUES (?, ?, ?)''',
            (csv_record['email'], csv_record['description'],
            csv_record['amount']))

    debtors_database.commit()

def db_init(debtors_database):
    """
    `db_init` initialises creates the tables we will use later on.
    """
    cur = debtors_database.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS debtors (
        email TEXT UNIQUE,
        name TEXT NOT NULL)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS debts (
        debtor_email TEXT REFERENCES debtors (email),
        description TEXT NOT NULL,
        amount TEXT NOT NULL)''')
    debtors_database.commit()

def verify_send(msg):
    """
    `verify_send` will ask the user to verify the message before sending it.
    It will return True if the user agrees to sending the message and False
    if the user rejects the message.
    """

    print u"\n"
    print (u"Sending from %(sender)s to %(recipient)s;\nSubject: %(subject)s\n\n%(payload)s\n" % 
        {'sender': msg['From'], 'recipient': msg['To'], 'subject': msg['Subject'], 'payload': msg.get_payload()})
    if CONFIG['yes_to_all']:
        response = 'yes'
    else:
        response = prompt(u'Do you want to continue? (y/n) ').strip()
    try_again = 2
    while try_again > 0:
        if re.match(r'^y(es?)?$', response, re.IGNORECASE):
            return True
        elif re.match(r'^no?$', response, re.IGNORECASE):
            return False
        response = prompt(u"Please answer 'yes' or 'no'. (y/n) ")
        try_again -= 1
    return False

def send_emails(queue):
    """
    `send_mails` will send the messages in queue (list). It will verify
    sending each email with the user first.
    """

    try:
        connection = SMTP(CONFIG['smtp_host'])
        if CONFIG['verbosity'] >= 2:
            connection.set_debuglevel(True)
        if CONFIG['use_tls']:
            connection.starttls()
        connection.login(CONFIG['smtp_username'], CONFIG['smtp_password'])
        for msg in queue:
            if verify_send(msg):
                connection.sendmail(msg['From'], msg['To'].split(', '), msg.as_string())
    except EnvironmentError, e:
        logging.error("connection error: '%s'" % e.strerror)
        sys.exit(e.errno)


if __name__ == '__main__':
    # configure ArgumentParser
    parser = ArgumentParser(
        description=u'Send automated emails.')
    parser.add_argument('--config', metavar='FILE', dest='config_file',
        help=u'specify a config file (default: %s)' % DEFAULT_CONFIG_FILE, default=DEFAULT_CONFIG_FILE)
    parser.add_argument('--host', '-H', metavar='HOST', dest='smtp_host', help=u'SMTP host')
    parser.add_argument('--user', '-u', metavar='USER', dest='smtp_username', help=u'SMTP username')
    parser.add_argument('--password', '-p', metavar='PASSWORD', dest='smtp_password', help=u"SMTP password (will be prompted if not provided)")
    parser.add_argument('--from', metavar='FROM', dest='from_addr', help=u"the sender address")
    parser.add_argument('--no-tls', dest='no_tls', action='store_true', help=u'do not use TLS')
    parser.add_argument('--verbose', '-v', action='count', help=u'be (more) verbose')
    parser.add_argument('--yes-to-all', '-y', dest='yes_to_all', action='store_true', help=u'do not confirm the sending of emails')
    parser.add_argument('debtors_file', metavar='FILE')
    args = parser.parse_args()

    # initialise logging
    if args.verbose == 0:
        LOGGING_LEVEL = logging.WARN
    elif args.verbose == 1:
        LOGGING_LEVEL = logging.INFO
    else:
        LOGGING_LEVEL = logging.DEBUG
    logging.basicConfig(format='%(levelname)s:%(message)s',
        level=LOGGING_LEVEL)
    logging.debug('Showing debug messages')
    
    # make sure the logger quits on exit
    atexit.register(logging.shutdown)

    # load config
    config_file = os.path.splitext(args.config_file)[0]
    logging.debug(config_file)
    config_module = __import__(config_file)
    conf_contents = dir(config_module)

    CONFIG = {}
    for variable in conf_contents:
        if re.match('^[A-Z_]+$', variable):
            CONFIG[variable.lower()] = getattr(config_module, variable)

    # override the configuration if a command line argument is given
    CONFIG['debtors_file'] = args.debtors_file
    CONFIG['smtp_host'] = args.smtp_host or CONFIG.get('smtp_host', None)
    CONFIG['smtp_username'] = args.smtp_username or CONFIG.get('smtp_username', None)
    CONFIG['smtp_password'] = args.smtp_password or CONFIG.get('smtp_password', None)
    CONFIG['use_tls'] = False if args.no_tls else True
    CONFIG['from_addr'] = args.from_addr or CONFIG.get('from_addr', None)
    CONFIG['verbosity'] = args.verbose
    CONFIG['yes_to_all'] = args.yes_to_all or CONFIG.get('yes_to_all', False)

    # ask for unspecified, but required data
    if not CONFIG['smtp_host']:
        CONFIG['smtp_host'] = prompt('SMTP hostname: ')
    if not CONFIG['smtp_username']:
        CONFIG['smtp_username'] = prompt('SMTP username: ')
    if not CONFIG['smtp_password']:
        CONFIG['smtp_password'] = prompt('SMTP password: ', getpass)
    if not CONFIG['from_addr']:
        CONFIG['from_addr'] = prompt('Sender address: ')

    # initialize a database and load the CSV-file into it
    database_name = ':memory:' if CONFIG['verbosity'] < 2 else 'schopslet.db'
    debtors_database = sqlite3.connect(database_name)
    db_init(debtors_database)
    csv_read(debtors_database)

    # compose emails and send them
    queue = write_email(debtors_database)
    if queue:
        send_emails(queue)
    else:
        logging.warn('No emails are sent, did something go wrong?')