import time
import uuid
import logging

logger = logging.getLogger('petmatch.request')

class RequestLoggingMiddleware:
    """
    Middleware que inyecta un ID de trazabilidad (X-Request-ID) en cada petición,
    calcula la duración de la misma y registra información estructurada de seguimiento.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4())[:8])
        request.request_id = request_id
        start_time = time.time()

        # Log al iniciar la petición
        client_ip = self._get_client_ip(request)
        logger.info(f"[REQ-START] id={request_id} method={request.method} path={request.path} ip={client_ip}")

        try:
            response = self.get_response(request)
        except Exception as exc:
            duration = round((time.time() - start_time) * 1000, 2)
            logger.exception(f"[REQ-ERROR] id={request_id} method={request.method} path={request.path} duration={duration}ms error={str(exc)}")
            raise exc

        duration = round((time.time() - start_time) * 1000, 2)
        response['X-Request-ID'] = request_id

        log_level = logger.warning if response.status_code >= 400 else logger.info
        log_level(f"[REQ-END] id={request_id} method={request.method} path={request.path} status={response.status_code} duration={duration}ms")

        return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')

# Logging optimizations
