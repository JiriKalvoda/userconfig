from main import *

@action_init()
def AND(self, *arg, main=0):
    self.data = arg
    self.main = main

@action_init()
def CMD(self, cmd):
    self.cmd = cmd

@action_init()
def GO_MODE(self, mode):
    print(mode, file=sys.stderr)
    if isinstance(mode, str):
        mode = mode_by_name(mode)
    self.mode = mode

@action_init()
def CONFIRM_CMD(self, cmd, text=None):
    self.cmd = cmd
    self.text = text

@action_implement("CONFIRM_CMD")
def f(self):
    return CMD(self.cmd)

@action_init()
def ACTION_ABSTRACT_WM_COMMAND(self):
    pass
@action_init()
def FOCUS_CONT(self, argument):
    assert_in(argument, dirs + ["floating", "parent", "child"])
    self.argument = argument
@action_init()
def MOVE_CONT(self, argument):
    assert_in(argument, dirs)
    self.argument = argument
@action_init()
def MOVE_WORKSPACE(self, argument):
    self.argument = argument
@action_init()
def SPLIT_CONT(self, argument):
    assert_in(argument, ["stacking", "tabbed", "splith", "splitv"])
    self.argument = argument
@action_init()
def LAYOUT_CONT(self, argument):
    assert_in(argument, ["stacking", "tabbed", "splith", "splitv", "toggle split"])
    self.argument = argument

@action_init()
def ACTION_ABSTRACT_WORKSPACE(self, workspace=None, master=None, slave=None, notify=False):
    self.workspace = workspace
    self.master = master
    self.slave = slave
    self.notify = notify

action_init("GOTO_WORKSPACE", ACTION_ABSTRACT_WORKSPACE)()
action_init("CONT_WORKSPACE", ACTION_ABSTRACT_WORKSPACE)()
action_init("CONT_AND_GOTO_WORKSPACE", ACTION_ABSTRACT_WORKSPACE)()
action_init("SWAP_WORKSPACE", ACTION_ABSTRACT_WORKSPACE)()
action_init("SWAP_MASTER_WORKSPACE", ACTION_ABSTRACT_WORKSPACE)()
action_init("WORKSPACE_GUI")()

@action_init()
def RESIZE_CONT(self, direction, size=12):
    self.direction = direction
    self.size = size

@action_init()
def CONT_TOGGLE(self, prop_name):
    assert_in(prop_name, ["fullscreen", "floating", "sticky"])
    self.prop_name = prop_name

@action_init()
def RESTART_MANAGER(self, prop_name):
    assert_in(prop_name, ["fullscreen", "floating", "sticky"])
    self.prop_name = prop_name

@action_init()
def RESTART_MANAGER(self, variant=None):
    self.variant = variant

action_init("EXIT_PROG")()
action_init("EXIT_SHUTDOWN")()
action_init("EXIT_SUSPEND")()
action_init("EXIT_RESTART")()
action_init("EXIT_LOCK")()

@action_implement("EXIT_SHUTDOWN")
def f(self):
    return CONFIRM_CMD("poweroff", "Do you really want to SHUTDOWN?")
@action_implement("EXIT_SUSPEND")
def f(self):
    return CMD("suspender")
@action_implement("EXIT_RESTART")
def f(self):
    return CONFIRM_CMD("reboot", "Do you really want to REBOOT?")
@action_implement("EXIT_PROG")
def f(self):
    return CONFIRM_CMD("i3-msg exit", "Do you really want to EXIT i3?")
@action_implement("EXIT_LOCK")
def f(self):
    return CMD("xtrlock")

@action_init()
def LIGHT(self, raw=None, val=None, change=None):
    self.raw = raw
    self.val = val
    self.change = change
@action_implement("LIGHT")
def f(self):
    if self.raw is not None:
        return CMD(f"light H {self.raw}; lightGUI")
    if self.val is not None:
        return CMD(f"light = {self.val}; lightGUI")
    if self.change is not None:
        if self.change >= 0:
            return CMD(f"light + {self.change}; lightGUI")
        else:
            return CMD(f"light - {-self.change}; lightGUI")
@action_init()
def MONITOR_POWER(self, val):
    self.val = val
@action_implement("MONITOR_POWER")
def f(self):
    return CMD(f"echo {self.val} > /run/monitor_power")

@action_init()
def VOLUME(self, val=None, change=None):
    self.val = val
    self.change = change
@action_implement("VOLUME")
def f(self):
    if self.val is not None:
        return CMD(f"amixer sset Master -q {self.val*100}%; sleep 0.05; volumeGUI")
    if self.change is not None:
        if self.change >= 0:
            return CMD(f"amixer sset Master -q {+self.change*100}%+; sleep 0.05; volumeGUI")
        else:
            return CMD(f"amixer sset Master -q {-self.change*100}%-; sleep 0.05; volumeGUI")
