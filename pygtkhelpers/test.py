
class CheckCalled(object):
    def __init__(self, object, signal):
        self.called = None

        def call(*k):
            self.called = k

        object.connect(signal, call)
