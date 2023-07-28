from threading import Lock
import json
import copy


# #########################################################################
# Storage class for shared resources (dictionary)
# #########################################################################
class SharedDict:

    # =========================================================================
    def __init__(self, dictionary=None):
        self.__lock = Lock()
        if dictionary is not None:
            with self.__lock:
                self.__storage = dictionary
                self.__reset = copy.deepcopy(dictionary)
        else:
            with self.__lock:
                self.__storage = dict()
                self.__reset = dict()

    # =========================================================================
    def __getitem__(self, item):
        with self.__lock:
            value = self.__storage[item]
        return value

    # =========================================================================
    def __setitem__(self, key, value):
        with self.__lock:
            self.__storage[key] = value

    # =========================================================================
    def __delitem__(self, key):
        with self.__lock:
            del self.__storage[key]

    # =========================================================================
    def __len__(self):
        with self.__lock:
            length = len(self.__storage)
        return length

    # =========================================================================
    def pop(self, key):
        with self.__lock:
            value = self.__storage.pop(key)
        return value

    # =========================================================================
    def get(self, key):
        with self.__lock:
            value = self.__storage.get(key)
        return value

    # =========================================================================
    def keys(self):
        with self.__lock:
            keys = self.__storage.keys()
        return keys

    # =========================================================================
    def values(self):
        with self.__lock:
            values = self.__storage.values()
        return values

    # =========================================================================
    def items(self):
        with self.__lock:
            items = self.__storage.items()
        return items

    # =========================================================================
    def print(self):
        with self.__lock:
            print(self.__storage)

    # =========================================================================
    def json(self, key=None):
        with self.__lock:
            if key is None:
                result = json.dumps(self.__storage)
            else:
                result = json.dumps(self.__storage[key])
        return result

    # =========================================================================
    def reset(self):
        with self.__lock:
            self.__storage = copy.deepcopy(self.__reset)

    # =========================================================================
    # result = dict(filter(lambda i: i[0] in SET, DICT.items()))
    # result = list(filter(lambda k: k in SET, DICT))
    def purge(self, f_set):
        with self.__lock:
            purged_posts = list(filter(lambda k: k not in f_set, self.__storage))
            self.__storage = dict(filter(lambda i: i[0] in f_set, self.__storage.items()))
        return purged_posts
