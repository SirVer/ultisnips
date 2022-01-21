import sys
import threading
from bdb import BdbQuit

from UltiSnips import vim_helper


class RemotePDB(object):
    """
    Launch a pdb instance listening on (host, port).
    Used to provide debug facilities you can access with netcat or telnet.
    """

    singleton = None

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self._pdb = None

    def start_server(self):
        """
        Create an instance of Pdb bound to a socket
        """
        if self._pdb is not None:
            return
        import pdb
        import socket

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.server.bind((self.host, self.port))
        self.server.listen(1)
        self.connection, address = self.server.accept()
        io = self.connection.makefile("rw")
        parent = self

        class Pdb(pdb.Pdb):
            """Patch quit to close the connection"""

            def set_quit(self):
                parent._shutdown()
                super().set_quit()

        self._pdb = Pdb(stdin=io, stdout=io)

    def _pm(self, tb):
        """
        Launch the server as post mortem on the currently handled exception
        """
        try:
            self._pdb.interaction(None, tb)
        except:  # Ignore all exceptions part of debugger shutdown (and bugs... https://bugs.python.org/issue44461 )
            pass

    def set_trace(self, frame):
        self._pdb.set_trace(frame)

    def _shutdown(self):
        if self._pdb is not None:
            import socket

            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            self.server.close()
            self._pdb = None

    @staticmethod
    def get_host_port(host=None, port=None):
        if host is None:
            host = vim_helper.eval("g:UltiSnipsDebugHost")
        if port is None:
            port = int(vim_helper.eval("g:UltiSnipsDebugPort"))
        return host, port

    @staticmethod
    def is_enable():
        return bool(int(vim_helper.eval("g:UltiSnipsDebugServerEnable")))

    @staticmethod
    def is_blocking():
        return bool(int(vim_helper.eval("g:UltiSnipsPMDebugBlocking")))

    @classmethod
    def _create(cls):
        if cls.singleton is None:
            cls.singleton = cls(*cls.get_host_port())

    @classmethod
    def breakpoint(cls, host=None, port=None):
        if cls.singleton is None and not cls.is_enable():
            return
        cls._create()
        cls.singleton.start_server()
        cls.singleton.set_trace(sys._getframe().f_back)

    @classmethod
    def pm(cls):
        """
        Launch the server as post mortem on the currently handled exception
        """
        if cls.singleton is None and not cls.is_enable():
            return
        cls._create()
        t, val, tb = sys.exc_info()

        def _thread_run():
            cls.singleton.start_server()
            cls.singleton._pm(tb)

        if cls.is_blocking():
            _thread_run()
        else:
            thread = threading.Thread(target=_thread_run)
            thread.start()
