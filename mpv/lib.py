from pathlib import Path
import os

POINTERS_DIR = Path(Path.home(), ".mp/pointers")

IDENTIFICATORS = {
        's': 'sound',
        'f': 'film',
}

try:
   os.makedirs(POINTERS_DIR)
except FileExistsError:
   pass
