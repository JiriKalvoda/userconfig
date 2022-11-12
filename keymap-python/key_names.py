table = [
    ["ESC"] + [f"F{i+1}" for i in range(12)],
    list("`1234567890-=") + ["Backspace"],
    ["Tab"] + list("QWERTYUIOP[]") + ["Enter"],
    ["CapsLk"] + list("ASDFGHJKL;'") + ["BackSlash"],
    ["ShiftL", "Not"] + list("ZXCVBNM,./") + ["ShiftR"],
    ["CtrlL", "SuperL", "Alt", "Space", "AltGr", "SuperR", "CtrlR"],
    ["PrtSc", "ScrLock", "Pause"],
    ["Insert", "Home", "PgUp"],
    ["Delete", "End", "PgDown"],
    ["Up"],
    ["Left", "Down", "Right"],
    ["NumLock", "N/", "N*", "N-"],
    ["N7", "N8", "N9", "+"],
    ["N4", "N5", "N6"],
    ["N1", "N2", "N3", "NEnter"],
    ["N0", "N."],
]


reverse = {y:(i, j) for (i, x) in enumerate(table) for (j, y) in enumerate(x) }
