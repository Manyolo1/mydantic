from typing import Any
# check if the obj is a subclass of basemodel 
def is_model_class(obj:Any)->bool:
    try:
        from .models import BaseModel
        return isinstance(obj,type) and issubclass(obj,BaseModel)

    except Exception:
        return False
