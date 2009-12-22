import gtk

from pygtkhelpers.debug import ExtendedExceptionDialog, install_hook


def _test2(*a):
    a = 1
    b = 0
    a/b

def _test(*a):
    x = lambda: _test2()
    x()

def _main():
    install_hook(ExtendedExceptionDialog)
    w = gtk.Window()
    w.set_title('test')
    w.set_size_request(100,100)
    w.connect('destroy', gtk.main_quit)
    b = gtk.Button("click")
    b.connect("clicked", _test)
    w.add(b)
    w.show_all()

    gtk.main()

if __name__=='__main__':
    _main()
