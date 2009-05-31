
import os

from collections import defaultdict

class ResourceManager(object):

    def __init__(self):
        self.resources = defaultdict(list)

    def add_resource(self, typename, location):
        self.resources[typename].append(os.path.abspath(location))

    def get_resource(self, typename, filename):
        for resource in self.resources[typename]:
            path = os.path.join(resource, filename)
            if os.path.exists(path):
                return path
        raise LookupError('Resource does not exist.')


resource_manager = ResourceManager()

