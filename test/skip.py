# -*- mode: python -*-
"""General pytest decorators for skipping tests."""
import platform

import pytest


is_windows = False
if platform.system() == "Windows":
    is_windows = True


skip_windows = pytest.mark.skipif(is_windows, reason="Lacks Windows support.")
