from .fields import BaseField


class QueryResult(object):
    def __init__(self, query, cursor, cached=False):
        self.query = query
        self.cursor = cursor
        self.cached = cached
        self._cache = []

    def __len__(self):
        return self.query.count()

    def __getitem__(self, item):
        if not self.cached:
            raise Exception("Cannot index a non-cached QueryResult")

        load = (len(self._cache) - item) - 1
        if load > 0:
            for _ in range(load):
                self.next()
        return self._cache[item]

    def next(self):
        obj = self.query.parent.from_object(self.cursor.next())
        if self.cached:
            self._cache.append(obj)
        return obj

    def __iter__(self):
        for item in self.cursor:
            obj = self.query.parent.from_object(item)
            if self.cached:
                self._cache.append(obj)
            yield obj


class Query(object):
    def __init__(self, parent):
        self.parent = parent
        self.table = self.parent._state.table
        self.conn = self.parent._state.conn

        self._filters = {}
        self._only = set()

    def _compile(self):
        q = self.table
        if self._filters:
            q = self.table.filter(self._filters)
        return q

    def filter_by(self, **kwargs):
        self._filters.update(kwargs)
        return self

    def only(self, *args):
        for arg in args:
            if isinstance(arg, BaseField):
                self._only.add(arg.name)
            else:
                # TODO: validate
                self._only.add(str(arg))
        return self

    def one(self):
        return list(QueryResult(self, self._compile().limit(1).run(self.conn)))[0]

    def all(self, cached=True):
        return QueryResult(self, self._compile().run(self.conn), cached=cached)

    def count(self):
        return self._compile().count().run(self.conn)

    def delete(self):
        return self._compile().delete().run(self.conn)['deleted']
