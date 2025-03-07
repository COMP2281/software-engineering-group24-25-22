"""
Custom JSON encoding utilities for MongoDB objects and other non-standard types
"""
import json
from bson import ObjectId
from decimal import Decimal

class MongoJSONEncoder(json.JSONEncoder):
    """JSON encoder that can handle MongoDB ObjectId objects and Decimal objects"""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)