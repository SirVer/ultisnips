"""Pytest conftest that mocks the vim module.

UltiSnips code is normally imported inside Vim's embedded Python, where the
`vim` module is provided by Vim itself. For unit tests that exercise
pure-Python logic (diff, position, ...) we install a lightweight mock so that
the import chain succeeds.

This file lives at pythonx/ (one level above the UltiSnips package) so that
the mock is installed before Python processes UltiSnips/__init__.py.
"""

import sys
from unittest.mock import MagicMock

sys.modules["vim"] = MagicMock()
