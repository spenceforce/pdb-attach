# -*- mode: python -*-
"""pdb-attach end to end tests."""
from __future__ import unicode_literals

import os
import subprocess
import time

try:
    from test.support.socket_helper import find_unused_port
except ImportError:
    from test.support import find_unused_port

from skip import skip_windows


pdb_path = os.path.abspath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir)
)


def run_script(script_input):
    """Run pdb-attach from the command line.

    Parameters
    ----------
    script_input
        Which input file to use with the script.

    Returns
    -------
    [str] : Lines of actual output.
    bool : True if the script finished executing.
    """
    input_file = "test/end_to_end/input/{}.txt".format(script_input)

    port = find_unused_port()
    env = os.environ.copy()

    if len(env.get("PYTHONPATH", "")) == 0:
        env["PYTHONPATH"] = pdb_path
    else:
        env["PYTHONPATH"] += os.pathsep + pdb_path

    script = subprocess.Popen(
        ["python", "test/end_to_end/script.py", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    time.sleep(1)  # Give the script time to set up the server.

    with open(input_file) as f:
        client = subprocess.Popen(
            ["python", "-m" "pdb_attach", str(script.pid), str(port)],
            stdin=f,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        out, err = client.communicate()

    output = out.decode().split(os.linesep)

    assert len(err) == 0

    out, err = script.communicate()
    assert len(err) == 0

    return output, out.decode() == "done" + os.linesep


expected_detach = os.linesep.join(
    [
        "> /path/to/pdb-attach/test/end_to_end/script.py(11)<module>()",
        "-> while running: pass",
        "(Pdb)   6  	",
        "  7  	pdb_attach.listen(port)",
        "  8  	",
        "  9  	running = True",
        " 10  	",
        " 11  ->	while running: pass",
        " 12  	",
        ' 13  	sys.stdout.write("done" + os.linesep)',
        " 14  	sys.stdout.flush()",
        "[EOF]",
        "(Pdb) (Pdb) ",
    ]
).replace("/path/to/pdb-attach", pdb_path)


@skip_windows
def test_end_to_end_detach():
    """Test the `detach` command."""
    actual_lines, done = run_script("detach")

    for expected, actual in zip(expected_detach.split(os.linesep), actual_lines):
        assert expected == actual

    assert done is True


expected_empty = os.linesep.join(
    [
        "> /path/to/pdb-attach/test/end_to_end/script.py(11)<module>()",
        "-> while running: pass",
        "(Pdb) (Pdb) (Pdb) ",
    ]
).replace("/path/to/pdb-attach", pdb_path)


@skip_windows
def test_end_to_end_empty():
    """Test an empty line."""
    actual_lines, done = run_script("empty")

    for expected, actual in zip(expected_empty.split(os.linesep), actual_lines):
        assert expected == actual

    assert done is True
