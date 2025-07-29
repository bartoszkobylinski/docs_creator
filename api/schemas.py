"""
API request/response schemas using Marshmallow.
"""

from marshmallow import Schema, fields, validate, ValidationError
from functools import wraps
from flask import request, jsonify


class ScanRequestSchema(Schema):
    """Schema for project scanning requests."""
    project_path = fields.Str(required=True, validate=validate.Length(min=1))


class LocalScanRequestSchema(Schema):
    """Schema for local project scanning."""
    project_path = fields.Str(required=True, validate=validate.Length(min=1))


class DocstringSaveRequestSchema(Schema):
    """Schema for saving docstrings."""
    item = fields.Dict(required=True)
    docstring = fields.Str(required=True, allow_none=True)


class DocstringGenerateRequestSchema(Schema):
    """Schema for generating docstrings."""
    item = fields.Dict(required=True)


class UMLGenerateRequestSchema(Schema):
    """Schema for UML generation."""
    items = fields.List(fields.Dict(), required=True)
    config = fields.Str(missing="overview", validate=validate.OneOf([
        "overview", "detailed", "simple", "classes_only", "inheritance"
    ]))


class ConfluenceSettingsSchema(Schema):
    """Schema for Confluence settings."""
    url = fields.Url(required=True)
    username = fields.Email(required=True)
    token = fields.Str(required=True, validate=validate.Length(min=1))
    space_key = fields.Str(required=True, validate=validate.Length(min=1))


class DocumentationGenerateSchema(Schema):
    """Schema for documentation generation."""
    project_name = fields.Str(missing="API Documentation")
    include_uml = fields.Bool(missing=True)


class ConfluencePublishSchema(DocumentationGenerateSchema):
    """Schema for Confluence publishing."""
    title_suffix = fields.Str(missing=None)


# Response schemas
class ScanResultSchema(Schema):
    """Schema for scan results."""
    success = fields.Bool(required=True)
    message = fields.Str(required=True)
    items = fields.List(fields.Dict())
    total_files = fields.Int()
    scan_time = fields.Float()


class DocstringSaveResultSchema(Schema):
    """Schema for docstring save results."""
    success = fields.Bool(required=True)
    message = fields.Str(required=True)
    backup_path = fields.Str(allow_none=True)


class GenerateResultSchema(Schema):
    """Schema for docstring generation results."""
    docstring = fields.Str(required=True)


class ReportStatusSchema(Schema):
    """Schema for report status."""
    exists = fields.Bool(required=True)
    path = fields.Str(required=True)
    item_count = fields.Int(required=True)


class ErrorSchema(Schema):
    """Schema for error responses."""
    error = fields.Str(required=True)
    message = fields.Str()
    status_code = fields.Int()


def validate_request(schema_definition):
    """
    Decorator for request validation using simple schema definitions.
    This is a placeholder implementation since the original validate_request
    function is being used but wasn't defined.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Simple validation - just check if request has JSON data
            if not request.is_json:
                return jsonify({"error": "Request must be JSON"}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
            
            # Basic validation based on schema_definition
            if isinstance(schema_definition, dict):
                required_fields = schema_definition.get('required', [])
                for field in required_fields:
                    if field not in data:
                        return jsonify({"error": f"Missing required field: {field}"}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator