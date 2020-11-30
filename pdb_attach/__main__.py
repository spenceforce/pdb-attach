# -*- mode: python -*-
"""Pdb-attach client that can be run as a module."""
import argparse
import os
import signal
import socket
import sys

PDB_PROMPT = "(Pdb) "

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "pid", type=int, metavar="PID", help="The pid of the process to debug."
)
parser.add_argument(
    "port",
    type=int,
    metavar="PORT",
    help="The port to connect to the running process.",
)
args = parser.parse_args()

os.kill(args.pid, signal.SIGUSR2)
client = socket.create_connection(("localhost", args.port))
try:
    client_io = client.makefile("rw", buffering=1)
except TypeError:
    # Unexpected keyword argument. Try bufsize.
    client_io = client.makefile("rw", bufsize=1)  # type: ignore  # Python 2.7 compatibility.

while True:
    lines = []
    while True:
        line = client_io.readline(len(PDB_PROMPT))
        lines.append(line)
        if line == PDB_PROMPT:
            break

        if line == "":
            # The other side has closed the connection, so we can exit.
            print("Connection closed.")
            sys.exit(0)

    prompt = "".join(lines)
    try:
        to_server = raw_input(lines)  # type: ignore  # Python 2.7 compatibility.
    except NameError:
        # Ignore flake8 warning about input in Python 2.7 since we are checking for raw_input first.
        to_server = input("".join(lines))  # noqa: S322

    if to_server[-1] != "\n":
        to_server += "\n"

    client_io.write(to_server)
