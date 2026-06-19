"""
Utility functions for JSON serialization of MongoDB documents.
"""
from bson import ObjectId
from typing import Any, Dict, List


def convert_objectid_to_str(obj: Any) -> Any:
    """
    Recursively convert ObjectId instances to strings in a dictionary or list.
    """
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    else:
        return obj


def serialize_mongo_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a MongoDB document to a JSON-serializable dictionary.
    Converts all ObjectId fields to strings.
    """
    if doc is None:
        return None
    return convert_objectid_to_str(doc)

