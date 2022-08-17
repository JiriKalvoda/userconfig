from i3_workspace_constants import *
VERSION = "0.0.1"

LICENCE_HELP = """
LICENCE
=======

i3-workspace - Two-dimensional workspace manager for i3wm
(c)   2022 Jiri Kalvoda <jirikalvoda@kam.mff.cuni.cz>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

BASE_HELP = f"""
BASE CONCEPT
============
I3 workspace manager is an addition to i3 window manager.
It should manage 2D array of workspaces.

Workspaces are organized into master slave topology.
There is {MAX_MASTER - MIN_MASTER + 1} masters (labeled from {MIN_MASTER} to {MAX_MASTER}).
Each master have {MAX_MASTERED_SLAVE - MIN_SLAVE + 1} slaves (labeled from {MIN_SLAVE} to {MAX_MASTERED_SLAVE}).
Additional there is some workspaces out of this hierarchy (shared across all masters).
Some of then has number 9??, other has special name.

If you change master, last used slave (on this output) for selected master will
be used. If you jump to some workspace out of this hierarchy, last used master
(on this output) is still remembered and will be used for switching to some slave.
"""

TECHNICAL_HELP = """
BASE USAGE:
===========
For using this program, you should first start i3-workspace-daemon, then you can use
i3-workspace script for changing current workspace, moving container ...
You can use i3 configuration file to map keyboard shortcut to execute this script.
It is possible to start daemon with GUI by `--gui` option.
"""

QT_HELP = """
MANAGER HELP
============

You can see scrollable list of all workspaces with screenshots and windows informations.
Screenshot of each workspace is taken when you leave it by `i3-workspace` command
(for example by key press) or by going to other output.
Windows information (I3 container tree) is loaded on each jump to GUI by `i3-workspace gui`
or on key `T` press.

On click on workspace it will be shown.
On click on container/window, it will be focused.

You can search in windows name by tipping search term to`Find input area.
Input should contain at least 3 character ad it will be procesed as regex.
See <https://docs.python.org/3/library/re.html> for supported terms.

There is one active workspace marked with red border. Active workspace is important for most of keyboard shortcuts. Initially it is last used workspace. You can change it by shortcuts (see below).

Shortcuts:
----------
?                - Show this help
/                - Begin of search (start input mode)
n                - focus next workspace with find match
N                - focus previous workspace with find match
<DOWN> / <UP>
or j / k         - Focus next / previous nonempty master
Shift + <DOWN> / <UP>
or J / K - Focus next / previous master
<RIGHT> / <LEFT>
or l / h         - Focus next / previous nonempty slave
Shift + <RIGHT> / <LEFT>
or L / H         - Focus next / previous slave
<ENTER>          - go to focused workspace
<ESC>            - go to previous used workspace
w / e            - advance / reduce screenshot size
`, 1-9, 0, -, =  - focus corresponding slave
F1-F12           - focus corresponding master

Shortcuts in search bar (input mode):
-------------------------------------
<ESC>          - Clear search and exit input mode
<ENTER>        - Exit input mode
<DOWN> / <UP>  - Focus next / previous search match workspace
And standard shortcuts with extra CTRL

GUI meaning:
------------

Red cross on the screenshot is shown when screenshot is old, for example
when workspace was leaven without capture or is come container was moved no this workspace.

Background color of the workspace name denote output of this workspace.

Text color of workspace name is green if workspace is currently visible (on other output).
Red is on current slave for some master and blue is on slave for master on any output.
"""
