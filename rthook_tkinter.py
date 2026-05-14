# Runtime hook: fix TCL_LIBRARY / TK_LIBRARY paths inside a frozen PyInstaller bundle.
import os
import sys

if getattr(sys, "frozen", False):
    base = sys._MEIPASS
    tk_data = os.path.join(base, "_tk_data")
    if os.path.isdir(tk_data):
        for name in os.listdir(tk_data):
            path = os.path.join(tk_data, name)
            if not os.path.isdir(path):
                continue
            lower = name.lower()
            if lower.startswith("tcl"):
                os.environ["TCL_LIBRARY"] = path
            elif lower.startswith("tk"):
                os.environ["TK_LIBRARY"] = path
