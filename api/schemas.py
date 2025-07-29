"""
API request/response schemas using Marshmallow.
"""

from marshmallow import Schema, fields, validate, ValidationError


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