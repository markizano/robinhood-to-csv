
import os, sys
import pymongo
from Robinhood.cli import getConfig

class Robinhood2Mongo(object):
    '''
    Robinhood 2 MongoDB
    Take data from Robinhood and store in MongoDB for later presentation.
    '''
    def __init__(self, config):
        self.mongo = pymongo.MongoClient(config.mongo_url)
        self.db = self.mongo.get_database('Robinhood')
        self.client = Robinhood.api.Robinhood()

    def saveOrders(self):
        '''
        Take order history and store to MongoDB.
        '''

    def saveTransfers(self):
        '''
        Save all ACH/Wire transfers to MongoDB.
        '''

    #> Speaking of saving relationships, can you save mine? (LOL)
    def saveRelationships(self):
        '''
        Save the ACH relationships since they contain some bank account metadata
        we can use in presentation later.
        '''

def main():
    config = getConfig()
    rh2mongo = Robinhood2Mongo(config)
    return 0

if __name__ == '__main__':
    sys.exit(main())
