import gtk
from pygtkhelpers.utils import refresh_gui
from pygtkhelpers.ui.objectlist import Column

def test_column_title():
    col = Column("name")
    view_col = col.create_treecolumn(None)
    assert view_col.get_title() == "Name"

    title_col = Column(title="Test", cells=[])
    title_view_col = title_col.create_treecolumn(None)
    assert title_view_col.get_title() == 'Test'
    assert len(title_view_col.get_cells()) == 0

def test_column_visiblility():
    col = Column('test')
    view_col = col.create_treecolumn(None)
    assert view_col.get_visible()

def test_column_invisiblility():
    col = Column('test', visible=False)
    view_col = col.create_treecolumn(None)
    assert not view_col.get_visible()

def test_column_width():
    col = Column('test', width=30)
    view_col = col.create_treecolumn(None)
    refresh_gui()
    assert view_col.get_sizing() == gtk.TREE_VIEW_COLUMN_FIXED
    assert view_col.get_fixed_width() == 30

def test_column_expandable():
    col = Column('name', expand=True)
    treeview_column = col.create_treecolumn(None)
    assert treeview_column.props.expand
