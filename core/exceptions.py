import logging
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models.deletion import ProtectedError, RestrictedError
from django.db import IntegrityError
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('anivel.api')


def custom_exception_handler(exc, context):
    """
    Manejador global y centralizado de excepciones para Django REST Framework.

    Objetivos:
    1. Erradicar fugas de información interna (stacktraces, tablas, settings, variables).
    2. Convertir excepciones de base de datos de Django (ProtectedError, IntegrityError, etc.)
       en respuestas JSON estéticas, claras y con códigos HTTP apropiados (400 / 409).
    3. Interceptar cualquier fallo no controlado (500), registrando el stacktrace completo
       en los logs del servidor para los desarrolladores, pero entregando al usuario
       un mensaje amigable y seguro sin exponer la arquitectura del sistema.
    """
    # 1. Llamar al manejador estándar de DRF
    response = exception_handler(exc, context)

    if response is not None:
        # Aseguramos formato consistente si la respuesta ya vino de DRF (ValidationError, PermissionDenied, etc.)
        return response

    # 2. Manejo de borrado protegido de Django (ProtectedError)
    if isinstance(exc, ProtectedError):
        protected_objects = getattr(exc, 'protected_objects', set())
        count = len(protected_objects) if protected_objects else 0

        logger.warning(
            f"[ProtectedError] Intento de eliminar registro con dependencias activas: {exc}. "
            f"Contexto: {context.get('view')}"
        )

        if count > 0:
            detail_msg = (
                f"No se puede eliminar este registro porque actualmente está en uso por "
                f"{count} elemento(s) dependiente(s) en el sistema. "
                "Para poder eliminarlo, primero debes reasignar o eliminar los elementos asociados."
            )
        else:
            detail_msg = (
                "No se puede eliminar este registro porque tiene elementos dependientes asociados. "
                "Por favor reasigna o elimina los elementos relacionados antes de continuar."
            )

        return Response(
            {
                "detail": detail_msg,
                "code": "protected_dependency_error",
                "count": count,
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # 3. Manejo de borrado restringido (RestrictedError)
    if isinstance(exc, RestrictedError):
        logger.warning(f"[RestrictedError] Restricción de borrado: {exc}")
        return Response(
            {
                "detail": (
                    "No es posible eliminar este registro debido a una restricción de integridad "
                    "con otros datos existentes."
                ),
                "code": "restricted_dependency_error",
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # 4. Manejo de errores de integridad de base de datos (IntegrityError: unicidad, claves foráneas, etc.)
    if isinstance(exc, IntegrityError):
        logger.warning(f"[IntegrityError] Violación de integridad en base de datos: {exc}")
        error_str = str(exc).lower()

        if "unique" in error_str or "duplicate key" in error_str:
            detail_msg = "Ya existe un registro con estos datos o se infringe una regla de unicidad."
            code = "duplicate_record_error"
        elif "foreign key" in error_str:
            detail_msg = "No se puede completar la operación debido a una referencia no válida o una dependencia existente."
            code = "foreign_key_constraint_error"
        else:
            detail_msg = "La operación no pudo completarse debido a una regla de integridad de datos."
            code = "database_integrity_error"

        return Response(
            {
                "detail": detail_msg,
                "code": code,
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # 5. Manejo de ValidationError nativo de Django
    if isinstance(exc, DjangoValidationError):
        logger.info(f"[DjangoValidationError] Validación fallida: {exc}")
        detail = getattr(exc, 'message_dict', getattr(exc, 'messages', str(exc)))
        return Response(
            {
                "detail": detail,
                "code": "validation_error",
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # 6. Excepciones inesperadas (Errores 500 no controlados)
    # IMPORTANTE: Se registra el log completo en la terminal/servidor para auditoría técnica
    view_name = context.get('view').__class__.__name__ if context.get('view') else 'UnknownView'
    logger.exception(f"[Unhandled Exception] Error 500 no controlado en {view_name}: {exc}")

    # Al cliente se le entrega un JSON seguro y estético, erradicando páginas de error de Django
    return Response(
        {
            "detail": "Ha ocurrido un error inesperado al procesar la solicitud. Por favor intenta nuevamente o contacta al administrador.",
            "code": "internal_server_error",
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
