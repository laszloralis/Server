import json

from shared_storage import SharedDict
from websocket_io import WebsocketIO


# #########################################################################
# Protocol
# #########################################################################

# =========================================================================
# class ProtocolData
# =========================================================================
class ProtocolData:
    POST_ID = 'id'
    TITLE = 'title'
    DATE = 'date'
    MODIFY_DATE = 'modify_date'
    STATUS = 'status'
    WORDS = 'words'

    STS_NEW = 'new'
    STS_MODIFIED = 'modified'

    # =========================================================================
    def __init__(self, post_id, title, date, modify_date, words):
        self.__datadict = {ProtocolData.POST_ID: post_id,
                           ProtocolData.TITLE: title,
                           ProtocolData.DATE: date,
                           ProtocolData.MODIFY_DATE: modify_date,
                           ProtocolData.STATUS: ProtocolData.STS_NEW,
                           ProtocolData.WORDS: words
                           }

    # =========================================================================
    def id(self): return self.__datadict[ProtocolData.POST_ID]
    def title(self): return self.__datadict[ProtocolData.TITLE]
    def date(self): return self.__datadict[ProtocolData.DATE]
    def modify_date(self): return self.__datadict[ProtocolData.MODIFY_DATE]
    def status(self): return self.__datadict[ProtocolData.STATUS]
    def words(self): return self.__datadict[ProtocolData.WORDS]
    def mark_new(self): self.__datadict[ProtocolData.STATUS] = ProtocolData.STS_NEW
    def mark_modified(self): self.__datadict[ProtocolData.STATUS] = ProtocolData.STS_MODIFIED

    # =========================================================================
    def print(self):
        print(self.__datadict)

    # =========================================================================
    def json(self):
        return json.dumps(self.__datadict)

    # =========================================================================
    def dict(self):
        return self.__datadict


# =========================================================================
# class Protocol
# =========================================================================
class Protocol:
    __NEW_POSTS = 'new_posts'
    __DELETED_POSTS = 'deleted_posts'
    __CHANGED_POSTS = 'changed_posts'
    __CLIENTS = 'clients'
    __REQ = 'req'
    __ACK = 'ack'
    __ID_LIST = 'id_list'
    __POST = 'post'
    __OBJ = 'obj'

    # =========================================================================
    def __init__(self):
        # Create websocketIO object with 'process_message' as the callback function
        self.__websocket_object = WebsocketIO(self.process_message)
        # Create the dictionaries and set
        self.__processed_posts = SharedDict()
        self.__changed_posts = SharedDict({Protocol.__NEW_POSTS: [],
                                           Protocol.__DELETED_POSTS: [],
                                           Protocol.__CHANGED_POSTS: [],
                                           Protocol.__CLIENTS: 0
                                           })
        self.__tmp_active_set = set()

    # =========================================================================
    def infinite_io_loop(self):
        self.__websocket_object.start_server()

    # =========================================================================
    def notify_clients(self):
        # =========================================================================
        # SERVER
        # - broadcasts the current changes
        #   {'new_posts': [], 'deleted_posts': [], 'changed_posts': [], 'clients:' n }
        # CLIENT
        #   {'req': 'ack'}
        # =========================================================================
        self.__changed_posts[Protocol.__CLIENTS] = self.__websocket_object.get_client_count()
        message = self.__changed_posts.json()
        self.__changed_posts.reset()
        self.__websocket_object.broadcast(message)

    # =========================================================================
    def process_message(self, message):
        answer = None
        try:
            json_msg = json.loads(message)
            req = json_msg[Protocol.__REQ]

            # =========================================================================
            # ack
            # =========================================================================
            # CLIENT --> {'req': 'ack'}
            # =========================================================================
            if req == Protocol.__ACK:
                # nothing to do...
                pass

            # =========================================================================
            # id_list - Get available post id-s
            # =========================================================================
            # CLIENT --> {'req': 'id_list'}
            #
            # SERVER --> {'ack': 'id_list', 'obj': [12345, 4321, ...]}
            # (Returns the available id-s)
            # =========================================================================
            elif req == Protocol.__ID_LIST:
                # get the keys as a list
                obj = list(self.__processed_posts.keys())
                # create a string
                answer = json.dumps({Protocol.__ACK: req, Protocol.__OBJ: obj})

            # =========================================================================
            # posts - Get words of selected post
            # =========================================================================
            # CLIENT --> {'req': 'post', 'id': 14333}
            #
            # SERVER --> {'ack': 'post', 'obj': {'id': 17444, title: 'This is a title', status: ***, words: {...}}
            # (Returns the requested post or 'None'/null if the post not exists)
            # =========================================================================
            elif req == Protocol.__POST:
                # get the ProtocolData Object as dictionary
                obj = self.__processed_posts.get(json_msg[ProtocolData.POST_ID])
                # if it is a valid ProtocolData object, convert it to dictionary
                # otherwise use it as None value
                if obj is not None:
                    obj = obj.dict()
                # create a string
                answer = json.dumps({Protocol.__ACK: req, Protocol.__OBJ: obj})
            return answer

        except json.JSONDecodeError as error:
            print(f'Protocol error \'{message}\': {error}')
        except KeyError as error:
            print(f'Protocol error \'{message}\': {error}')

    # =========================================================================
    def append_posts(self, post):
        key = str(post.id())
        # New post?
        if self.__processed_posts.get(key) is None:
            # the default post status is new thus we simply store it
            self.__changed_posts[Protocol.__NEW_POSTS].append(key)
        # Modified post?
        else:
            # mark the post as modified
            post.mark_modified()
            #store it
            self.__changed_posts[Protocol.__CHANGED_POSTS].append(key)
        self.__processed_posts[key] = post

    # =========================================================================
    def mark_post_as_active(self, post_id):
        key = str(post_id)
        self.__tmp_active_set.add(key)

    # =========================================================================
    def purge_inactive_posts(self):
        self.__changed_posts[Protocol.__DELETED_POSTS] = self.__processed_posts.purge(self.__tmp_active_set)
        self.__tmp_active_set.clear()

    # =========================================================================
    def get_post_count(self):
        return len(self.__processed_posts)


# =========================================================================
# Global Protocol Object
# =========================================================================
# create the Protocol object
protocol_object = Protocol()
