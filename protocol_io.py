import json

from shared_storage import SharedDict

# #########################################################################
# Protocol
# #########################################################################


# =========================================================================
# class ProtocolData
# =========================================================================
class ProtocolData:

    # =========================================================================
    def __init__(self, post_id, title, date, modify_date, words):
        self.__datadict = {'id': post_id,
                           'title': title,
                           'date': date,
                           'modify_date': modify_date,
                           'words': words,
                           'is_updated': True
                           }

    # =========================================================================
    def id(self): return self.__datadict['id']
    def title(self): return self.__datadict['title']
    def date(self): return self.__datadict['date']
    def modify_date(self): return self.__datadict['modify_date']
    def words(self): return self.__datadict['words']
    def is_updated(self): return self.__datadict['is_updated']

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

    # =========================================================================
    def __init__(self):
        self.__processed_posts = SharedDict()
        self.__changed_posts = SharedDict({'+': [], '-': [], '!': []})
        self.__tmp_active_set = set()

    # =========================================================================
    # =========================================================================
    # SERVER
    # - broadcasts the current changes
    #   {'+': [], '-': [], '!': []}
    # CLIENT
    #   {'req': 'ack'}
    # =========================================================================
    def get_broadcast_message(self):
        message = self.__changed_posts.json()
        self.__changed_posts.reset()
        return message

    # =========================================================================
    # =========================================================================
    # CLIENT
    #   {'req': 'ack'}
    # =========================================================================
    # CLIENT
    # - Get available post id-s
    #   {'req': 'id_list'}
    # SERVER
    # - Returns the available id-s
    #   {ack: 'id_list', 'obj': [12345, 4321, ...]}
    # =========================================================================
    # CLIENT
    # - Get words of selected post
    #   {'req': 'post', id: 14333}
    # SERVER
    # - Returns the selected post
    #   {ack: 'post', obj: {'id': 17444, title: 'This is a title', is_updated: True, words: {...}}
    # =========================================================================
    def process_message(self, message):
        answer = None
        try:
            json_msg = json.loads(message)
            req = json_msg['req']

            # ack
            if req == 'ack':
                # nothing to do...
                pass

            # id_list
            elif req == 'id_list':
                # get the keys as a list
                obj = list(self.__processed_posts.keys())
                print(obj)
                # create a string
                answer = json.dumps({'ack': req, 'obj': obj})

            # post
            elif req == 'post':
                # get the ProtocolData Object as dictionary
                obj = self.__processed_posts.get(json_msg['id'])
                # if it is a valid ProtocolData object, convert it to dictionary
                # otherwise use it as None value
                if obj is not None:
                    obj = obj.dict()
                # create a string
                answer = json.dumps({'ack': req, 'obj': obj})
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
            self.__changed_posts['+'].append(key)
        # Modified post?
        else:
            self.__changed_posts['!'].append(key)
        self.__processed_posts[key] = post

    # =========================================================================
    def mark_post_as_active(self, post_id):
        key = str(post_id)
        self.__tmp_active_set.add(key)

    # =========================================================================
    def purge_inactive_posts(self):
        self.__changed_posts['-'] = self.__processed_posts.purge(self.__tmp_active_set)
        pass

    # =========================================================================
    def get_post_count(self):
        return len(self.__processed_posts)


# =========================================================================
# Global Protocol Object
# =========================================================================
protocol_object = Protocol()
