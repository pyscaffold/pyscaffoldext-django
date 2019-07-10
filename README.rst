.. image:: https://travis-ci.org/pyscaffold/pyscaffoldext-django.svg?branch=master
    :alt: Travis
    :target: https://travis-ci.org/pyscaffold/pyscaffoldext-django
.. image:: https://readthedocs.org/projects/pyscaffoldext-django/badge/?version=latest
    :alt: ReadTheDocs
    :target: https://pyscaffoldext-django.readthedocs.io/
.. image:: https://img.shields.io/coveralls/github/pyscaffold/pyscaffoldext-django/master.svg
    :alt: Coveralls
    :target: https://coveralls.io/r/pyscaffold/pyscaffoldext-django
.. image:: https://img.shields.io/pypi/v/pyscaffoldext-django.svg
    :alt: PyPI-Server
    :target: https://pypi.org/project/pyscaffoldext-django/

====================
pyscaffoldext-django
====================


    Integration of **Django**'s built-in generator (``django-admin``)
    into **PyScaffold**

`PyScaffold`_ is a development tool focused in distributable Python packages.
This extension allows the development of `Django`_ websites using
PyScaffold sensible project structure, by tapping into the `django-admin`_ cli.

Quickstart
==========

This extension can be directly installed with ``pip``:

.. code-block:: bash

    $ pip install pyscaffoldext-django

Or, if you prefer ``pipx``:

.. code-block:: shell

   $ pipx install pyscaffold  # if you haven't installed pyscaffold yet
   $ pipx inject pyscaffold pyscaffoldext-django

Note that, after the installation, ``putup -h`` will show a new option
``--django``. Use this option to indicate when you are trying to create a
django app. For example:

.. code-block:: shell

   $ putup --django myapp

Please refer to `django-admin`_ documentation for more details.

.. note::

    Using Django extension in PyScaffold is roughly equivalent to first create
    an app using `django-admin` and then convert it to PyScaffold:

    .. code-block:: bash

        $ django-admin startproject myapp
        $ mkdir myapp/src
        $ mv myapp/myapp myapp/src
        $ putup myapp --force

    For complex use cases, maybe a better option is to do the conversion
    manually.


Note
====

This project has been set up using PyScaffold 3.2. For details and usage
information on PyScaffold see https://pyscaffold.org/.


.. _PyScaffold: https://pyscaffold.org
.. _Django: https://www.djangoproject.com/
.. _django-admin: https://docs.djangoproject.com/en/2.2/ref/django-admin/
.. _extension: https://pyscaffold.org/en/latest/extensions.html
