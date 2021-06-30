from __future__ import print_function
from Robinhood import Robinhood
from login_data import collect_login_data
from profit_extractor import profit_extractor
import getpass
import collections
import argparse
import ast
from dotenv import load_dotenv, find_dotenv
import os
import pdb

logged_in = False

parser = argparse.ArgumentParser(
    description='Export Robinhood trades to a CSV file')
parser.add_argument(
    '--debug', action='store_true', help='store raw JSON output to debug.json')
parser.add_argument(
    '--username', default='', help='your Robinhood username')
parser.add_argument(
    '--password', default='', help='your Robinhood password')
parser.add_argument(
    '--mfa_code', help='your Robinhood mfa_code')
parser.add_argument(
    '--device_token', help='your device token')
parser.add_argument(
    '--profit', action='store_true', help='calculate profit for each sale')
parser.add_argument(
    '--dividends', action='store_true', help='export dividend payments')
args = parser.parse_args()
username = args.username
password = args.password
mfa_code = args.mfa_code
device_token = args.device_token

load_dotenv(find_dotenv())

robinhood = Robinhood()

# login to Robinhood
logged_in = collect_login_data(robinhood_obj=robinhood, username=username, password=password, device_token=device_token, mfa_code=mfa_code)

print("Pulling trades. Please wait...")

fields = collections.defaultdict(dict)
trade_count = 0
queued_count = 0

#holds instrument['symbols'] to reduce API ovehead {instrument_url:symbol}
cached_instruments = {}

'''
transfers:
{
  "next": "https://api.robinhood.com/public/ach/transfers/?cursor=cD0yMDE3LTEyLTE1KzIwJTNBMzMlM0EzNS44MTI5MDIlMkIwMCUzQTAw",
  "previous": null,
  "results": [
    {
      "id": "6d482f27-8dd6-44e8-a7f4-f40689848d4d",
      "ref_id": "6d482f27-8dd6-44e8-a7f4-f40689848d4d",
      "url": "https://api.robinhood.com/ach/transfers/6d482f27-8dd6-44e8-a7f4-f40689848d4d/",
      "cancel": null,
      "ach_relationship": "https://api.robinhood.com/ach/relationships/ed83a384-d6f5-4789-8b18-461dcb7a5f12/",
      "account": "https://api.robinhood.com/accounts/5QT38840/",
      "amount": "500.00",
      "direction": "deposit",
      "state": "completed",
      "fees": "0.00",
      "status_description": "",
      "scheduled": false,
      "expected_landing_date": "2021-06-17",
      "early_access_amount": "0.00",
      "created_at": "2021-06-11T18:54:01.659065-04:00",
      "updated_at": "2021-06-17T12:13:11.985414Z",
      "rhs_state": "completed",
      "expected_sweep_at": null,
      "expected_landing_datetime": "2021-06-17T09:00:00-04:00",
      "investment_schedule_id": null
    }, ...
  ]
}

relationships:
{
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "ed83a384-d6f5-4789-8b18-461dcb7a5f12",
      "verification_method": "bank_auth",
      "bank_account_number": "3331",
      "bank_account_nickname": "Chase",
      "verified": true,
      "state": "approved",
      "first_created_at": "2018-11-10T14:29:40.615906-05:00",
      "document_request": null,
      "url": "https://api.robinhood.com/ach/relationships/ed83a384-d6f5-4789-8b18-461dcb7a5f12/",
      "withdrawal_limit": "3206.66",
      "initial_deposit": "0.00",
      "account": "https://api.robinhood.com/accounts/5QT38840/",
      "unlink": "https://api.robinhood.com/ach/relationships/ed83a384-d6f5-4789-8b18-461dcb7a5f12/unlink/",
      "verify_micro_deposits": null,
      "unlinked_at": null,
      "created_at": "2018-11-10T14:29:40.615906-05:00",
      "bank_account_type": "checking",
      "bank_routing_number": "065400137",
      "bank_account_holder_name": "Mark Harris"
    }, ...
  ]
}
'''

# fetch order history and related metadata from the Robinhood API
orders = robinhood.get_endpoint('orders')
transfers = robinhood.get_endpoint('ach_transfers')
relationships = robinhood.get_endpoint('ach_relationships')

# load a debug file
# raw_json = open('debug.txt','rU').read()
# orders = ast.literal_eval(raw_json)

# store debug
if args.debug:
    import code
    print('Start a PDB debugging shell. Use `code.interact(local=locals())\' to start an interactive Python shell.')
    pdb.set_trace()

