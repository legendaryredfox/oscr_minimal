#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Atalho: python host/dumper.py detect|dump|save-read|save-write ..."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from oscr_host.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
