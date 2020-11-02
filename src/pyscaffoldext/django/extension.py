"""
Extension that creates a base structure for the project using django-admin.
from typing import List
"""

# This file was transfered from the main PyScaffold repository using
# ``git filter-branch``, and therefore might have lost parts of its
# commit history.
# Please refer to ``pyscaffold`` if that is needed.

import re
import stat
from functools import partial
from pathlib import Path
from typing import List

from pyscaffold import file_system as fs
from pyscaffold.actions import Action, ActionParams, ScaffoldOpts, Structure
from pyscaffold.extensions import Extension
from pyscaffold.log import logger
from pyscaffold.operations import add_permissions
from pyscaffold.shell import ShellCommand
from pyscaffold.structure import merge, reify_content, resolve_leaf
from pyscaffold.templates import get_template

from . import templates

django_admin = ShellCommand("django-admin")
template = partial(get_template, relative_to=templates)

UPDATE_WARNING = (
    "Updating code generated using external tools is not "
    "supported. The extension `django` will be ignored, only "
    "changes in PyScaffold core features will take place."
)


class Django(Extension):
    """Generate Django project files"""

    persist = False

    def activate(self, actions: List[Action]) -> List[Action]:
        """Activate extension. See :obj:`pyscaffold.extension.Extension.activate`."""
        actions = self.register(actions, enforce_options, after="get_default_options")
        actions = self.register(actions, create_django)
        return self.register(actions, instruct_user, before="report_done")


def enforce_options(struct: Structure, opts: ScaffoldOpts) -> ActionParams:
    """Make sure options reflect the Django usage.
    See :obj:`pyscaffold.actions.Action`.
    """
    opts["force"] = True
    opts.setdefault("requirements", []).append("django")

    return struct, opts


def create_django(struct: Structure, opts: ScaffoldOpts) -> ActionParams:
    """Creates a standard Django project with django-admin.
    See :obj:`pyscaffold.actions.Action`.
    Raises:
        :obj:`RuntimeError`: raised if django-admin is not installed
    """
    if opts.get("update"):
        logger.warning(UPDATE_WARNING)
        return struct, opts

    try:
        django_admin("--version")
    except Exception as e:
        raise DjangoAdminNotInstalled from e

    pretend = opts.get("pretend")
    project_path = Path(opts["project_path"])
    pkg_name = opts["package"]
    fs.create_directory(project_path, pretend=pretend)
    django_admin("startproject", pkg_name, str(project_path), log=True, pretend=pretend)

    src_dir = project_path / "src"
    pkg_dir = src_dir / pkg_name
    orig_dir = project_path / pkg_name

    if not pretend:
        src_dir.mkdir(exist_ok=True)
        orig_dir.rename(pkg_dir)
    logger.report("move", orig_dir, target=pkg_dir)

    manage = project_path / "manage.py"
    main = pkg_dir / "__main__.py"

    if not pretend:
        manage.rename(main)
    logger.report("move", manage, target=main)

    settings = pkg_dir / "settings.py"
    replace_default_database(logger, settings, pretend=pretend)

    contents, file_op = resolve_leaf(struct[".gitignore"])
    gitignore = reify_content(contents, opts) + "{}\n\n# Django\n/*.sqlite3\n"

    files: Structure = {
        ".gitignore": (gitignore, file_op),
        "manage.py": (template("manage"), add_permissions(stat.S_IXUSR)),
    }

    return merge(struct, files), opts


def instruct_user(struct, opts):
    logger.warning(
        "\nDjango is used to create web applications while PyScaffold makes it "
        "easy to create re-usable Python (pip) packages, such as libraries.\n"
        "There is nothing wrong with trying to distribute your web application "
        "as an installable package, but you have to be aware about the changes "
        "in mindset. Please check the official docs in\n\n"
        "\thttps://pyscaffold.org/projects/django\n\n"
        "for more information.\n"
    )

    return struct, opts


PATTERN = re.compile(r"BASE_DIR\s*/\s*['\"]db\.sqlite3['\"]")
REPLACEMENT = 'BASE_DIR.parent / "db.sqlite3"'


def replace_default_database(
    logger, file_path, pattern=PATTERN, replacement=REPLACEMENT, pretend=False
):
    exception = DjangoVersionMightBeUnsupported(
        "Failed attempt to replace the default sqlite3 database file with "
        f"{REPLACEMENT} in {file_path}."
    )

    try:
        if not pretend:
            text = file_path.read_text()
            replaced, n = pattern.subn(replacement, text)
            if n < 1:
                # No substitution was made, there is something wrong with the
                # assumptions on how the file should be.
                raise SystemError(text)
            file_path.write_text(replaced)
        logger.report("replace", f"default database in {file_path}")
    except PyScaffoldDjangoError:
        raise
    except Exception as ex:
        raise exception from ex


class PyScaffoldDjangoError(RuntimeError):
    """Base class for all the exceptions in this package"""


class DjangoVersionMightBeUnsupported(PyScaffoldDjangoError):
    """The files generated by django-admin are different from expected."""

    EXTRA = (
        "\nA possible reason for that is that a new version of Django is "
        "incompatible with pyscaffoldext-django.\n"
        "Please visit the documentation in https://pyscaffold.org/projects/django "
        "and follow the steps to integrate django manually.\n"
        "Please also consider submitting a pull request with the fix."
    )

    def __init__(self, message=None, *args, **kwargs):
        message = (message or self.__class__.__doc__) + self.EXTRA
        super(DjangoVersionMightBeUnsupported, self).__init__(message, *args, **kwargs)


class DjangoAdminNotInstalled(PyScaffoldDjangoError):
    """This extension depends on the ``django-admin`` cli script."""

    DEFAULT_MESSAGE = "django-admin is not installed, " "run: pip install django"

    def __init__(self, message=DEFAULT_MESSAGE, *args, **kwargs):
        super(DjangoAdminNotInstalled, self).__init__(message, *args, **kwargs)
