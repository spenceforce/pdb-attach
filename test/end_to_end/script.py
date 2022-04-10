from __future__ import print_function
import sys

port = int(sys.argv[1])

import pdb_attach

pdb_attach.listen(port)

running = True

while running: pass

print("done", flush=True)
