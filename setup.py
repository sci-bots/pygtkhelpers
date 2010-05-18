try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='pygtkhelpers',
    version='0.4',
    author='Ali Afshar',
    author_email='aafshar@gmail.com',
    description='Helper library for PyGTK',
    packages=[
        'pygtkhelpers',
        'pygtkhelpers.ui',
        'pygtkhelpers.debug',
    ],
)
