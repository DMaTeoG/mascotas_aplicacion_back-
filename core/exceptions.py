import logging
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.exceptions import ValidationError

logger = logging.getLogger('petmatch.errors')

def custom_exception_handler(exc, context):
    """
    Handler centralizado de excepciones para Django REST Framework.
    Interpreta y registra en backend/logs/errors.log cualquier fallo de validación
    o error no controlado, asociándolo al path y view que lo disparó.
    """
    response = drf_exception_handler(exc, context)

    view_name = context.get('view').__class__.__name__ if context.get('view') else 'UnknownView'
    request = context.get('request')
    path = request.path if request else 'UnknownPath'
    method = request.method if request else 'UnknownMethod'
    request_id = getattr(request, 'request_id', 'no-id')

    if response is not None:
        if response.status_code == 400:
            logger.warning(
                f"[API-VALIDATION-ERROR] id={request_id} view={view_name} method={method} path={path} "
                f"details={response.data}"
            )
        else:
            logger.error(
                f"[API-CLIENT-ERROR] id={request_id} view={view_name} status={response.status_code} "
                f"method={method} path={path} details={response.data}"
            )
    else:
        logger.critical(
            f"[API-SERVER-EXCEPTION] id={request_id} view={view_name} method={method} path={path} "
            f"exception={str(exc)}",
            exc_info=True
        )

    return response
