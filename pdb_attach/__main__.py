# -*- mode: python -*-
"""Pdb-attach client that can be run as a module."""
import argparse

from pdb_attach.pdb_signal import PdbSignaler

if "__main__" == __name__:
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

    client = PdbSignaler(args.pid, args.port)
    client.connect()
    lines, closed = client.recv()
    while closed is False:
        try:
            try:
                to_server = raw_input(lines)  # type: ignore
            except NameError:
                # Ignore flake8 warning about input in Python 2.7 since we are checking for raw_input first.
                to_server = input(lines)  # noqa:S322

            lines, closed = client.send_and_recv(to_server)
        except EOFError:
            lines, closed = client.raise_eoferror()

    if len(lines) > 0:
        print(lines)
