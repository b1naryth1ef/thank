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

    def to_type(self, data):
        return data

    def from_type(self, data):
        return data

    def validate(self, data):
        if data is None and self.required:
            raise ValidationError("Field %s is required" % self.name)


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


class StringField(TypedField):
    TYPE = str


class UUIDField(BaseField):
    def to_type(self, data):
        return str(data)

    def from_type(self, data):
        return UUID(data, version=4)

    def validate(self, data):
        BaseField.validate(self, data)
        UUID(data, version=4)
