'''
SBE__ prefix for "Sierra Big Export"
'''

import datetime, json, logging, os, pprint, sys
import requests
from requests.auth import HTTPBasicAuth

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


def manage_download():
    """ Controller function.
        Called by `if __name__ == '__main__':` """
    log.debug( 'starting' )
    tracker = check_tracker_file()
    next_batch = get_next_batch( tracker )
    download_file( next_batch )
    log.debug( 'complete' )
    return


def check_tracker_file():
    """ Ensures file exists, is up-to-date, and contains last-bib and range-info.
        Called by manage_download() """
    tracker = grab_tracker_file()
    check_tracker_lastbib( tracker )
    check_tracker_batches( tracker, start_bib=int('1000000'), end_bib=int(tracker['last_bib']) )
    log.debug( 'check_tracker_file() complete' )
    return 'foo'


def grab_tracker_file():
    """ Returns (creates if necessary) tracker from json file.
        Called by check_tracker_file() """
    TRACKER_FILEPATH = os.environ['SBE__TRACKER_JSON_PATH']
    try:
        with open(TRACKER_FILEPATH, 'rb') as f:
            tracker = json.loads( f.read() )
    except:
        with open(TRACKER_FILEPATH, 'wb') as f:
            tracker = {
                'last_updated': str(datetime.datetime.now()), 'last_bib': None, 'batches': [] }
            f.write( json.dumps(tracker, sort_keys=True, indent=2).encode('utf-8') )
    log.debug( 'tracker, ```%s```' % pprint.pformat(tracker) )
    return tracker


def check_tracker_lastbib( tracker):
    """ Obtains last bib if it doesn't already exist.
        Called by check_tracker_file() """
    TRACKER_FILEPATH = os.environ['SBE__TRACKER_JSON_PATH']
    LASTBIB_URL = os.environ['SBE__LASTBIB_URL']
    if not tracker['last_bib']:
        r = requests.get( LASTBIB_URL )
        tracker['last_bib'] = r.json()['entries'][0]['id']
        with open(TRACKER_FILEPATH, 'wb') as f:
            f.write( json.dumps(tracker, sort_keys=True, indent=2).encode('utf-8') )
    log.debug( 'tracker, ```%s```' % pprint.pformat(tracker) )
    return tracker


def check_tracker_batches( tracker, start_bib, end_bib ):
    """ Checks for batches and creates them if they don't exist.
        Called by check_tracker_file() """
    NUMBER_OF_CHUNKS = int( os.environ['SBE__NUMBER_OF_CHUNKS'] )
    if tracker['batches']:
        return
    full_bib_range = end_bib - start_bib
    chunk_number_of_bibs = int( full_bib_range / NUMBER_OF_CHUNKS )
    log.debug( 'chunk_number_of_bibs, `%s`' % chunk_number_of_bibs )
    ( chunk_start_bib, chunk_end_bib ) = ( start_bib, start_bib + chunk_number_of_bibs )
    for i in range( 0, NUMBER_OF_CHUNKS ):
        chunk_dct = {}
        chunk_dct['chunk_start_bib'] = chunk_start_bib
        chunk_dct['chunk_end_bib'] = chunk_end_bib
        chunk_dct['last_grabbed'] = None
        tracker['batches'].append( chunk_dct )
        chunk_start_bib = chunk_start_bib + chunk_number_of_bibs
        chunk_end_bib = chunk_end_bib + chunk_number_of_bibs
    log.debug( 'tracker, ```%s```' % pprint.pformat(tracker) )
    return tracker



### saved

