import i3_workspace_util as util

GUI_WORKSPACE = (-1, -1)
GUI_WORKSPACE_STR = "0"

MAX_MASTERED_SLAVE = 8
MAX_SLAVE = 14
MAX_MASTER = 12
MIN_SLAVE = 0
MIN_MASTER = 1
MASTERED_SLAVE_LIST = list(range(1, MAX_MASTERED_SLAVE+1)) + [0]

WORKSPACES_RENAMES = {913: "MAIL", 914: "ZOOM"}
REV_RENAMES = {v: k for (k, v) in WORKSPACES_RENAMES.items()}
WORKSPACES_KEY = {911: "-", 912: "=", 913: "M", 914: "Z"}
ORD_TO_WORKSPACE = {util.iford(v): k for k, v in WORKSPACES_KEY.items()}


@list
@util.run()
def WORKSPACES():
    for i in range(MIN_MASTER, MAX_MASTER + 1):
        for j in range(MIN_SLAVE, MAX_MASTERED_SLAVE + 1):
            yield (i, j)
    for j in range(MAX_MASTERED_SLAVE + 1, MAX_SLAVE + 1):
        yield (None, j)


WORKSPACES_REV = {x: i for (i, x) in enumerate(WORKSPACES)}

GUI_MASTERS = [None] + list(range(MIN_MASTER, MAX_MASTER+1))
GUI_WORKSPACES_ORDER = [i for i in WORKSPACES if i[0] is None] + [i for i in WORKSPACES if i[0] is not None]


GUI_WORKSPACES_ORDER_REV = {x: i for (i, x) in enumerate(GUI_WORKSPACES_ORDER)}
