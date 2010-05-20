try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

short_description = """
PyGTKHelpers is a library to assist the building of PyGTK applications.
""".strip()

long_description = """
PyGTKHelpers is a library to assist the building of PyGTK applications. It is
intentionally designed to be *non-frameworky*, and blend well with your
particular style of PyGTK development.

PyGTKHelpers provides a number of widespread features including: View
delegation, MVC, mixed GtkBuilder/Python views, widget proxying, signal
auto-connection, object-base lists and trees, a number of helper widgets,
utility functions for assisting creating new GObject types, unit testing
helpers and utilities to help debug PyGTK applications.
""".strip()

setup(
    name='pygtkhelpers',
    version='0.4.1',
    author='Ali Afshar',
    author_email='aafshar@gmail.com',
    url='http://packages.python.org/pygtkhelpers',
    description=short_description,
    long_description=long_description,
    license='LGPL-3.0',
    packages=[
        'pygtkhelpers',
        'pygtkhelpers.ui',
        'pygtkhelpers.debug',
    ],
)
