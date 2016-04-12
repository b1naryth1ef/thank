from rethinkdb import r
from uuid import UUID

from .errors import *


class BaseField(object):
    def __init__(self, primary=False, required=True, **kwargs):
        self.name = None
        self.primary = primary
        self.required = required if not primary else False

        self._has_default = False
        if 'default' in kwargs:
            self._has_default = True
            self.required = False
            self.default = kwargs['default']

    def get_default(self):
        return self.default if not callable(self.default) else self.default()

    def to_type(self, data):
        return data

    def from_type(self, data):
        return data

    def validate(self, data):
        if data is None and self.required:
            raise ValidationError("Field %s is required" % self.name)

    def resolve(self, model):
        pass

    def __lt__(self, other):
        return (r.row[self.name] < other)

    def __le__(self, other):
        return (r.row[self.name] <= other)

    def __eq__(self, other):
        return (r.row[self.name] == other)

    def __ne__(self, other):
        return (r.row[self.name] != other)

    def __gt__(self, other):
        return (r.row[self.name] > other)

    def __ge__(self, other):
        return (r.row[self.name] >= other)


class TypedField(BaseField):
    TYPE = None

    def to_type(self, data):
        return self.TYPE(data)

    def from_type(self, data):
        return data

    def validate(self, data):
        BaseField.validate(self, data)

        try:
            self.TYPE(data)
        except (TypeError, ValueError):
            raise ValidationError("Uncoercible value %s for field %s" % (data, self.name))


class IntegerField(TypedField):
    TYPE = int


class FloatField(TypedField):
    TYPE = float


class StringField(TypedField):
    TYPE = unicode


class BooleanField(TypedField):
    TYPE = bool


class BinaryField(TypedField):
    TYPE = bytes


class ObjectField(TypedField):
    TYPE = dict


class ArrayField(TypedField):
    TYPE = list


class UUIDField(BaseField):
    def to_type(self, data):
        return str(data)

    def from_type(self, data):
        return UUID(data, version=4)

    def validate(self, data):
        BaseField.validate(self, data)
        UUID(data, version=4)


class EmbeddedField(ObjectField):
    pass


class ReferenceField(BaseField):
    def __init__(self, obj, *args, **kwargs):
        if 'default' not in kwargs:
            kwargs['default'] = obj
        BaseField.__init__(self, *args, **kwargs)
        self.obj = obj
        self.obj._state.relates_from.append(self)

        if 'field' in kwargs:
            self.field = kwargs['field']
        else:
            self.field = obj._state.primary_key.name

    def to_type(self, data):
        if isinstance(data, self.obj):
            return str(data._primary)
        else:
            return data

    def from_type(self, data):
        if isinstance(data, dict):
            return self.obj.from_object(data)
        return data

    def resolve(self, model):
        model._state.relates_to.append(self)
