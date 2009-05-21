
import os

from collections import defaultdict

class ResourceManager(object):

    def __init__(self):
        self.resources = defaultdict(list)

    def add_resource(self, typename, location):
        self.resources[typename].append(os.path.abspath(location))

    def get_resource(self, typename, filename):
        for resource in self.resources[typename]:
            for name in os.listdir(resource):
                if filename == name:
                    return os.path.join(resource, filename)
        raise ValueError('Resource does not exist.')


resource_manager = ResourceManager()

