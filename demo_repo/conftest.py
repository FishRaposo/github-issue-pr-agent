"""Ensure ``calculator`` is importable when the agent runs pytest here.

The agent invokes ``python -m pytest .`` with ``cwd`` set to this directory, so
inserting the directory onto ``sys.path`` lets ``from calculator import ...``
resolve regardless of the rootdir pytest picks.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
