import os, sys

port = int(sys.argv[1])

import pdb_attach

pdb_attach.listen(port)

running = True

while running: pass

sys.stdout.write("done" + os.linesep)
sys.stdout.flush()
