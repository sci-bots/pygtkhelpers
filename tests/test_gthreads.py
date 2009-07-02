from itertools import repeat
from pygtkhelpers.utils import refresh_gui
from pygtkhelpers.gthreads import AsyncTask, GeneratorTask

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

