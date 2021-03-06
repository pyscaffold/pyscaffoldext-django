from pathlib import Path

import pytest
from pyscaffold import cli
from pyscaffold.file_system import chdir

from pyscaffoldext.django.extension import Django

from .helpers import run_common_tasks

EXT_FLAG = Django().flag


def test_add_custom_extension(tmpfolder):
    args = ["--no-config", EXT_FLAG, "my_project", "-p", "my_package"]
    # --no-config: avoid extra config from dev's machine interference
    cli.main(args)

    assert Path("my_project/src/my_package/__init__.py").exists()


@pytest.mark.slow
@pytest.mark.system
def test_generated_extension(tmpfolder):
    args = ["--no-config", "--venv", "--pre-commit", EXT_FLAG, "my_project"]
    # --no-config: avoid extra config from dev's machine interference
    # --venv: generate a venv so we can install the resulting project
    # --pre-commit: ensure generated files respect repository conventions
    cli.main(args)

    with chdir("my_project"):
        # Testing a project generated by the custom extension
        run_common_tasks()
