# -*- coding: utf-8 -*-
"""Setup file"""
import io
import os
import re
import sys
from setuptools import setup


VER_RE = "__version__ = [\"'](?P<Version>(?:(?![\"']).)*)"

here = os.path.abspath(os.path.dirname(__file__))

with io.open(os.path.join(os.getcwd(), "pdb_attach.py"), "r", encoding="utf-8") as f:
    init_file = f.read()
    match = re.search(VER_RE, init_file)
    if match is not None:
        version = match.group("Version")
    else:
        # Cannot find version. Bail.
        sys.exit(1)

with io.open(os.path.join(here, "README.md"), "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="pdb-attach",
    # uses semantic versioning scheme
    version=version,
    description="A python debugger that can attach to running processes.",
    long_description=long_description,
    url="https://github.com/smitchell556/pdb-attach",
    author="Spencer Mitchell",
    author_email="smitchell556@gmail.com",
    license="BSD 3-Clause",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="pdb debug debugger process",
    py_modules=["pdb_attach"],
    include_package_data=True,
    extras_require={"dev": ["black", "mypy", "pylint", "pytest"]},
)
