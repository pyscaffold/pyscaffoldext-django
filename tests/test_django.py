import logging
import os
import re
from pathlib import Path

import pytest
from pyscaffold import __version__ as pyscaffold_version
from pyscaffold.api import NO_CONFIG, create_project
from pyscaffold.cli import parse_args, run
from pyscaffold.templates import get_template

from pyscaffoldext.django.extension import Django, DjangoAdminNotInstalled

PROJ_NAME = "proj"
DJANGO_FILES = ["proj/manage.py", "proj/src/proj/wsgi.py", "proj/src/proj/__main__.py"]

FLAG = Django().flag


@pytest.mark.slow
def test_create_project_with_django(tmpfolder):
    # Given options with the django extension,
    opts = dict(
        project_path=PROJ_NAME,
        name=PROJ_NAME,
        package=PROJ_NAME,
        extensions=[Django()],
        version=pyscaffold_version,
        config_files=NO_CONFIG,
    )
    # NO_CONFIG: avoid extra config from dev's machine interference

    # when the project is created,
    create_project(opts)

    # then django files should exist
    for path in DJANGO_FILES:
        assert Path(path).exists()
    # and also overwritable pyscaffold files (with the exact contents)
    existing = (tmpfolder / PROJ_NAME / "setup.py").read_text()
    assert existing == get_template("setup_py").safe_substitute(opts)


def test_pretend_create_project_with_django(tmpfolder, isolated_log):
    # Given options with the django extension,
    isolated_log.set_level(logging.INFO)
    opts = parse_args([PROJ_NAME, "--no-config", "--pretend", FLAG])
    # --no-config: avoid extra config from dev's machine interference

    # when the project is created,
    create_project(opts)

    # then files should exist
    assert not Path(PROJ_NAME).exists()
    for path in DJANGO_FILES:
        assert not Path(path).exists()

    # but activities should be logged
    logs = isolated_log.text
    assert re.search(r"run.+django", logs)


def test_create_project_without_django(tmpfolder):
    # Given options without the django extension,
    opts = dict(project_path=PROJ_NAME, config_files=NO_CONFIG)
    # NO_CONFIG: avoid extra config from dev's machine interference

    # when the project is created,
    create_project(opts)

    # then django files should not exist
    for path in DJANGO_FILES:
        assert not Path(path).exists()


def test_create_project_no_django(tmpfolder, nodjango_admin_mock):
    # Given options with the django extension,
    # but without django-admin being installed,
    opts = dict(project_path=PROJ_NAME, extensions=[Django()], config_files=NO_CONFIG)
    # NO_CONFIG: avoid extra config from dev's machine interference

    # when the project is created,
    # then an exception should be raised.
    with pytest.raises(DjangoAdminNotInstalled):
        create_project(opts)


@pytest.mark.slow
def test_cli_with_django(tmpfolder):
    # Given the command line with the django option,
    args = ["--no-config", FLAG, PROJ_NAME]
    # --no-config: avoid extra config from dev's machine interference

    # when pyscaffold runs,
    run(args)

    # then django files should exist
    for path in DJANGO_FILES:
        assert Path(path).exists()


def test_cli_without_django(tmpfolder):
    # Given the command line without the django option,
    args = ["-vv", "--no-config", PROJ_NAME]
    # --no-config: avoid extra config from dev's machine interference

    # when pyscaffold runs,
    run(args)

    # then django files should not exist
    for path in DJANGO_FILES:
        assert not Path(path).exists()


def test_cli_with_django_and_update(tmpfolder, capfd):
    # Given a project exists
    create_project(project_path=PROJ_NAME, config_files=NO_CONFIG)
    # NO_CONFIG: avoid extra config from dev's machine interference

    # when the project is updated
    # with the django extension,
    run([PROJ_NAME, "--no-config", "--update", FLAG])
    # --no-config: avoid extra config from dev's machine interference

    # then a warning should be displayed
    out, err = capfd.readouterr()
    out_err = out + err
    try:
        assert "external tools" in out_err
        assert "not supported" in out_err
        assert "will be ignored" in out_err
    except AssertionError:
        if os.name == "nt":
            pytest.skip("pytest is having problems to capture stderr/stdout on Windows")
        else:
            raise
