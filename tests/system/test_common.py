# -*- coding: utf-8 -*-
import sys
from os.path import exists

import pytest

from .helpers import run, run_common_tasks

pytestmark = [pytest.mark.slow, pytest.mark.system]


def is_venv():
    """Check if the tests are running inside a venv"""
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


@pytest.fixture(autouse=True)
def cwd(tmpdir):
    """Guarantee a blank folder as workspace"""
    with tmpdir.as_cwd():
        yield tmpdir


def test_ensure_inside_test_venv():
    # This is a METATEST
    # Here we ensure `putup` is installed inside tox or
    # a local virtualenv (pytest-runner), so we know we are testing the correct
    # version of pyscaffold and not one the devs installed to use in other
    # projects
    assert ".tox" in run("which putup") or is_venv()


def test_django_generates_files(cwd):
    # Given pyscaffold is installed,
    # when we call putup with extensions
    name = "myproj"
    run("putup", "--django", name)
    with cwd.join(name).as_cwd():
        # then special files should be created
        assert exists("manage.py")
        # and all the common tasks should run properly
        run_common_tasks(flake8=False)
