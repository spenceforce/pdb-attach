# pdb-attach #

A python debugger that can attach to running processes.

This package was made in response to frustration over debugging long running processes. Wouldn't it be nice to just attach pdb to a running python program and see what's going on? Well that's exactly what pdb-attach does.

## Installation ##

```bash
$ pip install pdb-attach
```

## Usage ##

`pdb_attach` must be imported and set up in the python program of interest in order for a user to attach to the running program.

```python
import pdb_attach
pdb_attach.listen(50000)  # Listen on port 50000.

def do_stuff():
    ...

if __name__ == '__main__:
    do_stuff()
```

When the program is running, attach to it by calling `pdb_attach` from the command line with the PID of the program to inspect.

```bash
$ python -m pdb_attach <PID> 50000
(Pdb)  # Interact with pdb as you normally would
```

When done, entering `detach` at the pdb prompt will detach pdb and the program will continue running from that point.

```bash
(Pdb) detach
$  # Back at the command line and the original process is still running!
```

<!-- `pdb_attach` uses a signal handler to start pdb on the running process and sockets to communicate with the user. By default, `pdb_attach` uses `SIGUSR2` for the signal handler and a random port for the sockets, but these can be changed by the user. -->
