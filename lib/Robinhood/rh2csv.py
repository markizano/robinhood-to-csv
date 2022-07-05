
import os, sys
import io
import csv
from Robinhood.cli import getConfig
from Robinhood.api import Client

from kizano import getLogger
log = getLogger(__name__)

class Robinhood2CSV(object):
    '''
    Robinhood 2 CSV
    Take data from Robinhood and store in CSV files for later inspection & review.
    '''
    def __init__(self, config):
        self.config = config
        self.client = Client(self.config)

    def __enter__(self):
        log.debug(self.config)
        #self.fd = io.open(self.config.outfile, 'w')
        #self.csv = csv.DictWriter(self.fd, list(config.keys()))
        return self

    def __exit__(self, exType, exValue, exTraceback):
        #self.fd.close()
        pass

    def saveTransfers(self):
        '''
        Save all ACH/Wire transfers and orders to CSV.
        Sorted by date.
        '''
        achTransfers = self.client.achTransfers()
        achRelationships = self.client.achRelationships()
        orders = self.client.orders()
        


def main():
    config = getConfig()
    with Robinhood2CSV(config) as rh2csv:
        rh2csv.saveTransfers()
    return 0

if __name__ == '__main__':
    sys.exit(main())
