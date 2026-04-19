# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import pytest
from pitnode.core.presenter import PitNodePresenter
from pitnode.core.controller import PitNodeCtrl
from pitnode.app.app import SystemStatus

from dataclasses import dataclass
from typing import List, Optional

@pytest.fixture
def presenter():
    sys_status = SystemStatus()
    presenter = PitNodePresenter(sys_status, )

def test_get_temps():
    pass