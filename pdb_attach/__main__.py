# -*- mode: python -*-
import argparse
import os
import signal
import socket
import sys

from .pdb_attach import PDB_PROMPT

if __name__ == "__main__":
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
    client_io = client.makefile("rw", buffering=1)

    first_command = True
    while True:
        lines = []
        while True:
            line = client_io.readline(len(PDB_PROMPT))
            if line == PDB_PROMPT:
                break

            if line == "":
                # The other side has closed the connection, so we can exit.
                print("Connection closed.")
                sys.exit(0)

        if first_command is not True:
            to_server = input("".join(lines))
            if to_server[-1] != "\n":
                to_server += "\n"

            client_io.write(to_server)
        else:
            # For some reason the debugger starts in the __repr__ method of the
            # socket, so counteract this by jumping up a frame.
            client_io.write("u\n")
            first_command = False
