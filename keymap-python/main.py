from copy import copy
import sys
import key_names


class KeyMapException(Exception):
    pass

g = {}
modes_stack = []
all_modes = []

def set_global(name=None):
    def l(f):
        nonlocal name
        if name is None:
            name = f.__name__.upper()
            if name.startswith("GLOBAL__"):
                name = name[len("GLOBAL__"):]
        assert name not in g
        g[name] = f
        return f
    return l

INF = 1000
set_global("INF")(INF)


@set_global()
def load(fname, share_vars=False):
    vars = None
    if share_vars:
        vars = load_stack[-1].vars
    load_stack.append(LoadStackItem(vars))
    with open(fname) as f:
        exec(f.read(), *load_stack[-1].vars)

class LoadStackItem():
    def __init__(self, vars=None):
        if vars is None:
            vars = (create_load_globals(),)
        self.vars = vars

load_stack = []

class KeyAbstract:
    def __hash__(self):
        return hash(self._key())

    def __eq__(self, other):
        return self._key() == other._key()

from enum import IntFlag, auto
class Modificator(IntFlag):
    SHIFT = auto()
    CTRL = auto()
    SUPER = auto()
    ALT = auto()

modificator_none = Modificator(0)
set_global("MODIFICATOR_NONE")(modificator_none)

set_global("SHIFT")(Modificator.SHIFT)
set_global("CTRL")(Modificator.CTRL)
set_global("SUPER")(Modificator.SUPER)
set_global("ALT")(Modificator.ALT)

@set_global()
class Key(KeyAbstract):
    def _key(self):
        return (Key, self.row, self.col, self.mod)

    def __init__(self, row, col, mod=modificator_none):
        self.row = row
        self.col = col
        self.mod = mod

    def with_mod(self, mod):
        return self(add_mod=mod)

    def __call__(self, add_mod=None, add_col=None):
        dup = copy(self)
        if add_mod: dup.mod |= add_mod
        if add_col: dup.col += add_col
        return dup


@set_global("K")
def key_by_name(name, *arg, **kvarg):
    x = key_names.reverse[name]
    if x is None:
        raise KeyMapException("No sutch key name {name}")
    return Key(*x, *arg, **kvarg)

for i, x in enumerate(key_names.table):
    for j, y in enumerate(x):
        set_global(f"K_{y}")(Key(i, j))


@set_global("I3_DIRECT_MAPPER")
class I3DirectMapper(KeyAbstract):
    def _key(self):
        return id(self)

@set_global()
def i3_direct(cmd):
    return KeyMap(I3DirectMapper(), cmd, propagate=-INF)

@set_global("EXEC_ON_STARTUP_MAPPER")
class ExecOnStartupMapper(KeyAbstract):
    def __init__(self, always=False):
        self.always = always

    def _key(self):
        return id(self)

@set_global()
def exec_on_startup(cmd, always=False):
    return KeyMap(ExecOnStartupMapper(always=always), cmd, propagate=-INF)


@set_global()
def get_mode(index=-1):
    return modes_stack[index]

@set_global()
class Mode:
    def __init__(self, name):
        self.connected_contexts = []
        self.key_changer = lambda x:x
        self.name = name
        self.table = []
        if name in [x.name for x in all_modes]:
            raise KeyMapException(f"Duplicit mode name {name}")
        all_modes.append(self)

    def __enter__(self):
        modes_stack.append(self)
        for i in self.connected_contexts:
            i.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        for i in self.connected_contexts:
            i.__exit__(exc_type, exc_value, exc_traceback)
        p = modes_stack.pop()
        assert p == self

    def map_by_keys(self):
        out = [[{} for _ in x] for x in key_names.table]
        for i in self.table:
            if isinstance(i.key, Key):
                out[i.key.row][i.key.col][i.key.mod] = i
        return out

    def used_modificators(self):
        out = set()
        for i in self.table:
            if isinstance(i.key, Key):
                out.add(i.key.mod)
        l = list(out)
        l.sort()
        return l

class KeyChanger():
    def __init__(self):
        self.mode = get_mode()
        self.before = self.mode.key_changer
        self.mode.key_changer = self

    def __enter__(self): return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.mode.key_changer = self.before

    def __call__(self, key):
        return self.before(key)

@set_global("NO_KEY_CHANGE")
class NoKeyChange(KeyChanger):
    def __call__(self, key):
        return key

@set_global("ADD_MODIFICATOR")
class AddModificator(KeyChanger):
    def __init__(self, modificator):
        super().__init__()
        self.modificator = modificator
    def __call__(self, key):
        if isinstance(key, Key):
            key = key(self.modificator)
        return self.before(key)


@set_global
def mode_by_name(name):
    m = {i.name: i for i in all_modes}
    if name not in m:
        raise KeyMapException(f"No mode with name {name}")
    return m[name]


@set_global()
def std_mode(name):
    m = Mode(name)
    m.parrent = get_mode()
    with m:
        KeyMap(g["K_ESC"], g["GO_MODE"](g["ROOT_MODE"]))
        KeyMap(g["K_Enter"], g["GO_MODE"](m.parrent))
    return m


@set_global("M")
class KeyMap():
    def __init__(self, key, press_action=None, release_action=None, mode=None, propagate=0):
        action = press_action or release_action
        self.propagate = propagate
        if mode==None:
            mode = get_mode()
        key = mode.key_changer(key)
        self.key = key
        self.action = action
        self.press_action = press_action
        self.release_action = release_action
        if key in [x.key for x in mode.table]:
            raise KeyMapException(f"Duplicit map of key {key} in {mode} mode")
        mode.table.append(self)


def create_load_globals():
    return g.copy()

def load_main():
    if len(sys.argv) < 2:
        print("Missing mandatory argument -- main file.", file=sys.stderr)
        exit(1)
    with Mode("") as root_mode:
        set_global("ROOT_MODE")(root_mode)
        load(sys.argv[1])


class Action():
    pass

@set_global()
def global__print(*arg, **kvarg):
    print(*arg, **kvarg, file=sys.stderr)

@set_global()
def global__action_init(name=None, base=Action):
    def l(f=None):
        nonlocal name
        if name is None:
            name = f.__name__
        class Tmp(base):
            pass
        Tmp.__name__ = name
        if f is not None:
            Tmp.__init__ = f
        return Tmp
    return l
def action_init(name=None, base=Action):
    def l(f=None):
        Tmp = global__action_init(name, base)(f)
        g[Tmp.__name__] = Tmp
        return Tmp
    return l
@set_global()
def global__action_implement(cls):
    def l(f):
        cls.implement = f
        cls.serialize = lambda self: self.implement().serialize()
        return f
    return l
def action_implement(name):
    return global__action_implement(g[name])
@set_global()
def global__action_serialize(cls):
    def l(f):
        cls.serialize = f
        return f
    return l
def action_serialize(name):
    return global__action_serialize(g[name])



def assert_in(val, options):
    if val not in options:
        raise KeyMapException(
            f"Wrong value {val}, must be in {', '.join(options)}."
        )

dirs = ["left", "right", "up", "down"]
set_global("DIRS")(dirs)

import actions