# do/while for pagination
paginated = True
page = 0
while paginated:
    for i, order in enumerate(orders['results']):
        executions = order['executions']

        symbol = cached_instruments.get(order['instrument'], False)
        if not symbol:
            symbol = robinhood.get_custom_endpoint(order['instrument'])['symbol']
            cached_instruments[order['instrument']] = symbol

        fields[i + (page * 100)]['symbol'] = symbol

        for key, value in enumerate(order):
            if value != "executions":
                fields[i + (page * 100)][value] = order[value]

        fields[i + (page * 100)]['num_of_executions'] = len(executions)
        fields[i + (page * 100)]['execution_state'] = order['state']

        if len(executions) > 0:
            trade_count += 1
            fields[i + (page * 100)]['execution_state'] = ("completed", "partially filled")[order['cumulative_quantity'] < order['quantity']]
            fields[i + (page * 100)]['first_execution_at'] = executions[0]['timestamp']
            fields[i + (page * 100)]['settlement_date'] = executions[0]['settlement_date']
        elif order['state'] == "queued":
            queued_count += 1
    # paginate
    if orders['next'] is not None:
        page = page + 1
        orders = robinhood.get_custom_endpoint(str(orders['next']))
    else:
        paginated = False

# for i in fields:
#   print fields[i]
#   print "-------"

# check we have trade data to export
if trade_count > 0 or queued_count > 0:
    print("%d queued trade%s and %d executed trade%s found in your account." %
          (queued_count, "s" [queued_count == 1:], trade_count,
           "s" [trade_count == 1:]))
    # print str(queued_count) + " queded trade(s) and " + str(trade_count) + " executed trade(s) found in your account."
else:
    print("No trade history found in your account.")
    quit()

# CSV headers
keys = fields[0].keys()
keys = sorted(keys)
csv = ','.join(keys) + "\n"

# CSV rows
for row in fields:
    for idx, key in enumerate(keys):
        if (idx > 0):
            csv += ","
        try:
            csv += str(fields[row][key])
        except:
            csv += ""

    csv += "\n"

# choose a filename to save to
print("Choose a filename or press enter to save to `robinhood.csv`:")
try:
    input = raw_input
except NameError:
    pass
filename = input().strip()
if filename == '':
    filename = "robinhood.csv"

try:
    with open(filename, "w+") as outfile:
        outfile.write(csv)
except IOError:
    print("Oops.  Unable to write file to ", filename)


if args.dividends:
    fields=collections.defaultdict(dict)
    dividend_count = 0
    queued_dividends = 0

    # fetch order history and related metadata from the Robinhood API
    dividends = robinhood.get_endpoint('dividends')


    paginated = True
    page = 0
    while paginated:
        for i, dividend in enumerate(dividends['results']):
            symbol = cached_instruments.get(dividend['instrument'], False)
            if not symbol:
                symbol = robinhood.get_custom_endpoint(dividend['instrument'])['symbol']
                cached_instruments[dividend['instrument']] = symbol

            fields[i + (page * 100)]['symbol'] = symbol

            for key, value in enumerate(dividend):
                if value != "executions":
                    fields[i + (page * 100)][value] = dividend[value]

            fields[i + (page * 100)]['execution_state'] = order['state']

            if dividend['state'] == "pending":
                queued_dividends += 1
            elif dividend['state'] == "paid":
                dividend_count += 1
        # paginate
        if dividends['next'] is not None:
            page = page + 1
            orders = robinhood.get_custom_endpoint(str(dividends['next']))
        else:
            paginated = False

    # for i in fields:
    #   print fields[i]
    #   print "-------"

    # check we have trade data to export
    if dividend_count > 0 or queued_dividends > 0:
        print("%d queued dividend%s and %d executed dividend%s found in your account." %
              (queued_dividends, "s" [queued_count == 1:], dividend_count,
               "s" [trade_count == 1:]))
        # print str(queued_count) + " queded trade(s) and " + str(trade_count) + " executed trade(s) found in your account."
    else:
        print("No dividend history found in your account.")
        quit()

    # CSV headers
    keys = fields[0].keys()
    keys = sorted(keys)
    csv = ','.join(keys) + "\n"

    # CSV rows
    for row in fields:
        for idx, key in enumerate(keys):
            if (idx > 0):
                csv += ","
            try:
                csv += str(fields[row][key])
            except:
                csv += ""

        csv += "\n"

    # choose a filename to save to
    print("Choose a filename or press enter to save to `dividends.csv`:")
    try:
        input = raw_input
    except NameError:
        pass
    filename = input().strip()
    if filename == '':
        filename = "dividends.csv"

    # save the CSV
    try:
        with open(filename, "w+") as outfile:
            outfile.write(csv)
    except IOError:
        print("Oops.  Unable to write file to ", filename)

if args.profit:
    profit_csv = profit_extractor(csv, filename)

