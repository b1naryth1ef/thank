from rethinkdb import r


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

        self.filter_raw = []
        self._only = set()
        self._join = {}

    def compile(self):
        q = self.table

        # Seperate filter argument
        if self.filter_raw:
            q = self.table.filter(reduce(lambda a, b: a & b, self.filter_raw))

        # Joins cause a merge function to be executed
        if self._join:
            for k, v in self._join.iteritems():
                q = q.merge(lambda z: {
                    k: r.table(k).get(z[v])
                })
        return q

    def debug(self):
        return self.compile().run(self.conn)

    def filter_by(self, **kwargs):
        for k, v in kwargs.iteritems():
            if hasattr(v, '_primary'):
                v = v._primary
            self.filter_raw.append(r.row[k] == v)
        return self

    def filter(self, *args):
        self.filter_raw += list(args)
        return self

    def only(self, *args):
        for arg in args:
            if hasattr(arg, 'name'):
                self._only.add(arg.name)
            else:
                # TODO: validate
                self._only.add(str(arg))
        return self

    def join(self, other):
        our_field = next((field for field in self.parent._state.relates_to if field.obj == other), None)
        if not our_field:
            raise Exception("Cannot join on Model %v, no relation" % other)

        self._join[other._state.name] = our_field.name

        return self

    def one(self):
        return list(QueryResult(self, self.compile().limit(1).run(self.conn)))[0]

    def all(self, cached=True):
        return QueryResult(self, self.compile().run(self.conn), cached=cached)

    def count(self):
        return self.compile().count().run(self.conn)

    def delete(self):
        return self.compile().delete().run(self.conn)['deleted']
