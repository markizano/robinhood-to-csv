
import os, sys
import argparse

def main():
    '''
    Main entrypoint into the application.
    '''
    parser = argparse.ArgumentParser(description='Export Robinhood trades to a CSV file')

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


if __name__ == '__main__':
  sys.exit(main())

