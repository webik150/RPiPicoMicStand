import ujson

class JSON:
    @staticmethod
    def deserialize(obj, data):
        if not isinstance(data, dict):
            raise TypeError(f"Expected data to be a dictionary, got {type(data)}")

        for key, value in data.items():
            if hasattr(obj, 'serializable_fields') and key not in obj.serializable_fields():
                raise AttributeError(f"{obj} has no attribute {key}")
            else:
                # if obj is dict, deserialize the value and set it
                if isinstance(obj, dict):
                    # if value is of basic type, set it
                    if isinstance(obj[key], (int, float, str, bool, type(None))):
                        obj[key] = value
                    elif isinstance(obj[key], list) and isinstance(value, list):
                        obj[key].clear()
                        obj[key].extend(value)
                    elif isinstance(obj[key], dict) and isinstance(value, dict):
                        JSON.deserialize(obj[key], value)
                    elif hasattr(obj[key], 'from_json'):
                        obj[key].from_json(ujson.dumps(value))

                    continue

                attr = getattr(obj, key)
                if isinstance(attr, (int, float, str, bool, type(None))):
                    setattr(obj, key, value)
                elif isinstance(attr, list) and isinstance(value, list):
                    attr.clear()
                    attr.extend(value)
                elif isinstance(attr, dict) and isinstance(value, dict):
                    JSON.deserialize(attr, value)
                elif hasattr(attr, 'from_json'):
                    attr.from_json(ujson.dumps(value))
                # elif isinstance(attr, dict):
                #     print(f"Deserializing dict {key}: {value}")
                #     setattr(obj, key, value)

    @staticmethod
    def serialize(obj):
        if isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        elif isinstance(obj, dict):
            return {key: JSON.serialize(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [JSON.serialize(item) for item in obj]
        elif hasattr(obj, 'serializable_fields'):
            return {field: JSON.serialize(getattr(obj, field)) for field in obj.serializable_fields()}
        else:
            raise TypeError(f"Type {type(obj)} not serializable")

