
class CheckCalled(object):
    def __init__(self, object, signal):
        self.called = None

        object.connect(signal, self)

    def __call__(self, *k):
        self.called = k
