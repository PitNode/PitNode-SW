# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

"""
User configuration file for PitNode
"""

# Unit for temperature "cel" or "far"
UNIT = "cel"

# Probe parameters
T_NTC_0_MK = [298150, 298150, 298150] # in mK
BETA_K = [3977, 3977, 3977] # in K
R_NTC_0_OHM = [100000, 100000, 100000] # in Ohm

# Probe to ADC channel assignment
PROBES = ["NTC", "NTC", "NTC"]

ENABLE_WIFI = True

# Flag is only for development
DEV_MODE = True

WEB_PORT = 80
WEB_PORT_DEV = 8080