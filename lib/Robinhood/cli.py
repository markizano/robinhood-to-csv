
import os, sys
import argparse
from easydict import EasyDict
from kizano import utils

from kizano import getLogger
log = getLogger(__name__)

class Config(EasyDict):
    def __init__(self):
        super()
        self.username = ''
        self.password = ''
        self.mfa = ''
        self.mongo_url = ''
        self.configfile = ''

def parseArguments():
    '''
    Get command line arguments and return argparse results.
    @return {object}
    '''
    parser = argparse.ArgumentParser(
      usage='''
Usage: %(prog)s [options]

Command line arguments are super-effective against
configuration files and environment variables!

''',
      formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
      '--config', '-c',
      action='store',
      dest='configfile',
      help='Config file to load. Defaults to ~/.config/robinhood/csv.yml',
      default=os.path.join( os.environ['HOME'], '.config', 'robinhood', 'csv.yml' )
    )

    parser.add_argument(
      '--username', '-u',
      action='store',
      dest='username',
      help='Username or email used to login to Robinhood.',
      default=False
    )

    parser.add_argument(
      '--password', '-p',
      action='store',
      dest='password',
      help='Password used to login to Robinhood. Use of this is discouraged. Prefer environment variable or config file.',
      default=False
    )

    parser.add_argument(
      '--mfa-code', '-m',
      action='store',
      dest='mfa',
      help='MFA Code from <MFA>-Authenticator app.',
      required=True
    )

    return parser.parse_args()

def loadConfigFile(configfile):
    '''
    Command line access to configuration.
    @return {object} Returns the YAML parsed configuration from the default or defined configuration file.
    '''
    try:
        return utils.read_yaml(configfile)
    except Exception as e:
        log.debug('failed: %s' % e)
        return {}

def getAllEnv():
    '''
    Get every environment variable we could ever use and combine it into a single object.
    Return that object as KVP (Key-Value Pairs).
    @return {object}
    '''
    return {
        'username': os.getenv('RH_USERNAME', ''),
        'password': os.getenv('RH_PASSWORD', ''),
        'mfa': os.getenv('RH_MFA_CODE', ''),
        'mongo_url': os.getenv('MONGO_URL', ''),
        'configfile': os.getenv('CONFIGFILE', '')
    }

def getConfig():
    '''
    Combine all the configurations into a single object.
    Return that object.
    @return {object}
    '''
    configProperties = [
        'username',
        'password',
        'mfa',
        'mongo_url',
        'configfile'
    ]
    args = parseArguments()
    env = getAllEnv()
    config = loadConfigFile(env['configfile'] or args.configfile)
    result = Config()
    for prop in configProperties:
        # First check command line arguments. They take precedence over anything else.
        if hasattr(args, prop) and getattr(args, prop):
            result[prop] = getattr(args, prop)
            continue
        # Next: Check environment variables. They have next layer of configurability.
        if prop in env and env[prop]:
            result[prop] = env[prop]
            continue
        # Finally: Check the config file and see if a value was set in the config file.
        if prop in config and config[prop]:
            result[prop] = config[prop]
    return result