def stuff():

    API_ROOT_URL = os.environ['SBE__ROOT_URL']
    HTTPBASIC_KEY = os.environ['SBE__HTTPBASIC_USERNAME']
    HTTPBASIC_SECRET = os.environ['SBE__HTTPBASIC_PASSWORD']
    FILE_DOWNLOAD_DIR = os.environ['SBE__FILE_DOWNLOAD_DIR']

    ## ok, let's get to work! ##

    ## get the token; looks like it's good for an hour

    token_url = '%stoken' % API_ROOT_URL
    log.debug( 'token_url, ```%s```' % token_url )
    r = requests.post( token_url, auth=HTTPBasicAuth(HTTPBASIC_KEY, HTTPBASIC_SECRET) )
    log.debug( 'token r.content, ```%s```' % r.content )
    token = r.json()['access_token']
    log.debug( 'token, ```%s```' % token )

    # ===================================
    # make a bib-request, just as a test
    # ===================================

    bib_url = '%sbibs/' % API_ROOT_URL
    payload = { 'id': '1000001' }
    log.debug( 'token_url, ```%s```' % token_url )
    custom_headers = {'Authorization': 'Bearer %s' % token }
    r = requests.get( bib_url, headers=custom_headers, params=payload )
    log.debug( 'bib r.content, ```%s```' % r.content )

    # ===================================
    # get 'last' bib
    # ===================================

    ## ok, we have the first bib, let's get the last (hack, close to the last)
    """
    TODO thought... there's probably a way to query the api to get this value.
    A hack, though, would be to run a cron job that would just get all the bibs over the last x/hours,
    and save the last one to a file at a specified location that the code below would load.
    """
    log.debug( '\n-------\ngetting end-bib\n-------' )
    today_date = str( datetime.date.today() )
    start_datetime = '%sT00:00:00Z' % today_date
    end_datetime = '%sT23:59:59Z' % today_date
    payload = {
        'limit': '1', 'createdDate': '[%s,%s]' % (start_datetime, end_datetime)  }
    r = requests.get( bib_url, headers=custom_headers, params=payload )
    log.debug( 'bib r.content, ```%s```' % r.content )
    end_bib = r.json()['entries'][0]['id']
    log.debug( 'end_bib, `%s`' % end_bib )

    # ===================================
    # detour, grab range of marc records
    # ===================================

    log.debug( '\n-------\ngetting small-range of marc records\n-------' )
    marc_url = '%sbibs/marc' % API_ROOT_URL
    payload = { 'id': '[1716554,1716564]' }  # i'll check these 10 records against the output of a saved-file, from this range, from the admin-corner script.
    r = requests.get( marc_url, headers=custom_headers, params=payload )
    log.debug( 'bib r.content, ```%s```' % r.content )
    file_url = r.json()['file']
    log.debug( 'file_url, ```%s```' % file_url )

    log.debug( '\n-------\ndownloading the marc file\n-------' )
    r = requests.get( file_url, headers=custom_headers )
    filepath = '%s/test.mrc' % FILE_DOWNLOAD_DIR
    with open(filepath, 'wb') as file_handler:
        for chunk in r.iter_content( chunk_size=128 ):
            file_handler.write( chunk )
    log.debug( 'file written to ```%s```' % filepath )




def get_record_sets(record_range, testing=False, settings=None):
    """Divides a set of record into sets based on the number specified
    in settings.py."""
    #Calculations to divide the bib set up into five parts.
    start = record_range['start_rec_int']
    end = record_range['end_rec_int']
    our_range = end - start

    set_chunks = settings.EXPORT_CHUNKS

    chunk = our_range / set_chunks

    range_sets = []

    for rec_set in range(1, set_chunks + 1):
        if rec_set == 1:
            this_start = start
            this_end = start + chunk
        else:
           this_start = last_end + 1
           this_end = this_start + chunk
           if this_end > end:
               this_end = end
        _d = {}
        _d['start'] = "%s%da" % (settings.RECORD_PREFIX, this_start)
        #If the testing variable exists, only do 10 recs per set.
        if testing:
            _d['end'] = "%s%da" % (settings.RECORD_PREFIX, this_start + settings.TEST_SET_SIZE)
        else:
             _d['end'] = "%s%da" % (settings.RECORD_PREFIX, this_end)
        last_end = this_end
        range_sets.append(_d)

    log.debug( 'range_sets, ```%s```' % pprint.pformat(range_sets) )
    return range_sets


if __name__ == '__main__':
    log.debug( 'starting' )
    manage_download()
    log.debug( 'complete' )
