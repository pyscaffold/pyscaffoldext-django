# -*- coding: utf-8 -*-
import sys
from contextlib import suppress
from os.path import exists
from subprocess import CalledProcessError

import pytest

from pyscaffoldext.django.extension import Django

from .helpers import run, run_common_tasks, uniqstr

pytestmark = [pytest.mark.slow, pytest.mark.system]

# TODO: Remove workaround for PyScaffold <= 4.x, see comments on class
FLAG = (lambda ext: getattr(ext, "xflag", ext.flag))(Django("django"))


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
    run("putup", FLAG, name)
    with cwd.join(name).as_cwd():
        # then special files should be created
        assert exists("manage.py")
        assert exists("src/myproj/__main__.py")
        assert not exists("myproj")
        # and all the common tasks should run properly
        run_common_tasks(flake8=False)


TASKS = [
    "test",
    "clearsessions",
    "showmigrations",
    "createsuperuser --username admin --email admin@localhost --no-input",
]


def remove_eventual_package(name):
    with suppress(Exception, CalledProcessError):
        run("pip uninstall --yes {}".format(name))


@pytest.mark.parametrize(
    "name,command",
    [
        ("pkg" + uniqstr(), "python manage.py"),
        (lambda x: (x, "python -m " + x))("pkg" + uniqstr()),
    ],
)
def test_manage_py_runs_nicely(cwd, name, command):
    # Given we have a project generated with putup --django pkg
    try:
        remove_eventual_package(name)
        run("putup", FLAG, name)
        with cwd.join(name).as_cwd():
            run("ls -la")
            run("cat manage.py")
            run("ls -la src/{}".format(name))
            run("pip install -Ie .")  # required for `python -m`

            # when we call manage.py or python -m djangotest
            run("{} migrate".format(command))
            # then it should create a sqlite3 file in the right place
            assert exists("db.sqlite3")
            assert not exists("src/db.sqlite3")
            # and everything should be fine
            for task in TASKS:
                run("{} {}".format(command, task))
    finally:
        remove_eventual_package(name)
