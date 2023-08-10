import requests
import base64
from datetime import datetime

import parser_functions as parser
import protocol_io as p_io

# #########################################################################
# WordPress I/O
# #########################################################################

# ~Update period for the Wordpress GET-s
# TODO - can be set to the desired value between 1 .. n (seconds)
UPDATE_PERIOD = 10.00  # sec

# Posts per page for GET.
# TODO - can be set to the desired value between 1 .. 100 (posts per page)
POST_PER_PAGE = 3

# Maximal number of GETs in one function loop.
# TODO - can be set to the desired value between 1 .. n  (but be careful...)
#  selected number of GETs will be dispatched between the threads
#  (As default we have  4 + CPU-logical-cores  threads in the pool)
PAGE_PER_LOOP_LIMIT = 16

# The used URL...
URL = 'https://www.thekey.academy/wp-json/wp/v2/posts'

# =========================================================================
# Other WP constants and variables
# =========================================================================
# Status of operation
STS_UNKNOWN_ERROR = -4
STS_IO_ERROR = -3
STS_RESPONSE_ERROR = -2
STS_JSON_ERROR = -1
STS_OK = 0

# State of the result - Result state for the returned status with synchronized values
# E.g. if status of operation is -1 : STS_JSON_ERROR --> ST_GLOBAL_HEADER_OK
ST_RESULT_INVALID = -4
ST_GLOBAL_HEADER_OK = -1
ST_RESULT_OK = 0

# other variables for GET parameter creation
# the latest dates
latest_date = None
latest_modify_date = None

# received (non-filtered) output
all_result_posts = 1
# received (filtered) outputs
result_posts = 1
result_pages = 1
# page variables for the posts
current_page = 1
pages = 1
# page variables for the del_test
check_page = 1
check_pages = 1
# datetime filter
modified_after = ''
# headers
headers = list()


# =========================================================================
# get_posts(string) -> dict
# =========================================================================
def get_posts(header_parameters):
    result = {
        # Result status of operation
        'status': STS_UNKNOWN_ERROR,
        # Global Header
        'total_posts': 0,
        'total_pages': 0,
        # Result as json object
        'json': dict()
    }

    # Compute basic authentication header
    auth_header = b"Basic " + base64.b64encode(b"guest:")

    try:
        # GET-Request
        entry = requests.get(URL + header_parameters, headers={'User-Agent': 'Custom', 'Authorization': auth_header})
        # Response check
        if entry.status_code >= 300:
            print("Error code: ", entry.status_code)
            print("(", entry.reason, ")")
            result['status'] = STS_RESPONSE_ERROR
            return result

        # Response is OK, retrieve the content (posts, pages, etc)
        result['total_posts'] = int(entry.headers.get('X-WP-Total'))
        result['total_pages'] = int(entry.headers.get('X-WP-TotalPages'))

        # convert entry to json
        entry_json_list = entry.json()
        result['json'] = entry_json_list
        # status is OK
        result['status'] = STS_OK
        return result

    except IOError as error:
        print("Wordpress: IO Error: ", error)
        result['status'] = STS_RESPONSE_ERROR
    except (requests.exceptions.InvalidJSONError, requests.exceptions.JSONDecodeError, TypeError) as error:
        print('Wordpress: JSON Error: ', error)
        result['status'] = STS_JSON_ERROR
    except Exception as error:
        print(error)
    finally:
        return result


# =========================================================================
# handle_posts()
# =========================================================================
def process_posts(process_parameters):
    task = process_parameters['task']
    header = process_parameters['header']

    result = {
        # Get-parameters
        'parameters': process_parameters,
        # Result status of operation
        'state': ST_RESULT_INVALID,
        # Global Header
        'total_posts': 0,
        'total_pages': 0,
        # Posts
        'posts': list()
    }

    # get the selected posts (filtered with the parameters)
    get_posts_result = get_posts(header)
    # was the action successful?

    # Header data is not available?
    if get_posts_result['status'] < ST_GLOBAL_HEADER_OK:
        # if not, we return the current result
        return result

    # otherwise analyze the json object and get the results (e.g. caption, date, etc..)
    try:
        result['total_posts'] = get_posts_result['total_posts']
        result['total_pages'] = get_posts_result['total_pages']

        for json_item in get_posts_result['json']:
            # parse the json object and count the words
            # - if the caller thread needs it, return an empty word-list otherwise
            parse_result = {'words': None}
            if task == 'parse':
                parse_result = parser.parse_json(json_item['content']['rendered'])
            # store the result
            protocol_data = p_io.ProtocolData(
                json_item['id'],
                json_item['title']['rendered'],
                json_item['date'],
                json_item['modified'],
                parse_result['words']
            )

            # print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
            # print(parse_result['content'])
            # print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')

            result['posts'].append(protocol_data)

        result['state'] = ST_RESULT_OK
        return result

    except KeyError as error:
        print(f'Wordpress: error by paring the returned json object! Key: {error} not found!')
    finally:
        return result


# =========================================================================
# is_ready
# =========================================================================
def is_ready():
    # 'ready' means, that every available posts are stored
    return p_io.protocol_object.get_post_count() >= all_result_posts


