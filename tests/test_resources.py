
from nose.tools import *

from pygtkhelpers.resources import resource_manager


def test_resource_add():
    resource_manager.add_resource('ui', 'tests/ui')

def test_resource_find():
    resource_manager.add_resource('ui', 'tests/ui')
    assert resource_manager.get_resource('ui', 'test_slave.ui')

def test_resource_nofind():
    resource_manager.add_resource('ui', 'tests/ui')
    assert_raises(ValueError, resource_manager.get_resource, 'ui', 'test_bad_slave.ui')

