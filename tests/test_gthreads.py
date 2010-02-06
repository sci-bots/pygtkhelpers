from itertools import repeat
from pygtkhelpers.utils import refresh_gui
from pygtkhelpers.gthreads import AsyncTask, GeneratorTask
from pygtkhelpers.gthreads import gcall, invoke_in_mainloop

def test_async_task():

    data = []

    def do():
        data.append(1)
        return 2, 3

    def done(*k):
        data.extend(k)

    GeneratorTask(do, done).start()
    refresh_gui()
    assert data == [1, 2, 3]


def test_generator_task():
    data = []

    def do():
        for i in range(10):
            yield i

    def work(val):
        data.append(val)

    def done():
        data.extend(data)

    GeneratorTask(do, work, done).start()
    refresh_gui()

    assert data == range(10)*2


def test_gcall():
    data = []

    def doit():
        gcall(data.append, 1)

    AsyncTask(doit).start()
    refresh_gui(.1)
    assert data == [1]


def test_invoke_in_mainloop():
    data = []

    def doit():
        invoke_in_mainloop(data.append, 1)
        assert invoke_in_mainloop(len, data) == 1

    AsyncTask(doit).start()
    # timeout needed for asynctask cleanup
    refresh_gui(.1)
    assert data == [1]
