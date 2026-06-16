"""Compatibility shim for tooling that still invokes ``setup.py``.

All project metadata lives in ``pyproject.toml``; this file simply delegates
to setuptools so legacy build commands continue to work.
"""

from setuptools import setup

if __name__ == "__main__":
    setup()
