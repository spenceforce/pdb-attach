# -*- mode: python -*-
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
import pdb_attach  # pylint: disable=wrong-import-position

pdb_attach.listen(sys.argv[1])

printable_value = "original value\n"
keep_running = True

while keep_running: pass

with open("./test/out.txt", "w") as f:
    f.write(printable_value)
