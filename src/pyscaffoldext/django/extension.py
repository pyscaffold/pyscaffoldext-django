# -*- coding: utf-8 -*-
"""
Extension that creates a base structure for the project using django-admin.py.

Warning:
    *Deprecation Notice* - In the next major release the Django extension
    will be extracted into an independent package.
    After PyScaffold v4.0, you will need to explicitly install
    ``pyscaffoldext-django`` in your system/virtualenv in order to be
    able to use it.
"""
import re
import stat
from pathlib import Path

from pyscaffold.api import Extension, helpers
from pyscaffold.log import logger
from pyscaffold.shell import ShellCommand
from pyscaffold.warnings import UpdateNotSupported

from . import templates

django_admin = ShellCommand("django-admin.py")


class Django(Extension):
    """Generate Django project files"""

    mutually_exclusive = True

    try:
        # TODO: Remove this try/except block on PyScaffold >= 4.x
        from pyscaffold.extensions import django  # Check if django is a builtin

        del django

        # WORKAROUND:
        #
        # This avoids raising an error by using `add_argument` with an
        # option/flag that was already used and at the same time provides
        # a unequivocal way of accessing the newest implementation in the
        # tests via the `--x-` prefix.
        #
        # For the time being this is useful to run against an existing
        # version of PyScaffold that have an old implementation of this
        # extension built into the core of the system. Once the builtin
        # extension is removed in future versions, the following overwriting
        # of the augment_cli method is not required.

        def augment_cli(self, parser):
            parser.add_argument(
                self.xflag,
                help="Newest version of `{}`, in development".format(self.flag),
                dest="extensions",
                action="append_const",
                const=self,
            )

        # TODO: Remove on PyScaffold 4.x
        @property
        def xflag(self):
            return "--x-" + self.flag.strip("-")

    except ImportError:
        pass  # Never mind, we are in a recent version of PyScaffold

    def activate(self, actions):
        """Register hooks to generate project using django-admin.

        Args:
            actions (list): list of actions to perform

        Returns:
            list: updated list of actions
        """

        # `get_default_options` uses passed options to compute derived ones,
        # so it is better to prepend actions that modify options.
        actions = helpers.register(
            actions, enforce_django_options, before="get_default_options"
        )
        # `apply_update_rules` uses CWD information,
        # so it is better to prepend actions that modify it.
        actions = helpers.register(
            actions, create_django_proj, before="apply_update_rules"
        )

        return actions + [instruct_user]


def enforce_django_options(struct, opts):
    """Make sure options reflect the Django usage.

    Args:
        struct (dict): project representation as (possibly) nested
            :obj:`dict`.
        opts (dict): given options, see :obj:`create_project` for
            an extensive list.

    Returns:
        struct, opts: updated project representation and options
    """
    opts["package"] = opts["project"]  # required by Django
    opts["force"] = True
    opts.setdefault("requirements", []).append("django")

    return struct, opts


def create_django_proj(struct, opts):
    """Creates a standard Django project with django-admin.py

    Args:
        struct (dict): project representation as (possibly) nested
            :obj:`dict`.
        opts (dict): given options, see :obj:`create_project` for
            an extensive list.

    Returns:
        struct, opts: updated project representation and options

    Raises:
        :obj:`RuntimeError`: raised if django-admin.py is not installed
    """
    if opts.get("update"):
        helpers.logger.warning(UpdateNotSupported(extension="django"))
        return struct, opts

    try:
        django_admin("--version")
    except Exception as e:
        raise DjangoAdminNotInstalled from e

    # TODO: replace project with project_path / name in PyScaffold 4.x

    pretend = opts.get("pretend")
    project_path = Path(opts["project"])
    pkg_name = opts["project"]

    django_admin("startproject", str(project_path), log=True, pretend=pretend)

    src_dir = project_path / "src"
    pkg_dir = src_dir / pkg_name
    orig_dir = project_path / pkg_name

    if not pretend:
        src_dir.mkdir(exist_ok=True)
        orig_dir.rename(pkg_dir)
    helpers.logger.report("move", orig_dir, target=pkg_dir)

    manage = project_path / "manage.py"
    main = pkg_dir / "__main__.py"

    if not pretend:
        manage.rename(main)
    helpers.logger.report("move", manage, target=main)

    settings = pkg_dir / "settings.py"
    replace_default_database(helpers.logger, settings, pretend=pretend)

    if not pretend:
        manage.write_text(templates.manage(opts))
        manage.chmod(manage.stat().st_mode | stat.S_IXUSR)
    helpers.logger.report("create", manage)
    helpers.logger.report("chmod", "+x {}".format(manage))

    struct = helpers.modify(
        struct,
        project_path / ".gitignore",
        lambda contents: "{}\n\n# Django\n/*.sqlite3".format(contents),
    )

    return struct, opts


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


PATTERN = re.compile(r"os\.path\.join\(BASE_DIR, ['\"]db\.sqlite3['\"]\)")
REPLACEMENT = 'os.path.join(os.path.dirname(BASE_DIR), "db.sqlite3")'


def replace_default_database(
    logger, file_path, pattern=PATTERN, replacement=REPLACEMENT, pretend=False
):
    exception = DjangoVersionMightBeUnsupported(
        "Failed attempt to replace the default sqlite3 database file with "
        "{} in {}.".format(REPLACEMENT, file_path)
    )

    try:
        if not pretend:
            text = file_path.read_text()
            replaced, n = pattern.subn(replacement, text)
            if n < 1:
                # No substitution was made, there is something wrong with the
                # assumptions on how the file should be.
                raise SystemError(text)
                raise exception
            file_path.write_text(replaced)
        logger.report("replace", "default database in {}".format(file_path))
    except PyScaffoldDjangoError:
        raise
    except Exception as ex:
        raise exception from ex


class PyScaffoldDjangoError(RuntimeError):
    """Base class for all the exceptions in this package"""


class DjangoVersionMightBeUnsupported(PyScaffoldDjangoError):
    """The files generated by django-admin.py are different from expected."""

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
    """This extension depends on the ``django-admin.py`` cli script."""

    DEFAULT_MESSAGE = "django-admin.py is not installed, " "run: pip install django"

    def __init__(self, message=DEFAULT_MESSAGE, *args, **kwargs):
        super(DjangoAdminNotInstalled, self).__init__(message, *args, **kwargs)
