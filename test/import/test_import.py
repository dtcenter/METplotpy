#!/usr/bin/env python3

import pytest

# used in METplus use case: model_applications/medium_range/UserScript_fcstGEFS_Difficulty_Index
def test_import_difficulty_index():
    try:
        import metplotpy.plots.difficulty_index.mycolormaps
        from metplotpy.plots.difficulty_index.plot_difficulty_index import plot_field
    except:
        assert False
    assert True

# used in METplus use case: model_applications/s2s/UserScript_obsPrecip_obsOnly_Hovmoeller
def test_import_hovmoeller():
    try:
        import metplotpy.plots.hovmoeller.hovmoeller
    except:
        assert False
    assert True

def test_import_all():
    try:
        import metplotpy
    except:
        assert False
    assert True
