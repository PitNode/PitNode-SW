# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

"""
User configuration file for PitNode
"""

# Unit for temperature "deg" or "far"
UNIT = "deg"

T_NTC_0_MK = [298150, 298150, 298150] # in mK
BETA_K = [3977, 3977, 3977] # in K
R_NTC_0_OHM = [100000, 100000, 100000] # in Ohm

ENABLE_WIFI = True
SERVER_START_TIMEOUT = 3

# Flag is only for development
DEV_MODE = True