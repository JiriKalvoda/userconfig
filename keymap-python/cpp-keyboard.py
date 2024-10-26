#!/usr/bin/python3
from main import *

g["TARGET"] = "cpp"

def str_expand(cmd):
    s = cmd.replace('"', '\\"')
    return f'"{s}"'

def print_mod(mod):
    r = "0b"
    for m in [Modificator.ALT, Modificator.SUPER, Modificator.CTRL, Modificator.SHIFT]:
        r += '1' if mod & m else '0'
    return r


@action_serialize("AND")
def f(self):
    pass
@action_serialize("CMD")
def x(self):
    return f'k::cmd({str_expand(self.cmd)}),'
@action_serialize("GO_MODE")
def x(self):
    return f'k::goMode({str_expand(self.mode.name or "default")}),'

load_main()

def print_keyboard(m, modificators):
    for modificator in modificators:
        print(f"{{ {{ {str_expand(m.name or 'default')} , {print_mod(modificator)} }}, {{ {{")
        for i,x in enumerate(m.map_by_keys()):
            print(f"{{")
            for j,k in enumerate(x):
                if modificator in k:
                    print(k[modificator].action.serialize())
                else:
                    print("k::null,")
            print(f"}},")
        print(f"}} }} }},")
    

print('#include "../actions.cpp"')
print('map<pair<string,int>,KeyMode> keyModes = {')

for m in all_modes:
    used_modificators = m.used_modificators()
    print_keyboard(m, used_modificators)

print('};')

