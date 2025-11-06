from typing import List, Optional 

# single field error 
class FieldError(Exception):
    def __init__(self,field_name:str,value,expected,message:str,original_exception:Optional[Exception]=None):
        self.field_name=field_name
        self.value=value
        self.expected=expected
        self.message=message
        self.original_exception=original_exception
        super().__init__(f"{field_name}:{message}")

    def to_dict(self):
        return {
            "field":self.field_name,
            "value":self.value,
            "expected":self.expected,
            "message":self.message,
            "cause":repr(self.original_exception) if self.original_exception else None,
        }


# aggregated error 
class ValidationError(Exception):
    def __init__(self,errors:List[FieldError]):
        if not all(isinstance(err, FieldError) for err in errors):
            raise TypeError("All errors must be instances of FieldError")
        self.errors=errors
        message=f"{len(errors)} validation error(s): " + "; ".join(f"{err.field_name}:{err.message}" for err in errors)
        super().__init__(message)

    def to_dict(self):
        return {
            "errors": [err.to_dict() for err in self.errors]
              }
    def __str__(self):
        return super().__str__()
