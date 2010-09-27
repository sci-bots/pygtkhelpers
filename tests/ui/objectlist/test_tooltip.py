
import gtk
from pygtkhelpers.ui.objectlist import Column

class MockTooltip(object):
    def set_text(self, text):
        self.text = text

    def set_markup(self, markup):
        self.markup = markup

    def set_custom(self, custom):
        self.custom = custom

    def set_icon(self, icon):
        self.pixbuf = icon

    def set_icon_from_stock(self, stock, size):
        self.stock = stock
        self.size = size

    def set_icon_from_icon_name(self, iconname, size):
        self.iconname = iconname
        self.size = size

class Fruit(object):
    attr = 'value'

def test_tooltip_type_text_value():
    c = Column('test', tooltip_value='banana')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.text == 'banana'

def test_tooltip_type_text_attr():
    c = Column('test', tooltip_attr='attr')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.text == 'value'

def test_tooltip_type_markup_value():
    c = Column('test', tooltip_value='banana', tooltip_type='markup')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.markup == 'banana'

def test_tooltip_type_markup_attr():
    c = Column('test', tooltip_attr='attr', tooltip_type='markup')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.markup == 'value'

def test_tooltip_type_stock_value():
    c = Column('test', tooltip_value='banana', tooltip_type='stock')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.stock == 'banana'

def test_tooltip_type_stock_attr():
    c = Column('test', tooltip_attr='attr', tooltip_type='stock')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.stock == 'value'

def test_tooltip_type_iconname_value():
    c = Column('test', tooltip_value='banana', tooltip_type='iconname')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.iconname == 'banana'

def test_tooltip_type_iconname_attr():
    c = Column('test', tooltip_attr='attr', tooltip_type='iconname')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.iconname == 'value'

def test_tooltip_type_pixbuf_value():
    c = Column('test', tooltip_value='banana', tooltip_type='pixbuf')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.pixbuf == 'banana'

def test_tooltip_type_pixbuf_attr():
    c = Column('test', tooltip_attr='attr', tooltip_type='pixbuf')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.pixbuf == 'value'

def test_tooltip_type_custom_value():
    c = Column('test', tooltip_value='banana', tooltip_type='custom')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.custom == 'banana'

def test_tooltip_type_custom_attr():
    c = Column('test', tooltip_attr='attr', tooltip_type='custom')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.custom == 'value'

def test_tooltip_image_size():
    c = Column('test', tooltip_attr='attr', tooltip_type='iconname',
                tooltip_image_size=gtk.ICON_SIZE_MENU)
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.iconname == 'value'
    assert t.size == gtk.ICON_SIZE_MENU


