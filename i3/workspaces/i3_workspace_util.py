import threading

class NoneContext:
    def __enter__(self):
        pass
    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass

def iford(x):
    return x if type(x) is int else ord(x)

class AdvLock:
    write_lock = threading.Lock()
    write_thrad = None
    read_lock = threading.Lock()

    def __enter__(self):
        self.write_lock.acquire()
        self.write_thrad = threading.current_thread()
        self.read_lock.acquire()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.read_lock.release()
        self.write_thrad = None
        self.write_lock.release()

    def __init__(self):
        class Read:
            def __enter__(s):
                self.read_lock.acquire()
            def __exit__(s, exc_type, exc_value, exc_traceback):
                self.read_lock.release()
        self.read = Read()

        class PauseOnlyRead:
            def __enter__(s):
                self.read_lock.release()
            def __exit__(s, exc_type, exc_value, exc_traceback):
                self.read_lock.acquire()
        self.pause_only_read = PauseOnlyRead()

    def pause_only_read_if_locked(self):
        if self.write_thrad == threading.current_thread():
            return self.pause_only_read
        return NoneContext




def defautl_val(*ar):
    for i in ar:
        if i is not None:
            return i
    return None

def run(*arg, **kvarg):
    return lambda f: f(*arg, *kvarg)

