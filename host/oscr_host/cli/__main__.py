# SPDX-License-Identifier: GPL-3.0-or-later
"""python -m oscr_host.cli"""
import sys

from .app import main

sys.exit(main())
