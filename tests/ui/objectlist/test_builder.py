import gtk
from pygtkhelpers.ui.objectlist import ObjectList

def test_build_simple():
    uidef = '''
        <interface>
          <object class="PyGTKHelpersObjectList" id="test">
          </object>
        </interface>
    '''
    b = gtk.Builder()
    b.add_from_string(uidef)
    objectlist = b.get_object('test')
    print objectlist
    assert isinstance(objectlist, ObjectList)

