#/usr/bin/env bash

rm -f test/out.txt
touch test/out.txt

python test/debuggable_process.py $1 &
PID=$!

python -m pdb_attach $PID $1 < test/in.txt

diff test/out.txt test/expected.txt

if [ $? -ne 0 ]; then
    exit 1
fi
