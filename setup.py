try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import platform

import version


short_description = """
PyGTKHelpers is a library to assist the building of PyGTK applications.
""".strip()

long_description = """
# Note #

This project is a fork of [this project][1], written by Ali Afshar
<aafshar@gmail.com>.

# Description #

PyGTKHelpers is a library to assist the building of PyGTK applications. It is
intentionally designed to be *non-frameworky*, and blend well with your
particular style of PyGTK development.

PyGTKHelpers provides a number of widespread features including: View
delegation, MVC, mixed GtkBuilder/Python views, widget proxying, signal
auto-connection, object-base lists and trees, a number of helper widgets,
utility functions for assisting creating new GObject types, unit testing
helpers and utilities to help debug PyGTK applications.


[1]: https://pythonhosted.org/pygtkhelpers/
""".strip()


install_requires = ['cairo-helpers>=0.2.post1', 'flatland-fork>=0.4.post2',
                    'si-prefix>=0.4', 'svg-model>=0.5.post18']

# Platform-specific package requirements.
if platform.system() == 'Windows':
    install_requires += ['pygtk2-win', 'pycairo-gtk2-win']
else:
    try:
        import gtk
    except ImportError:
        print >> sys.err, ('Please install Python bindings for Gtk 2 using '
                           'your systems package manager.')


setup(name='wheeler.pygtkhelpers',
      version=version.getVersion(),
      author='Christian Fobel',
      author_email='christian@fobel.net',
      url='https://github.com/wheeler-microfluidics/pygtk_helpers',
      description=short_description,
      long_description=long_description,
      license='LGPL-3.0',
      install_requires=install_requires,
      packages=['pygtkhelpers', 'pygtkhelpers.ui', 'pygtkhelpers.debug',
                'pygtkhelpers.ui.objectlist', 'pygtkhelpers.ui.views'],
      package_data={'pygtkhelpers': ['ui/glade/*.glade',
                                     'ui/views/glade/*.glade']})
