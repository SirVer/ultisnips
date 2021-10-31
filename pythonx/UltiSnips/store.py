from UltiSnips import vim_helper
from pathlib import Path
import hashlib
import json
from collections import defaultdict

class Store(object):
    """
    A dict-like supporting supporting the obj[key, default] syntax
    """
    def __init__(self):
        self._dict = dict()

    def __getitem__(self, key):
        if isinstance(key, tuple) :
            key, _default = key
            key = str(key)
            return self.setdefault(key, _default)
        else :
            key = str(key)
        return self._dict[key]

    def __getattr__(self, key):
        try :
            return getattr(self._dict, key)
        except :
            try :
                return self[key]
            except :
                pass
            raise

    def __setattr__(self, key, val):
        if key[0] == '_' :
            return super().__setattr__(key, val)
        else :
            self[key] = val

    def __setitem__(self, key, val):
        if isinstance(key, tuple) :
          key, _default = key
        key = str(key)
        return self._dict.__setitem__(key, val)
    def __delitem__(self, *args, **kwargs):
        return self._dict.__delitem__(*args, **kwargs)
    def __len__(self, *args, **kwargs):
        return self._dict.__len__(*args, **kwargs)
    def __iter__(self, *args, **kwargs):
        return self._dict.__iter__(*args, **kwargs)
    def __iter__(self, *args, **kwargs):
        return self._dict.__iter__(*args, **kwargs)

    def load(self):
        pass

    def save(self):
        pass

    def get(self, *args):
        """
        get(key[, default[, assigned_val]])
        Return for key if key is in the dictionary, else defaut.
        If assigned_val is present and key is not in the dict,
        assigned_val is assigned for the key, else nothing is inserted.
        """
        # If the call corresponds to dict.get() signature, forward
        arg_count = len(args)
        if arg_count <= 2:
            return self._dict.get(*args)
        if arg_count > 3 :
            raise TypeError(f'get expected at most 3 arguments, got {arg_count}')
        # else Do assign machinery
        if args[0] in self._dict :
          return self._dict[args[0]]
        self._dict[args[0]] = args[2]
        return args[1]
        


class BufferStore(Store):
    """
    A data store local to a buffer. Any python interpolation in a snippet running the same buffer
    access the same instance through `snip.store.buffer`
    """
    def __init__(self):
        self._dict = dict()

    _stores = defaultdict(lambda : BufferStore())

    @classmethod
    def bufferStore(cls, buffer_number):
        return cls._stores[buffer_number]


    @classmethod
    def currentBufferStore(cls):
        """
        Gets or create the store for the current buffer.
        """
        return cls.bufferStore(vim_helper.buf.number)

    @classmethod
    def clean(cls):
        """
        Check each buffer if it is alive, else delete it.
        """
        keys = set(cls._stores.keys())
        alive = { b.number for b in vim_helper.vim.buffers if b.valid }
        for k in keys - alive:
            del cls._stores[k]


class SessionStore(Store):
    """
    A Store common to a vim instance. Any python interpolation of any snippet in any buffer can access
    the same instance through `snip.store.session`
    """
    def __init__(self):
        self._dict = dict()

    _store = None
    @classmethod
    def get(cls):
        if cls._store is None :
            cls._store = cls()
        return cls._store


class _PersistentStore(Store):
    """
    A Store persistent saved to json format.
    """
    def __init__(self, path):
        self._path = path
        self.load()
        self._changed = False

    def load(self):
        try :
            with open(self._path, 'r') as f :
                self._dict = json.load(f)
        except :
            self._dict = dict()

    def save(self):
        if self._changed :
            with open(self._path, 'w') as f :
                json.dump(self._dict, f)

    def __setitem__(self, key, val):
        self._changed = True
        super().__setitem__(key, val)


def _encode_file_path(path):
    return hashlib.sha1(str(path))

def _store_dir():
    p = vim_helper.eval('g:UltiSnipsStoreDir')
    if p is not None :
        return Path(p).expanduser().resolve()
    return None


class FileStore(_PersistentStore):
    """
    Utility class to create a PersitantStore for a file accessible via `snip.store.file`.
    If the user do not provide a Store directory save path, it uses BufferStore as an alternate option (persistant only across the same vim session.
    """
    _alternate = dict()

    @classmethod
    def get(cls, path):
        path = Path(path).resolve()
        base = _store_dir()
        if base is None :
            return cls._getAlternate(path)
        return cls(base / _encode_file_path(path))

    @classmethod
    def _getAlternate(cls, path):
        rv = cls._alternate.get(path)
        if rv is None :
            rv = BufferStore()
            cls._alternate[path] = rv
        return rv

    @classmethod
    def bufferStore(cls, buffer_number):
        return cls.get(vim_helper.vim.buffers[buffer_number].name)

    @classmethod
    def currentBufferStore(cls):
        """
        Gets or create the store for the current buffer.
        """
        return cls.bufferStore(vim_helper.buf.number)


class CommonStore(_PersistentStore):
    """
    Persitent common accross all instances store accessible via `snip.store.common`.
    """
    _alternate = None

    @classmethod
    def get(cls):
        base = _store_dir()
        if base is None :
            return cls._getAlternate()
        return cls(base / 'common')

    @classmethod
    def _getAlternate(cls):
        if cls._alternate is None :
            cls._alternate = BufferStore()
        return cls._alternate

class StoreManager(object):
    """
    A manager to synchronize current stores
    """
    def __init__(self):
        self._reset()

    def _reset(self):
        self.buffer = None
        self.session = None
        self.file = None
        self.common = None
        self._snippet = []

    def _setup_state(self):
        number = vim_helper.buf.number
        self.buffer = BufferStore.bufferStore(number)
        self.session = SessionStore.get()
        self.file = FileStore.bufferStore(number)
        self.common = CommonStore.get()

    def _teardown_state(self):
        self.file.save()
        self.common.save()
        self._reset()

    def _pushSnippet(self):
        self._snippet.append(BufferStore())

    def _popSnippet(self):
        self._snippet.pop()

    @property
    def snippet(self):
        return self._snippet[-1]

