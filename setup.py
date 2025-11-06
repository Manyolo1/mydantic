from product import BaseModel, StringField, IntField, ListField, ModelField

class Address(BaseModel):
    street = StringField()
    city = StringField()

class User(BaseModel):
    name = StringField()
    age = IntField()
    address = ModelField(Address)
    tags = ListField(item_type=str, default=[])

u = User(name="Manya", age="21", address={"street":"X", "city":"New Delhi"})
print(u.dict())
print(u.json(indent=2))
