#!/usr/bin/env python3

import pytest

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
