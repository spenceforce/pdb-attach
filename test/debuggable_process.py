# -*- mode: python -*-
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
import pdb_attach  # pylint: disable=wrong-import-position

pdb_attach.listen()

printable_value = "original value"
keep_running = True

while keep_running: pass

with open("out.txt", "w") as f: f.write(printable_value)
