from typing import Any, Callable, Optional, Type
from .errors import FieldError, ValidationError
from .utils import is_model_class


class Field:
    def __init__(
        self,
        field_type: Type,
        *,
        default: Any = None,
        allow_none: bool = False,
        validator: Optional[Callable[[Any], None]] = None,
        name: Optional[str] = None
    ):
        self.field_type = field_type
        self.default = default
        self.allow_none = allow_none
        self.validator = validator
        self.name = name
        self.private_name = None

    def _bind_name(self, owner_name: str):
        self.name = owner_name
        self.private_name = f"_{owner_name}"

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self.private_name, self.default)

    def _coerce(self, value):
        """Attempt to coerce value into the expected type."""
        if value is None:
            return None

        if isinstance(value, self.field_type):
            return value

        try:
            # boolean coercion (string-friendly)
            if self.field_type is bool:
                if isinstance(value, str):
                    v = value.strip().lower()
                    if v in {"true", "1", "yes", "y", "t"}:
                        return True
                    if v in {"false", "0", "no", "n", "f"}:
                        return False
                return bool(value)

            # Handle simple coercion
            if self.field_type in (int, float, str):
                return self.field_type(value)

            # for nested model coercion — let ModelField handle dicts
            if is_model_class(self.field_type):
                return value

            return self.field_type(value)

        except Exception as e:
            raise TypeError(f"Coercion failed: cannot convert {value!r} to {self.field_type}") from e

    def __set__(self, instance, value):
        if value is None:
            if self.allow_none:
                instance.__dict__[self.private_name] = None
                return
            else:
                fe = FieldError(self.name, value, self.field_type, "None not allowed.")
                raise ValidationError([fe])

        # coercion & type check
        try:
            coerced = self._coerce(value)
        except Exception as e:
            fe = FieldError(self.name, value, self.field_type, "coercion failed", e)
            raise ValidationError([fe]) from e

        
        if is_model_class(self.field_type):
            if not isinstance(coerced, self.field_type) and not isinstance(coerced, dict):
                fe = FieldError(self.name, value, self.field_type, f"expected {self.field_type} or dict")
                raise ValidationError([fe])
        else:
            if not isinstance(coerced, self.field_type):
                fe = FieldError(self.name, value, self.field_type, f"expected {self.field_type.__name__}")
                raise ValidationError([fe])

        
        if self.validator:
            try:
                self.validator(coerced)
            except Exception as e:
                fe = FieldError(self.name, coerced, self.field_type, "validation failed", e)
                raise ValidationError([fe]) from e

        instance.__dict__[self.private_name] = coerced

    def __delete__(self, instance):
        instance.__dict__.pop(self.private_name, None)


#  dev. convenience fields :)
class StringField(Field):
    def __init__(self, **kwargs):
        super().__init__(str, **kwargs) 


class IntField(Field):
    def __init__(self, **kwargs):
        super().__init__(int, **kwargs)


class FloatField(Field):
    def __init__(self, **kwargs):
        super().__init__(float, **kwargs)


class BoolField(Field):
    def __init__(self, **kwargs):
        super().__init__(bool, **kwargs)


class ListField(Field):
    def __init__(self, item_type: Type = Any, **kwargs):
        super().__init__(list, **kwargs)
        self.item_type = item_type

    def _coerce(self, value):
        if value is None:
            return None
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        raise TypeError("Cannot coerce to list.")

    def __set__(self, instance, value):
        try:
            coerced = self._coerce(value)  
        except Exception as e:
            fe = FieldError(self.name, value, "list", "coercion to list failed.", e)
            raise ValidationError([fe]) from e

        errors = []
        for idx, item in enumerate(coerced):
            if self.item_type is not Any:
                try:
                    if is_model_class(self.item_type):
                        if isinstance(item, dict):
                            self.item_type(**item)
                        elif not isinstance(item, self.item_type):
                            raise TypeError(f"list item at {idx} expected {self.item_type}")
                    else:
                        if not isinstance(item, self.item_type):
                            
                            if self.item_type in (int, float, str, bool):
                                self.item_type(item)
                            else:
                                raise TypeError(f"list item at {idx} expected {self.item_type}")
                except Exception as e:
                    errors.append(FieldError(f"{self.name}[{idx}]", item, self.item_type, str(e), e))

        if errors:
            raise ValidationError(errors)

        instance.__dict__[self.private_name] = coerced


class ModelField(Field):
    def __init__(self, model_class: Type, **kwargs):
        if not is_model_class(model_class):
            raise TypeError("ModelField expects a BaseModel subclass.")
        super().__init__(model_class, **kwargs)
        self.model_class = model_class

    def __set__(self, instance, value):
        from .models import BaseModel

        if value is None:
            if self.allow_none:
                instance.__dict__[self.private_name] = None
                return
            else:
                fe = FieldError(self.name, value, self.model_class, "None not allowed")
                raise ValidationError([fe])

        if isinstance(value, dict):
            try:
                parsed = self.model_class(**value)
            except ValidationError as e:
                new_errors = [
                    FieldError(f"{self.name}.{err.field_name}", err.value, err.expected, err.message, err.original_exception)
                    for err in e.errors
                ]
                raise ValidationError(new_errors) from e
            instance.__dict__[self.private_name] = parsed
            return

        if not isinstance(value, self.model_class):
            fe = FieldError(self.name, value, self.model_class, f"expected {self.model_class} or dict")
            raise ValidationError([fe])

        instance.__dict__[self.private_name] = value
