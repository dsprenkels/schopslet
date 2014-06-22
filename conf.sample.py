# coding: utf-8

"""
Put you main configuration here and rename the file to `conf.py`.
"""

# `EMAIL TEMPLATE `is the email that must be filled with your own custom text
# %(debt_lines)s will be filled with a list of debts for this user, each on
# its own line. The items on this list will be composed by `DEBT_LINE`.
EMAIL_TEMPLATE = u'''
Dear %(name)s,

According to our administration you owe us the following:
%(debt_lines)s

You can transfer the money to the following account:
NL12 ABCD 3456 7890 12

Kind regards,

Bob
'''.strip()

# `DEBT_LINE` defines the format of each debt listed in the email. You can
# use the variables `amount` and `description` to format the string. By
# default, `amount` will be formatted as a string. But can be any type as
# long as it fits the type in the CSV file.
DEBT_LINE = u'   - €%(amount)s for %(description)s'

# These variables can be filled with default values. They can be overridden
# using command line arguments. Unknown variables will be prompted if they
# are not provdided. Setting your password here is NOT recommended!
#SMTP_HOST = 'stmp.example.com'
#SMTP_USERNAME = 'fluffyunicorn2000'
#SMTP_PASSWORD = 'mySecr3t'
#FROM_ADDR = 'fluffyunicorm2000@example.com'

# Set this to True if you don't want to confirm each sent email.
#YES_TO_ALL = False