# =========================================================================
# client(executor, ...)
# =========================================================================
def client(executor):
    global current_page
    global check_page
    global check_pages
    global pages
    global modified_after
    global latest_date
    global latest_modify_date
    global all_result_posts
    global result_posts
    global result_pages
    global headers

    # Preparing the headers the threads
    #  the prepared headers will be dispatched between the threads
    #  the length of the list defines the amount of used threads from the pool
    #  we assume, that at least one post exists.

    # Create the GET-header for the threads:
    # We create two lists:
    # - [POST_PER_PAGE] * pages        --> For example [3, 3, ... ] with 'pages' elements
    # - range(current_page, pages + 1) --> Range between ['current_page' ... 'pages' + 1]
    last_page = min(pages + 1, current_page + PAGE_PER_LOOP_LIMIT)
    headers = headers + list(map(lambda t, pp, p: {'task': t, 'header': f"?per_page={pp}&page={p}" + modified_after},
                                 ['parse'] * pages, [POST_PER_PAGE] * pages, range(current_page, last_page)))

    # Extra GET to check if a post was deleted:
    # if the datetime filter is set we need an extra GET in every loop
    # - without time-date filters (normally just the 1. page in every loop)
    # - without parse
    # to get the max post count in result_all_posts
    if modified_after != '':
        headers.append({'task': 'del_check', 'header': f"?per_page={POST_PER_PAGE}&page={check_page}"})

    print('#########################################################################')
    print('headers: ', headers)
    print()

    for result in executor.map(process_posts, headers):
        try:

            # if GET was successful, we can remove this GET-header from the headers
            if result['state'] >= ST_GLOBAL_HEADER_OK:

                # The returned page count (result_pages) is needed for the
                # 'parse' tasks to determine if a next page exists
                if result['parameters']['task'] == 'parse':
                    # store the current page count
                    result_pages = result['total_pages']
                    result_posts = result['total_posts']
                    # we store the new value only if greater, just to have something until the 'del_check'
                    all_result_posts = max(all_result_posts, result_posts)
                # The maximal post count (without any filter)
                # can be determined only by 'del_check' tasks

                elif result['parameters']['task'] == 'del_check':
                    # store the max amount of posts
                    all_result_posts = result['total_posts']
                    check_pages = result['total_pages']

                    # test if there is any deleted post...
                    if all_result_posts < p_io.protocol_object.get_post_count():
                        # at least one post was deleted!
                        # we should test every post in our dictionary:
                        #  - increment check_page in every loop until check_pages reached
                        #  - mark every post in the dictionary, if we found the same entry in the received posts
                        #    (comparing the post-id-s)
                        #  - delete the not marked posts and send a broadcast to inform the clients
                        if check_page < check_pages:
                            # mark the received id-s as active
                            for post_object in result['posts']:
                                p_io.protocol_object.mark_post_as_active(post_object.id())
                            # select the next page
                            check_page = check_page + 1
                        else:
                            # every post was checked. delete the inactive posts from our memory-storage
                            p_io.protocol_object.purge_inactive_posts();
                            check_page = 1
                    else:
                        # set the check to the 1. page again
                        check_page = 1

            if result['state'] == ST_RESULT_OK:
                # remove the header of the successfully processed post
                headers.remove(result['parameters'])

                print('result_posts   ', result_posts)
                print('result_pages   ', result_pages)
                print('current_page   ', current_page)
                print('pages          ', pages)
                print('modified_after ', modified_after)

                # The returned posts should be stored only for 'parse' tasks
                if result['parameters']['task'] == 'parse':

                    for post_object in result['posts']:
                        # check the received dates and update the last dates if needed
                        try:
                            date = datetime.strptime(post_object.date(), '%Y-%m-%dT%H:%M:%S')
                            modify_date = datetime.strptime(post_object.modify_date(), '%Y-%m-%dT%H:%M:%S')

                            if latest_date is None or latest_date < date:
                                latest_date = date
                            if latest_modify_date is None or latest_modify_date < modify_date:
                                latest_modify_date = modify_date
                        except ValueError as error:
                            print('Wordpress: date conversion error! ', error)

                        # Store the fully received result
                        p_io.protocol_object.append_posts(post_object)

                        post_object.print()

        except KeyError as error:
            print('Wordpress: internal error, key not found: ', error)
        except Exception as error:
            print('Wordpress: internal error: ', error)

    # update the current_page
    current_page = last_page

    # Did we process every page?
    # - If not select the next page
    # - otherwise select 1. page (but this time with a datetime filter)
    if current_page <= result_pages:
        # update pages (at least 1)
        pages = max(result_pages, 1)
    else:
        # reset current page to the first one
        current_page = 1
        # reset available pages to 1
        pages = 1
        # Preparing the filter(s)
        #  if we got the available posts, next step is to use a datetime filter for GET
        #  in this way we are able to GET only the new / modified posts
        #  TODO - Theoretically by new posts the 'modified' field has the same value as 'date' field
        #  TODO   Therefore we filter only with 'modified'.
        #  TODO - If this solution is not correct, this code-part should be updated.
        modified_after = f"&modified_after={latest_modify_date}"
