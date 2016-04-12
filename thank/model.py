import copy
from rethinkdb import r
from collections import OrderedDict

from .query import Query
from .fields import BaseField, UUIDField


class State(object):
    pass


class BaseModel(object):
    pass


class ModelMeta(type):
    def __init__(self, name, cls, attrs):
        self._state = State()
        self._state.primary_key = None
        self._state.fields = OrderedDict()
        self._state.meta = {}

        for parent_cls in cls:
            if issubclass(parent_cls, BaseModel) and not parent_cls == BaseModel:
                self._state = copy.deepcopy(parent_cls._state)
            elif hasattr(parent_cls, 'Meta'):
                for k in dir(parent_cls.Meta):
                    self._state.meta[k] = getattr(parent_cls.Meta, k)

        if 'Meta' in attrs:
            self._state.meta.update(attrs['Meta'])

        self._state.cls_name = name

        # Other fields that relate this model
        self._state.relates_from = []

        # Relations within this field
        self._state.relates_to = []

        self._resolve_fields(attrs)
        self._resolve_meta()

    def _resolve_meta(self):
        self._state.conn = self._state.meta.get('conn')
        self._state.name = self._state.meta.get('table_name', self._state.cls_name.lower())
        self._state.table = r.table(self._state.name)
        self._state.dura = self._state.meta.get('durability', 'hard')
        self._state.shards = self._state.meta.get('shards', 1)

    def _resolve_fields(self, attrs):
        for k, v in attrs.iteritems():
            if not isinstance(v, BaseField):
                continue
            self._state.fields[k] = v
            v.name = k

            if v.primary:
                if not self._state.primary_key:
                    self._state.primary_key = v
                else:
                    raise Exception("Multiple primary keys passed")

            v.resolve(self)

        if not self._state.primary_key:
            raise Exception("No primary-key specified")

    def table_create(self):
        r.table_create(
            self._state.name,
            primary_key=self._state.primary_key.name,
            durability=self._state.dura,
            shards=self._state.shards).run(self._state.conn)

    def table_delete(self):
        r.table_drop(self._state.name).run(self._state.conn)

    def table_exists(self):
        return self._state.name in r.table_list().run(self._state.conn)

    @property
    def objects(self):
        return Query(self)


class Model(BaseModel):
    __metaclass__ = ModelMeta

    id = UUIDField(primary=True)

    def __init__(self, *args, **kwargs):
        self._loaded = False

        for index, value in enumerate(args):
            setattr(self, self._state.fields.keys()[index], value)

        for k, v in kwargs.items():
            if k not in self._state.fields.keys():
                raise Exception("Unknown field %s" % k)
            setattr(self, k, v)

    @classmethod
    def from_object(cls, obj):
        self = cls()
        self._loaded = True

        for k, v in obj.iteritems():
            setattr(self, k, getattr(self, k).from_type(v))

        return self

    @classmethod
    def create(cls, *args, **kwargs):
        return cls(*args, **kwargs).save(create=True)

    def validate(self):
        for k, v in self._state.fields.items():
            value = getattr(self, k)
            if isinstance(value, BaseField):
                if value.primary:
                    continue

                # If we have a default value, fill it in
                if value._has_default:
                    value = value.get_default()
                else:
                    value = None
            v.validate(value)

    @property
    def _primary(self):
        return getattr(self, self._state.primary_key.name)

    @_primary.setter
    def _primary(self, val):
        setattr(self, self._state.primary_key.name, val)

    def _get_object(self):
        self.validate()
        return {
            k: v.to_type(getattr(self, k)) for k, v in self._state.fields.items()
            if not isinstance(getattr(self, k), BaseField)
        }

    def save(self, create=False):
        data = self._get_object()

        if isinstance(self._primary, BaseField) or create:
            res = self._state.table.insert(data).run(self._state.conn)
            self._primary = res['generated_keys'][0]
        else:
            self._state.table.get(self._primary).update(data).run(self._state.conn)
        return self

    def replace(self, id):
        data = self._get_object()
        self._state.table.get(id).replace(data).run(self._state.conn)
        return self

    def delete(self):
        self._state.table.get(self._primary).delete().run(self._state.conn)
        return self
