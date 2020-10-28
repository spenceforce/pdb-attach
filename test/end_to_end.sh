#/usr/bin/env bash

touch out.txt

python debuggable_process.py &
PID=$!

python -m pdb_attach $PID < in.txt > out.txt

diff out.txt expected.txt

if [ $? -ne 0 ]; then
    return 1
fi

return 0
