# pdb-attach #

![Test](https://github.com/smitchell556/pdb-attach/workflows/Test/badge.svg)

A python debugger that can attach to running processes.

> :exclamation: pdb-attach does not work on processes where it hasn't been imported and set up. If you just discovered this package and hope to use it on an already running process, you will need to restart the program with pdb-attach listening. Another option is to use `gdb` which can attach to a running python process, more information can be found [here](https://wiki.python.org/moin/DebuggingWithGdb). The catch with using `gdb` is that it doesn't step through the python source code, but instead steps through the C code running the python program. Your mileage may vary with `gdb`.

This package was made in response to frustration over debugging long running processes. Wouldn't it be nice to just attach pdb to a running python program and see what's going on? Well that's exactly what pdb-attach does.

## Installation ##

```bash
$ pip install pdb-attach
```

## Requirements ##

### OS ###

Supports OSes that implement POSIX only.

Unfortunately pdb-attach doesn't work on Windows. It's an artifact of the implementation using signals to prompt the remote debugger to accept a socket connection. I would like to support Windows in the future, but because of how Windows handles signals, it will require a different implementation that doesn't rely on signals.

> :warning: On Windows, pdb-attach is still importable, but `listen` won't do anything. Instead a warning will be raised on import and when `listen` is called.

### Python versions ###

Currently supports:

- 2.7
- 3.3
- 3.4
- 3.5
- 3.6
- 3.7
- 3.8
- 3.9

The policy on python version support is to support all active versions of python. For any version that has reached end of life, that version will continue to be supported for the last major release of pdb-attach it was a part of. New major releases of pdb-attach after a python version has been end of lifed may drop support for that version of python.

## Usage ##

> :warning: pdb-attach uses sockets to communicate with the running process where `pdb` is actually being executed. There is always the possibility that a bad actor that has access to your machine can connect to that port before you do. Since `pdb` is an interactive session with the process, this would give them the ability to inspect the source code of the running process, modify state of the running process, and **_run python code as you!_** That is bad and now you've been warned.
>
> Having said that, there are a few planned features that can mitigate this problem.
> 1. Using a secret key known to the running process and the user so that only messages signed with that key will be executed.
> 1. Modifying `pdb` such that it can only inspect the state of the program and execute the program as-is. Granted a bad actor could still read the source code and the state of the program, but they would not be able to change the state of the program or run arbitrary python code.

`pdb_attach` must be imported and set up in the python program of interest in order for a user to attach to the running program.

```python
import pdb_attach
pdb_attach.listen(50000)  # Listen on port 50000.

def do_stuff():
    ...

if __name__ == '__main__:
    do_stuff()
```

When the program is running, attach to it by calling `pdb_attach` from the command line with the PID of the program to inspect and the port passed to `pdb_attach.listen()`.

```bash
$ python -m pdb_attach <PID> 50000
(Pdb)  # Interact with pdb as you normally would
```

When done, entering `detach` at the pdb prompt will detach pdb and the program will continue running from that point.

```bash
(Pdb) detach
$  # Back at the command line and the original process is still running!
```
