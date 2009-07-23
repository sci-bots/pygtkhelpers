"""
    pygtkhelpers.resources
    ~~~~~~~~~~~~~~~~~~~~~~

    resource-manager is a small tool that helps 
    with loading package data like ui files and images
"""

__all__ = "ResourceManager", "resource_manager"
import os

from collections import defaultdict

class ResourceLocation(object):
    pass

class PathResourceLocation(ResourceLocation):
    def __init__(self, base_path):
        self.base = os.path.normpath(os.path.abspath(base_path))

    def join(self, *names):
        med = os.path.join(self.base, *names)
        med = os.path.normpath(med)
        med = os.path.abspath(med)

        # prevent break-outs
        # if you need to catch that one, you are doing something wong
        assert med.startswith(self.base), "malicious resource path, %r not below %r"%(med. self.path)
        return med

    def exists(self, *names):
        path = self.join(*names)
        return os.path.exists(path)

    def read(self, *names):
        """
        return the byte content of a resource
        """

        full_path = self.join(*names)

        with open(full_path) as f:
            return f.read()

    def __eq__(self, other):
        return self.base == other.base

    def __repr__(self):
        return '<PathResourceLocation %r>'%self.base

class _PathPackageResource(PathResourceLocation):
    # the package is unziped somewhere, normal paths apply
    def __init__(self, package):
        PathResourceLocation.__init__(self, package.__path__[0])

class _LoaderPackageResource(ResourceLocation):
    # the package has a __loader__
    #XXX: todo
    pass


class _SubResource(ResourceLocation):
    def __init__(self, parent, subdir):
        self.parent = parent
        self.subdir = subdir

    def join(self, *names): return self.parent.join(self.subdir, *names)
    def exists(self, *names): return self.parent.exists(self.subdir, *names)
    def read(self, *names): return self.parent.read(self.subdir, *names)

    def __eq__(self, other):
        return self.parent == other.parent and self.subdir == other.subdir



class PackageResourceLocation(_SubResource):
    def __init__(self, package, subdir):
        print package
        if isinstance(package, str):
            print "im"
            self.package = package
            package = __import__(package, fromlist=['*'])
        else:
            self.package = package.__name__
        try:
            print package
            self._pkgr = _LoaderPackageResource(package.__loader__)
        except AttributeError:
            self._pkgr = _PathPackageResource(package)
        _SubResource.__init__(self, self._pkgr, subdir)

    def __repr__(self):
        return '<PackageResourceLocation %r/%r'%(self.package, self.subdir)

def _make_res_loc(location):
    try:
        module, subdir = location
        return PackageResourceLocation(module, subdir)
    except ValueError:
        return PathResourceLocation(location)


class ResourceManager(object): 

    def __init__(self):
        self.resources = defaultdict(list)

    def add_resource(self, category, location):
        location = _make_res_loc(location)
        self.resources[category].append(location)

    def remove_resource(self, category, location):
        location = _make_res_loc(location)
        try:
            self.resources[category].remove(location)
        except ValueError:
            pass

    def path_for(self, category, filename):
        """
        return a fully qualified path for a resource of the given type

        it might not exist in the normal filesystem
        """
        for resource in self.resources[category]:
            if resource.exists(filename):
                return resource.join(filename)
        raise LookupError('Resource does not exist.')

    def read(self, category, filename):
        """
        return the binary content of a resource as bytestring
        """
        for resource in self.resources[category]:
            if resource.exists(filename):
                return resource.read(filename)
        raise IOError("%r of %s not found"%(filename, category))



resource_manager = ResourceManager()

