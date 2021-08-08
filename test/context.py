"""Pdb-attach context.

For tests, import ``pdb_attach`` and other related modules from this module instead of
directly. This ensures ``pdb_attach`` is on the path.
"""
import os
import platform
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
import pdb_attach
import pdb_attach.client as pdb_client
import pdb_attach.pdb_detach as pdb_detach
from pdb_attach._prompt import PROMPT
