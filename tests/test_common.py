import sys
from contextlib import suppress
from glob import glob
from pathlib import Path
from subprocess import CalledProcessError

import pytest
from pyscaffold import file_system as fs
from pyscaffold import shell
from pyscaffold.identification import underscore

from pyscaffoldext.django.extension import Django

from .helpers import PYTHON, run, uniqstr

FLAG = Django().flag
PUTUP = shell.get_executable("putup")
PIP = shell.get_executable("pip")


def is_venv():
    """Check if the tests are running inside a venv"""
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


@pytest.fixture(autouse=True)
def cwd(tmpfolder):
    """Guarantee a blank folder as workspace"""
    yield tmpfolder


def chdir(path):
    return fs.chdir(fs.create_directory(path))


def test_ensure_inside_test_venv():
    # This is a METATEST
    # Here we ensure `putup` is installed inside tox or
    # a local virtualenv (pytest-runner), so we know we are testing the correct
    # version of pyscaffold and not one the devs installed to use in other
    # projects
    assert PUTUP
    assert PIP
    assert ".tox" in PUTUP or is_venv()
    assert Path(PUTUP).parent == Path(PIP).parent


def test_django_generates_files(tmpfolder):
    # Given pyscaffold is installed,
    # when we call putup with extensions
    name = "myproj"
    run(PUTUP, "--no-config", FLAG, name)
    # --no-config: avoid extra config from dev's machine interference
    with chdir(tmpfolder / name):
        # then special files should be created
        assert Path("manage.py").exists()
        assert Path("src/myproj/__main__.py").exists()
        assert not Path("myproj").exists()


TASKS = [
    "test",
    "clearsessions",
    "showmigrations",
    "createsuperuser --username admin --email admin@localhost --no-input",
]


def remove_eventual_package(name):
    with suppress(Exception, CalledProcessError):
        run(f"{PIP} uninstall --yes {name}")


@pytest.mark.slow
@pytest.mark.system
@pytest.mark.parametrize(
    "name,command",
    [
        ("pkg" + uniqstr(), f"{PYTHON} manage.py"),
        (lambda x: (x, f"{PYTHON} -m " + underscore(x)))("pkg" + uniqstr()),
    ],
)
def test_manage_py_runs_nicely(tmpfolder, name, command):
    # Given we have a project generated with putup --django pkg
    try:
        remove_eventual_package(name)
        run(PUTUP, "--no-config", FLAG, name)
        with chdir(tmpfolder / name):
            print(list(glob("*")))
            print(list(Path("src").glob("*/*")))
            print(Path("manage.py").read_text())
            run(f"{PIP} install -Ie .")  # required for `python -m`

            # when we call manage.py or python -m djangotest
            run(f"{command} migrate")
            # then it should create a sqlite3 file in the right place
            assert Path("db.sqlite3").exists()
            assert not Path("src/db.sqlite3").exists()
            # and everything should be fine
            for task in TASKS:
                run(f"{command} {task}")
    finally:
        remove_eventual_package(name)
