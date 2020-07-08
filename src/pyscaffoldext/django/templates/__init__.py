# -*- coding: utf-8 -*-
import os
import string
from pkg_resources import resource_string


# TODO: replace with pyscaffold's reusable get_template
def get_template(name):
    """Retrieve the template by name
    Args:
        name: name of template
    Returns:
        :obj:`string.Template`: template
    """
    file_name = "{name}.template".format(name=name)
    data = resource_string(__name__, file_name)
    # we assure that line endings are converted to '\n' for all OS
    data = data.decode(encoding="utf-8").replace(os.linesep, "\n")
    return string.Template(data)


def manage(opts):
    return get_template("manage").safe_substitute(opts)
