from typing import Dict, Any, Type
import json 
from .fields import Field, ModelField, ListField
from .utils import is_model_class
from .core import   ModelMeta
from .errors import FieldError, ValidationError
class BaseModel(metaclass=ModelMeta):
    def __init__(self,**kwargs):
        errors=[]

        for name,field in self._fields.items():
            if name in kwargs:
                try:
                    setattr(self,name,kwargs.pop(name))
                except ValidationError as e:
                    errors.extend(e.errors)  # Use extend instead of append for nested ValidationErrors
                except Exception as e:
                    errors.append(FieldError(name,kwargs.get(name),getattr(field,"field_type","unknown"),str(e),e))
            else:
                if getattr(field,"default",None) is None and not getattr(field,"allow-none",False):
                    errors.append(FieldError(name,None,getattr(field,"field_type","unknown"),"Missing required field."))

        if kwargs:
             errors.append(FieldError("__base__", kwargs, None, f"Unexpected fields: {', '.join(kwargs.keys())}"))
        if errors:
            raise ValidationError(errors)


    @classmethod
    def parse_obj(cls: Type["BaseModel"], obj: Dict[str, Any]) -> "BaseModel":
        if not isinstance(obj, dict):
            raise TypeError("parse_obj expects a mapping/dict")
        return cls(**obj)

    def json(self, **kwargs) -> str:
        return json.dumps(self.dict(), **kwargs)

    def copy(self, **updates) -> "BaseModel":
        data = self.dict()
        data.update(updates)
        return self.__class__(**data)

    def __repr__(self):
        items = ", ".join(f"{k}={getattr(self, k)!r}" for k in self._fields)
        return f"{self.__class__.__name__}({items})"
    
    def dict(self) -> Dict[str, Any]:
        res = {}
        for name, field in self._fields.items():
            val = getattr(self, name)
            if is_model_class(getattr(field, "field_type", None)) and val is not None:
                res[name] = val.dict()
            else:
                res[name] = val
        return res
