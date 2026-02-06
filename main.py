# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import asyncio
from pitnode.ui.port import start_ui

if __name__ == "__main__":
    asyncio.run(start_ui())
