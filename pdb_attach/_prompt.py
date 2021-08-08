# -*- mode: python -*-
"""The Pdb prompt.

This module's sole purpose is to determine the Pdb prompt. It's highly unlikely the
prompt will change, but it's better to get the prompt straight from the source than to
assume it won't change between versions.
"""
import pdb

__all__ = ["PROMPT"]

_pdb = pdb.Pdb()
PROMPT = _pdb.prompt
del _pdb
