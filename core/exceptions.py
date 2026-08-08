from rest_framework.views import exception_handler
from rest_framework import status


ERROR_CODES = {
    'VALIDATION_ERROR': 'The provided data was invalid.',
    'NOT_FOUND': 'The requested resource was not found.',
    'FORBIDDEN': 'You do not have permission to perform this action.',
    'UNAUTHORIZED': 'Authentication credentials were not provided.',
    'METHOD_NOT_ALLOWED': 'This method is not allowed.',
    'THROTTLED': 'Request was throttled. Please try again later.',
    'BAD_REQUEST': 'The request was malformed.',
    'CONFLICT': 'The request conflicts with the current state.',
    'INTERNAL_ERROR': 'An unexpected error occurred.',
}


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': ERROR_CODES['INTERNAL_ERROR'],
                    'details': {},
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    data = response.data
    error_code = get_error_code(response.status_code, data)
    message = ERROR_CODES.get(error_code, str(data))

    details = {}
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                details[key] = value
            else:
                details[key] = [str(value)]
    elif isinstance(data, list):
        details = {'non_field_errors': data}

    response.data = {
        'error': {
            'code': error_code,
            'message': message,
            'details': details,
        }
    }

    return response


def get_error_code(status_code, data):
    if status_code == 400:
        if isinstance(data, dict):
            if 'detail' in data:
                detail = str(data['detail']).lower()
                if 'not found' in detail:
                    return 'NOT_FOUND'
                if 'invalid' in detail or 'required' in detail:
                    return 'VALIDATION_ERROR'
        return 'VALIDATION_ERROR'
    elif status_code == 401:
        return 'UNAUTHORIZED'
    elif status_code == 403:
        return 'FORBIDDEN'
    elif status_code == 404:
        return 'NOT_FOUND'
    elif status_code == 405:
        return 'METHOD_NOT_ALLOWED'
    elif status_code == 409:
        return 'CONFLICT'
    elif status_code == 429:
        return 'THROTTLED'
    return 'BAD_REQUEST'


from rest_framework.response import Response
