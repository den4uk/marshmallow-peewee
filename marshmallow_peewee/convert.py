import peewee as pw
from marshmallow import fields, validate as ma_validate
from marshmallow.compat import OrderedDict


class Related(fields.Nested):

    def __init__(self, nested=None, **kwargs):
        return super(Related, self).__init__(nested, **kwargs)

    def init_model(self, model, name):
        from .schema import ModelSchema
        field = model._meta.fields[name]
        rel_model = field.rel_model
        meta = type('Meta', (), {'model': rel_model})
        self.nested = type('Schema', (ModelSchema,), {'Meta': meta})


class ModelConverter(object):

    """ Convert Peewee model to Marshmallow schema."""

    TYPE_MAPPING = {
        pw.PrimaryKeyField: fields.Integer,
        pw.IntegerField: fields.Integer,
        pw.BigIntegerField: fields.Integer,
        pw.FloatField: fields.Float,
        pw.DoubleField: fields.Float,
        pw.DecimalField: fields.Decimal,
        pw.CharField: fields.String,
        pw.FixedCharField: fields.String,
        pw.TextField: fields.String,
        pw.UUIDField: fields.UUID,
        pw.DateTimeField: fields.DateTime,
        pw.DateField: fields.Date,
        pw.TimeField: fields.Time,
        pw.BooleanField: fields.Boolean,
        pw.ForeignKeyField: fields.Integer,
    }

    def fields_for_model(self, model, opts):
        fields = opts.fields
        result = OrderedDict()
        for field in [f for f in model._meta.sorted_fields if not fields or f.name in fields]:
            ma_field = self.convert_field(field)
            if ma_field:
                result[field.name] = ma_field
        return result

    def convert_field(self, field):
        params = {
            'allow_none': field.null,
            'attribute': field.name,
            'default': field.default,
            'required': not field.null and not field.default,
            'validate': field.coerce,
        }
        method = getattr(self, 'convert_' + field.__class__.__name__, self.convert_default)
        return method(field, **params)

    def convert_default(self, field, **params):
        """Return raw field."""
        ma_field = self.TYPE_MAPPING.get(type(field), fields.Raw)
        return ma_field(**params)

    def convert_PrimaryKeyField(self, field, **params):
        return fields.Integer(dump_only=True, **params)

    def convert_CharField(self, field, validate=None, **params):
        validate = ma_validate.Length(max=field.max_length)
        return fields.String(validate=validate, **params)

    def convert_ForeignKeyField(self, field, attribute=None, **params):
        return fields.Integer(attribute=field.db_column, **params)
