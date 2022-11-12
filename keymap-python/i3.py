#!/usr/bin/python3
from main import *

def cmd_expand(cmd):
    s = cmd.replace('"', '\\\\"')
    return f'"{s}"'

def i3_woman_serialize(cmd, args):
    r = f"i3-woman {cmd}"
    if args.workspace is not None:
        r += f" --workspace {args.workspace}"
    if args.master is not None:
        r += f" --master {args.master}"
    if args.slave is not None:
        r += f" --slave {args.slave}"
    if args.notify:
        r += f" --notify"
    return "exec " + cmd_expand(r)

@action_serialize("GOTO_WORKSPACE")
def f(self):
    return i3_woman_serialize("goto-workspace", self)
@action_serialize("CONT_WORKSPACE")
def f(self):
    return i3_woman_serialize("container-to", self)
@action_serialize("CONT_AND_GOTO_WORKSPACE")
def f(self):
    return i3_woman_serialize("goto-with-container-to", self)
@action_serialize("SWAP_WORKSPACE")
def f(self):
    return i3_woman_serialize("swap-with-workspace", self)
@action_serialize("SWAP_MASTER_WORKSPACE")
def f(self):
    return i3_woman_serialize("swap-master-with", self)
@action_serialize("WORKSPACE_GUI")
def f(self):
    return "exec " + cmd_expand("i3-woman gui")
@action_serialize("AND")
def f(self):
    return "; ".join(x.serialize() for x in self.data)
@action_serialize("CMD")
def x(self):
    return "exec " + cmd_expand(self.cmd)
@action_serialize("CONFIRM_CMD")
def x(self):
    return "exec " + cmd_expand(f"i3-nagbar -t warning -m '{self.text}' -b 'Yes' '{self.cmd}'")
    # TODO ' expansion
@action_serialize("FOCUS_CONT")
def x(self):
    return f"focus {self.argument}"
@action_serialize("MOVE_CONT")
def x(self):
    return f"move {self.argument}"
@action_serialize("MOVE_WORKSPACE")
def x(self):
    return f"move workspace to output {self.argument}"
@action_serialize("SPLIT_CONT")
def x(self):
    return {
        "splitv": f"split v",
        "splith": f"split v",
        "tabbed": f"split v; layout tabbed",
        "stacking": f"split v; layout stacking",
    }[self.argument]
@action_serialize("RESIZE_CONT")
def x(self):
    return "resize " + {
        "up": f"shrink height",
        "down": f"grow height",
        "left": f"shrink width",
        "right": f"grow width",
    }[self.direction] + f" {self.size} px or {self.size} ppt"
@action_serialize("CONT_TOGGLE")
def x(self):
    return f"{self.prop_name} toggle"
@action_serialize("GO_MODE")
def x(self):
    return f'mode "{self.mode.name or "default"}"; exec '+cmd_expand(f"i3-mode-log '{self.mode.name or 'default'}'")
@action_serialize("LAYOUT_CONT")
def x(self):
    return f"layout {self.argument}"
@action_serialize("RESTART_MANAGER")
def f(self):
    if self.variant == "v2":
        return "restart"
    else:
        return "exec "+cmd_expand(f"cd ~/.config/i3/; terminal -e bash -c './config-gen > config-tmp && mv config-tmp config && i3-msg restart || read'")
@action_implement("EXIT_PROG")
def f(self):
    return g["CONFIRM_CMD"]("i3-msg exit", "Do you really want to EXIT i3?")


load_main()


def print_key(key):
    import i3_codes
    k_id = i3_codes.query(key.row, key.col)
    if k_id is None: raise KeyMapException("Undefined key {key.row} {key.col} for I3 output")
    r = f"{k_id}"
    if key.mod & Modificator.SHIFT: r = "shift+" + r
    if key.mod & Modificator.CTRL: r = "ctrl+" + r
    if key.mod & Modificator.SUPER: r = "Mod4+" + r
    if key.mod & Modificator.ALT: r = "Mod1+" + r
    return r

for m in all_modes:
    def print_mode(tabs):
        for i in m.table:
            if isinstance(i.key, Key):
                if i.press_action is not None:
                    print(tabs+f"bindcode {print_key(i.key)} {i.press_action.serialize()}")
                if i.release_action is not None:
                    print(tabs+f"bindcode {print_key(i.key)} --release {i.release_action.serialize()}")
            if isinstance(i.key, I3DirectMapper):
                print(tabs+f"{i.action}")
            if isinstance(i.key, ExecOnStartupMapper):
                print(tabs+f"exec{'_always' if i.key.always else ''} {cmd_expand(i.action)}")

    if m.name=="":
        print_mode("")
    else:
        print(f'mode "{m.name}" {{')
        print_mode("    ")
        print(f"}}")

