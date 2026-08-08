from rest_framework.versioning import URLPathVersioning


class ApiVersioning(URLPathVersioning):
    """Custom URL path versioning for the API."""
    allowed_versions = ['v1']
    version_param = 'version'
    default_version = 'v1'
