#!/usr/bin/python3
from main import *
import tex_template

g["TARGET"] = "tex"

print(tex_template.template)

def print_mod(mod):
    r = ""
    if mod & Modificator.SHIFT: r = "Shif " + r
    if mod & Modificator.CTRL: r = "Ctr " + r
    r += "$nl "
    if mod & Modificator.SUPER: r = "Super " + r
    if mod & Modificator.ALT: r = "Alt " + r
    return r

@set_global("TEX_te")
def te(x):
    return x.replace("[", "").replace("]", "").replace("$", "")

@set_global("TEX_p")
def p(r, g, b, text):
    return f"$printkey[$rgb[{r} {g} {b}]][{text}]"

def workspace_serialize(cmd, args):
    s = f"{cmd}\\nl "
    if args.workspace is not None:
        s += f"W: {args.workspace}"
    if args.master is not None:
        s += f"M: {args.master}"
    if args.slave is not None:
        s += f"S: {args.slave}"
    return p(*COLOR_WORKSPACE, s)

COLOR_CMD = 1, 0.8, 1
COLOR_MODE = 0.8, 0.8, 1
COLOR_WORKSPACE = 0, 1, 1
COLOR_FOCUS = 0, 1, 0
COLOR_EDIT_WM = 0.85, 1, 0
COLOR_EXIT = 1, 0, 0

@action_serialize("AND")
def f(self):
    return self.data[self.main].serialize()

@action_serialize("CMD")
def x(self):
    return p(*COLOR_CMD, f"$autofont[{te(self.cmd)}]")

@action_serialize("GO_MODE")
def x(self):
    return p(*COLOR_MODE, f"MODE$nl {self.mode.name}")


@action_serialize("GOTO_WORKSPACE")
def f(self):
    return workspace_serialize("Workspace", self)
@action_serialize("CONT_WORKSPACE")
def f(self):
    return workspace_serialize("Move to workspace", self)
@action_serialize("CONT_AND_GOTO_WORKSPACE")
def f(self):
    return workspace_serialize("Move and go to wsp.", self)
@action_serialize("SWAP_WORKSPACE")
def f(self):
    return workspace_serialize("Swap with workspace", self)
@action_serialize("SWAP_MASTER_WORKSPACE")
def f(self):
    return workspace_serialize("Swap master with", self)
@action_serialize("WORKSPACE_GUI")
def f(self):
    return p(*COLOR_WORKSPACE, "Workspace GUI")
@action_serialize("FOCUS_CONT")
def x(self):
    return p(*COLOR_FOCUS, f"Focus {self.argument}")
@action_serialize("MOVE_CONT")
def x(self):
    return p(*COLOR_EDIT_WM, f"Move {self.argument}")
@action_serialize("MOVE_WORKSPACE")
def x(self):
    return p(*COLOR_EDIT_WM, f"Move worksp. {self.argument}")
@action_serialize("SPLIT_CONT")
def x(self):
    return p(*COLOR_EDIT_WM, f"Split cont. {self.argument}")
@action_serialize("LAYOUT_CONT")
def x(self):
    return p(*COLOR_EDIT_WM, f"Layout. {self.argument}")
@action_serialize("RESIZE_CONT")
def x(self):
    return p(*COLOR_EDIT_WM, f"Resize {self.direction} by {self.size} pt")
@action_serialize("CONT_TOGGLE")
def x(self):
    return p(*COLOR_EDIT_WM, f"Toogle {self.prop_name}")

@action_serialize("RESTART_MANAGER")
def x(self):
    return p(*COLOR_EXIT, f"Restart WM $nl {self.variant or ''}")
@action_implement("EXIT_PROG")
def f(self):
    return g["CONFIRM_CMD"]("i3-msg exit", "Do you really want to EXIT i3?")
@action_serialize("SHOW_STATUSBAR")
def f(self):
    return p(*COLOR_EDIT_WM, f"Show statusbar")

#@action_serialize("POWEROFF")
def x(self):
    return p(*COLOR_EXIT, f"Restart")
#@action_serialize("RESTART")
def x(self):
    return p(*COLOR_EXIT, f"Restart")
#@action_serialize("RESTART")
def x(self):
    return p(*COLOR_EXIT, f"Restart")


load_main()


def print_keyboard(m, modificators):
    print(f"$def$modlist[")
    for modificator in modificators:
        print(f"$modificatorbox[{print_mod(modificator)}]")
    print(f"]")
    for i,x in enumerate(m.map_by_keys()):
        for j,k in enumerate(x):
            print(f"$defcs[key{i}x{j}][")
            print(f"$def$keyname[{te(key_names.table[i][j])}]")
            for modificator in modificators:
                if modificator in k:
                    print(k[modificator].action.serialize())
                else:
                    print("$printemptykey")
            print(f"]")
    print("$PrintKeyboard")
    

for m in all_modes:
    print(f'$Mode[{te(m.name)}][')
    used_modificators = m.used_modificators()
    if len(used_modificators)>4:
        print_keyboard(m, [x for x in used_modificators if not x & Modificator.SUPER])
        print_keyboard(m, [x for x in used_modificators if x & Modificator.SUPER])
    else:
        print_keyboard(m, used_modificators)
    print(f"]")


print(f"$bye")
