#!/usr/bin/env python3

from __future__ import print_function
from Robinhood import Robinhood
from login_data import collect_login_data
from profit_extractor import profit_extractor
import getpass
import collections
import argparse
import ast
from dotenv import load_dotenv, find_dotenv
import os, sys
import pdb

import pymongo

logged_in = False

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

# fetch order history and related metadata from the Robinhood API
orders = robinhood.get_endpoint('orders')
transfers = robinhood.get_endpoint('achTransfers')
relationships = robinhood.get_endpoint('achRelationships')

conn = pymongo.MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017/admin'))
db = conn.robinhood

relcount = len(relationships['results'])
db.relationships.delete_many({})
db.relationships.insert_many(relationships['results'])
while 'next' in relationships and relationships['next']:
    if relationships['next'] != None:
        print('Next relationship url: %s' % relationships['next'])
        relationships = robinhood.get_custom_endpoint(relationships['next'])
    relcount += len(relationships['results'])
    db.relationships.insert_many(relationships['results'])
print('Found %d account relationships.' % relcount)

tcount = len(transfers['results'])
db.transfers.delete_many({})
for transfer in transfers['results']:
    transfer['ach_relationship_id'] = os.path.basename( transfer['ach_relationship'].rstrip('/') )
db.transfers.insert_many(transfers['results'])
while 'next' in transfers and transfers['next']:
    if transfers['next'] != None:
        # For some reason, the "next" argument from Robinhood comes with this extra "/public" folder in the URI path.
        next_url = transfers['next'].replace('https://api.robinhood.com/public/', 'https://api.robinhood.com/')
        print('Next transfers url: %s' % next_url)
        transfers = robinhood.get_custom_endpoint(next_url)
    for transfer in transfers['results']:
        transfer['ach_relationship_id'] = os.path.basename( transfer['ach_relationship'].rstrip('/') )
    tcount += len(transfers['results'])
    db.transfers.insert_many(transfers['results'])
print('Found %d transfers.' % tcount)


ocount = len(orders['results'])
db.orders.delete_many({})
db.orders.insert_many(orders['results'])
while 'next' in orders and orders['next']:
    if orders['next'] != None:
        print('Next order URL: %s' % orders['next'])
        orders = robinhood.get_custom_endpoint(orders['next'])
    ocount += len(orders['results'])
    db.orders.insert_many(orders['results'])
print('Found %d orders.' % ocount)


db.instruments.delete_many({})
instruments = []
for instrument_url in db.orders.distinct('instrument'):
    instrument_id = os.path.basename( instrument_url.rstrip('/') )
    print('Fetching instrument: %s' % instrument_url)
    instrument = robinhood.get_custom_endpoint(instrument_url)
    instruments.append({
      '_id': instrument_id,
      'symbol': instrument['symbol'],
      'name': instrument['simple_name'],
      'full_name': instrument['name'],
      'type': instrument['type'],
      'market': os.path.basename(instrument['market'].rstrip('/')),
    })

print('Found %d instruments.' % len(instruments))
db.instruments.insert_many(instruments)


if args.debug:
    import code
    print('Start a PDB debugging shell. Use `code.interact(local=locals())\' to start an interactive Python shell.')
    pdb.set_trace()

sys.exit(0)

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

