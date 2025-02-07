from django.db import models

class NullableIntegerField(models.IntegerField):
    """
    A custom IntegerField that treats an empty string from the database as None.
    """
    def from_db_value(self, value, expression, connection):
        # If the database returns an empty string, treat it as None.
        if value == '':
            return None
        # If the parent class defines from_db_value, use it.
        if hasattr(super(), 'from_db_value'):
            return super().from_db_value(value, expression, connection)
        # Otherwise, return the value as is.
        return value

    def to_python(self, value):
        if value == '':
            return None
        return super().to_python(value)
