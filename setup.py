import os

import setuptools

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "pdb_attach", "VERSION.txt")) as f:
    version = f.read().strip()
    if len(version) < 5:
        # Cannot find version. Bail.
        sys.exit(1)


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pdb-attach",
    version=version,
    author="Spencer Mitchell",
    author_email="smitchell556@gmail.com",
    description="A python debugger that can attach to running processes.",
    license="BSD 3-Clause",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="pdb debug debugger process",
    url="https://github.com/smitchell556/pdb-attach",
    project_urls={
        "Documentation": "https://github.com/smitchell556/pdb-attach",
        "Source": "https://github.com/smitchell556/pdb-attach",
        "Bug Tracker": "https://github.com/smitchell556/pdb-attach/issues",
    },
    packages=setuptools.find_packages(include=["pdb_attach", "pdb_attach.*"]),
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, <4",
    package_data={"pdb_attach": ["py.typed", "*.pyi", "VERSION.txt"]},
)
