import py
import tests
from pygtkhelpers.resources import ResourceManager

#XXX: add something with a __loader__

class FakedLoader(object):
    __name__ = 'tests'
    def __init__(self):
        self.__loader__ = self

    def get_data(self, path):
        return path == 'ui/test_slave.ui'


locations = {
    'path': 'tests/ui',
    'package_name': ('tests', 'ui'),
    'package_instance': (tests, 'ui'),
    'package_loader': (FakedLoader(), 'ui')
}



def pytest_generate_tests(metafunc):
    for name, location in locations.items():
        metafunc.addcall(id=name, param=location)


def pytest_funcarg__resman(request):
    resman = ResourceManager()
    resman.add_resource('ui', request.param)
    return resman

def pytest_funcarg__location(request):
    return request.param


def test_resource_path_for(resman):
    assert resman.path_for('ui', 'test_slave.ui')

def test_resource_read(resman):
    assert resman.read('ui', 'test_slave.ui')

def test_resource_path_for_missing(resman):
    py.test.raises(LookupError, resman.path_for,
                   'ui', 'test_bad_slave.ui')

def test_resource_read_missing(resman):
    py.test.raises(IOError, resman.read,
                   'io', 'test_bad_slave.ui')


def test_remove_resource_location(location):
    resman = ResourceManager()
    resman.add_resource('ui', location)
    assert len(resman.resources['ui']) == 1

    resman.remove_resource('ui', location)
    assert len(resman.resources['ui']) == 0

    # shouldn't fail
    resman.remove_resource('ui', location)


