import sys

class Hook(object):
    def __init__(self, oldhook):
        self.called = False
        self.oldhook = oldhook


    def __call__(self, *k):
        self.called = True
        self.args = k
        self.oldhook(*k)


def pytest_runtest_call(item, __multicall__):
    sys.excepthook = Hook(sys.excepthook)
    __multicall__.execute()
    hook = sys.excepthook
    sys.excepthook = hook.oldhook
    if hook.called:
        tp, val, tb = hook.args
        print repr(tp), repr(val), repr(tb)
        raise tp, val, tb
