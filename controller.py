'''
SBE__ prefix for "Sierra Big Export"
'''

import datetime, json, logging, math, os, pprint, sys
import requests
from requests.auth import HTTPBasicAuth
from lib.sierra import MarcHelper
from lib.tracker import TrackerHelper

logging.basicConfig(
    filename=os.environ['SBE__LOG_PATH'],
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s',
    datefmt='%d/%b/%Y %H:%M:%S'
    )
log = logging.getLogger(__name__)
log.debug( '\n-------\nstarting log' )

if (sys.version_info < (3, 0)):
    raise Exception( 'forcing myself to use python3 always' )

marc_helper = MarcHelper()
tracker_helper = TrackerHelper()


def manage_download():
    """ Controller function.
        Called by `if __name__ == '__main__':` """
    log.debug( 'starting' )
    tracker = check_tracker_file()
    next_batch = tracker_helper.get_next_batch( tracker )
    download_file( next_batch, tracker )
    log.debug( 'complete' )
    return


def check_tracker_file():
    """ Ensures file exists, is up-to-date, and contains last-bib and range-info.
        Called by manage_download() """
    tracker = tracker_helper.grab_tracker_file()
    tracker_helper.check_tracker_lastbib( tracker )
    tracker_helper.check_tracker_batches( tracker, start_bib=int('1000000'), end_bib=int(tracker['last_bib']) )
    log.debug( 'check_tracker_file() complete' )
    return tracker


def download_file( next_batch, tracker ):
    """ Initiates production of marc file, then downloads it.
        Called by manage_download() """
    token = marc_helper.get_token()
    marc_file_url = marc_helper.initiate_bibrange_request( token, next_batch )
    marc_helper.grab_file( token, marc_file_url, next_batch['file_name'] )
    tracker_helper.update_tracker( next_batch, tracker )
    log.debug( 'download complete' )
    return



if __name__ == '__main__':
    log.debug( 'starting' )
    manage_download()
    log.debug( 'complete' )
