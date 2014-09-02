schopslet
=========

_schopslet_ is a script that allows the user to automate sending emails to
people. It is originally intented to reduce te effort to remind debtors to
pay their dues.

First compose your template email by editing `conf.sample.py` and saving the
file as `conf.py`.

Then create a CSV file with 5 columns. Each row will contain the information
to one debt. The columns 1 to 5 represent

1.  the "use"-flag, set to `1` or `0` to tell schopslet to use this row or not to;
2.  the debtor's name (used in the salutation);
3.  the debtor's email address;
4.  the description of the debt;
5.  and the amount of money owed for this debt.

An example of this file may look like this:

use | name          | email             | description          | amount |
---:| ------------- | ----------------- | -------------------- | ------:|
  1 | Alice         | alice@example.com | the barbecue         |   4.50 |
  1 | Bob           | bob@example.com   | the beer (friday)    |   3.00 |
  0 | Bob           | bob@example.com   | the tickets to Sikth |  11.00 |

If the file's name is `debtors.csv`, run `python schopslet.py debtors.csv`
to send Alice and Bob their emails. You will be prompted for your SMTP
credentials. Alternatively, you can provide this information by supplying
them as command line arguments or defining them in `conf.py`.

Have a nice day!
