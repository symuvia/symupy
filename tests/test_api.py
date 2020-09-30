"""
    Unit tests for symupy.api.connector 
"""
# ============================================================================
# STANDARD  IMPORTS
# ============================================================================

import os
import unittest
import platform
import pytest

# ============================================================================
# INTERNAL IMPORTS
# ============================================================================

from symupy.api import Simulation, Simulator
from symupy.utils.constants import DCT_DEFAULT_PATHS

# ============================================================================
# TESTS AND DEFINITIONS
# ============================================================================


@pytest.fixture
def symuvia_library_path():
    return DCT_DEFAULT_PATHS[("symuvia", platform.system())]


def test_load_symuvia_via_api(symuvia_library_path):
    sim_instance = Simulator(symuvia_library_path)
    sim_instance.load_symuvia()
    assert sim_instance.libraryPath == symuvia_library_path
