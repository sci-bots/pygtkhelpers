from mock import Mock

import gtk
from pygtkhelpers.ui.objectlist import Cell, Column

def test_make_cells():
    col = Column(title='Test', cells=[
        Cell('name', int),
        Cell('name2', int),
        ])
    view_col = col.create_treecolumn(None)

    assert len(view_col.get_cells()) == 2

def test_cell_format_func():
    cell = Cell('test', format_func=str)
    assert cell.format_data(1) == '1'

def test_cell_format_string():
    cell = Cell('test', format='hoo %s')
    assert cell.format_data(1) == 'hoo 1'

def test_cell_format_for_obj():
    cell = Cell(None)
    renderer = Mock()
    cell.mappers[0](cell, 1, renderer)
    assert renderer.set_property.call_args[0][1] == 1

def test_default_type():
    cell = Cell('test')
    assert cell.mappers[0].prop == 'text'

def test_pixbuf_type():
    cell = Cell('test', type=gtk.gdk.Pixbuf)
    assert cell.mappers[0].prop == 'pixbuf'

def test_markup():
    cell = Cell('test', use_markup=True)
    assert cell.mappers[0].prop == 'markup'

def test_stock_type():
    cell = Cell('test', use_stock=True)
    assert cell.mappers[0].prop == 'stock-id'

def test_secondar_mappers():
    cell = Cell('test', mapped={'markup': 'markup_attr'})
    assert len(cell.mappers) == 1
    m = cell.mappers[0].mappers[0] #XXX cellmapper needs death
    assert m.prop == 'markup'
    assert m.attr == 'markup_attr'

def test_cell_ellipsize():
    import pango
    cell = Cell('test', ellipsize=pango.ELLIPSIZE_END)
    renderer = cell.create_renderer(None, None)
    el = renderer.get_property('ellipsize')
    assert el == pango.ELLIPSIZE_END

def test_cell_toggle():
    cell = Cell('test', use_checkbox=True)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('radio') == False

def test_cell_radio():
    cell = Cell('test', use_radio=True)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('radio') == True

def test_cell_radio_checkbox_both():
    # radio and checkbox, checkbox should win
    cell = Cell('test', use_checkbox=True, use_radio=True)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('radio') == False

def test_cell_spin():
    cell = Cell('test', type=int, use_spin=True)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('adjustment').get_property('lower') == 0

def test_cell_spin_digits_int():
    cell = Cell('test', type=int, use_spin=True)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('digits') == 0

def test_cell_spin_digits_float():
    cell = Cell('test', type=float, use_spin=True)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('digits') == 2

def test_cell_spin_digits():
    cell = Cell('test', type=float, use_spin=True, digits=5)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('digits') == 5

def test_cell_spin_min():
    cell = Cell('test', type=int, use_spin=True, min=5)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('adjustment').get_property('lower') == 5

def test_cell_spin_max():
    cell = Cell('test', type=int, use_spin=True, max=5)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('adjustment').get_property('upper') == 5

def test_cell_spin_step():
    cell = Cell('test', type=int, use_spin=True, step=5)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('adjustment').get_property('step-increment') == 5

def test_cell_progress():
    cell = Cell('test', type=int, use_progress=True)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('pulse') < 1

def test_cell_progress_text():
    cell = Cell('test', type=int, use_progress=True, progress_text='hello')
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('text') == 'hello'

def test_cell_props():
    cell = Cell('test', cell_props={'size': 100})
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('size') == 100
