from typing import Dict
from .fields import Field

class ModelMeta(type):
    def __new__(mcs,name,bases,namespaces):
        fields:Dict[str,Field]={}

        for base in bases:
            base_fields=getattr(base,"_fields",{})
            fields.update(base_fields)

        for key,val in list(namespaces.items()):
            if isinstance(val,Field):
                fields[key]=val
        cls=super().__new__(mcs,name,bases,namespaces)
        cls._fields=fields

        for fname, field in fields.items():
            if getattr(field, "name", None) != fname:
                field._bind_name(fname)
        return cls