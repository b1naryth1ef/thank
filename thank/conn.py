from rethinkdb import r


class Connection(object):
    def __init__(self, *args, **kwargs):
        self.c = r.connect(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.c, name)

    @property
    def use(self):
        class _T(object):
            class Meta:
                conn = self
        return _T
