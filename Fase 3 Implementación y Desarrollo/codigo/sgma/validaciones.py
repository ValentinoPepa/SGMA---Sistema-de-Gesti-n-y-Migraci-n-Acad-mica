"""Validaciones compartidas por formularios, cargas masivas y migraciones.

Las reglas se basan en el Diccionario de Datos y Mapeo Legacy v1.1, secciones
2 y 5. El módulo usa solo la biblioteca estándar y no persiste ni modifica datos.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable


_EMAIL_RE = re.compile(r"^[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+$", re.IGNORECASE)
_DNI_SEPARATOR_RE = re.compile(r"[.\-\s]+")
_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%Y.%m.%d")


@dataclass(frozen=True)
class ErrorValidacion:
    """Error legible para UI/reporte, con código del catálogo cuando aplica."""

    codigo: str | None
    campo: str
    mensaje: str


@dataclass(frozen=True)
class ResultadoValidacion:
    """Valor normalizado y errores encontrados para un dato."""

    valor: Any = None
    errores: tuple[ErrorValidacion, ...] = ()

    @property
    def valido(self) -> bool:
        return not self.errores


def _resultado(valor: Any, codigo: str | None, campo: str, mensaje: str) -> ResultadoValidacion:
    return ResultadoValidacion(valor, (ErrorValidacion(codigo, campo, mensaje),))


def normalizar_dni(
    valor: Any,
    *,
    dni_existente: bool = False,
    dnis_del_lote: set[str] | None = None,
) -> ResultadoValidacion:
    """Quita puntos, guiones y espacios; verifica formato y duplicados.

    ``dnis_del_lote`` se actualiza con el DNI válido para detectar repetidos
    dentro de una misma importación, además de los ya existentes en la BD.
    """
    if valor is None or not str(valor).strip():
        return _resultado(None, None, "dni", "El DNI es obligatorio.")

    dni = _DNI_SEPARATOR_RE.sub("", str(valor).strip())
    if not re.fullmatch(r"[0-9]+", dni):
        return _resultado(None, None, "dni", "El DNI debe contener solo dígitos.")
    if dni_existente or (dnis_del_lote is not None and dni in dnis_del_lote):
        return _resultado(None, "ERR_01_DNI_DUP", "dni", "El DNI ya existe en la base o está repetido en la fuente.")
    if dnis_del_lote is not None:
        dnis_del_lote.add(dni)
    return ResultadoValidacion(dni)


def normalizar_nombre(valor: Any, campo: str) -> ResultadoValidacion:
    """Recorta, capitaliza y limita a 50 caracteres el nombre o apellido."""
    texto = "" if valor is None else str(valor).strip()
    if not texto:
        return _resultado(None, None, campo, f"{campo.capitalize()} no puede estar vacío.")
    if len(texto) > 50:
        return _resultado(None, None, campo, f"{campo.capitalize()} no puede superar 50 caracteres.")
    return ResultadoValidacion(texto.title())


def separar_nombre_completo(valor: Any) -> ResultadoValidacion:
    """Convierte ``APELLIDO, Nombre`` en campos apellido y nombre."""
    texto = "" if valor is None else str(valor).strip()
    partes = [parte.strip() for parte in texto.split(",", maxsplit=1)]
    if len(partes) != 2 or not all(partes):
        return _resultado(None, None, "nombre", "Use el formato 'Apellido, Nombre'.")
    apellido = normalizar_nombre(partes[0], "apellido")
    nombre = normalizar_nombre(partes[1], "nombre")
    errores = apellido.errores + nombre.errores
    if errores:
        return ResultadoValidacion(None, errores)
    return ResultadoValidacion({"apellido": apellido.valor, "nombre": nombre.valor})


def normalizar_fecha(valor: Any, *, campo: str, no_futura: bool = False) -> ResultadoValidacion:
    """Acepta ISO y dos formatos históricos; devuelve ``date``."""
    if isinstance(valor, datetime):
        fecha = valor.date()
    elif isinstance(valor, date):
        fecha = valor
    else:
        texto = "" if valor is None else str(valor).strip()
        fecha = None
        for formato in _DATE_FORMATS:
            try:
                fecha = datetime.strptime(texto, formato).date()
                break
            except ValueError:
                continue
        if fecha is None:
            return _resultado(None, "ERR_03_DATE_INVALID", campo, "La fecha no tiene un formato válido (AAAA-MM-DD).")
    if no_futura and fecha > date.today():
        return _resultado(None, "ERR_03_DATE_INVALID", campo, "La fecha no puede ser posterior a hoy.")
    return ResultadoValidacion(fecha)


def normalizar_email(valor: Any, *, obligatorio: bool = False) -> ResultadoValidacion:
    """Recorta y pasa a minúsculas; un correo vacío es válido si es opcional."""
    correo = "" if valor is None else str(valor).strip().lower()
    if not correo and not obligatorio:
        return ResultadoValidacion(None)
    if not correo or not _EMAIL_RE.fullmatch(correo):
        return _resultado(None, "ERR_05_EMAIL_INVALID", "email", "El e-mail no cumple el formato esperado.")
    return ResultadoValidacion(correo)


def normalizar_nota(valor: Any) -> ResultadoValidacion:
    """Acepta coma o punto decimal, con rango 1–10 y hasta dos decimales."""
    texto = "" if valor is None else str(valor).strip().replace(",", ".")
    try:
        nota = Decimal(texto)
    except (InvalidOperation, ValueError):
        return _resultado(None, "ERR_04_NOTA_OUT_RANGE", "nota", "La nota debe ser un número entre 1 y 10.")
    if not nota.is_finite() or nota < 1 or nota > 10 or nota.as_tuple().exponent < -2:
        return _resultado(None, "ERR_04_NOTA_OUT_RANGE", "nota", "La nota debe estar entre 1 y 10, con hasta dos decimales.")
    return ResultadoValidacion(nota.quantize(Decimal("0.01")))


def validar_referencia(existe: bool, *, campo: str, descripcion: str) -> ResultadoValidacion:
    """Valida una FK/código maestro (materia, alumno u otra referencia)."""
    if not existe:
        return _resultado(None, "ERR_02_FK_NOTFOUND", campo, f"No existe la referencia: {descripcion}.")
    return ResultadoValidacion(True)


def validar_correlativas(faltantes: Iterable[str]) -> ResultadoValidacion:
    faltantes = tuple(faltantes)
    if faltantes:
        detalle = ", ".join(faltantes)
        return _resultado(None, "ERR_06_CORRELATIVA", "inscripcion", f"Faltan correlativas aprobadas: {detalle}.")
    return ResultadoValidacion(True)


def validar_asignacion_docente(asignado: bool) -> ResultadoValidacion:
    if not asignado:
        return _resultado(None, "ERR_07_PERMISO", "id_materia", "El docente no tiene asignada esta materia para el ciclo lectivo.")
    return ResultadoValidacion(True)


def validar_columnas_plantilla(
    recibidas: Iterable[str],
    esperadas: Iterable[str],
) -> ResultadoValidacion:
    """Rechaza la plantilla completa si cambian, faltan o sobran columnas."""
    recibidas = tuple(str(c).strip() for c in recibidas)
    esperadas = tuple(str(c).strip() for c in esperadas)
    if recibidas != esperadas:
        faltantes = [c for c in esperadas if c not in recibidas]
        adicionales = [c for c in recibidas if c not in esperadas]
        detalle = []
        if faltantes:
            detalle.append("faltan: " + ", ".join(faltantes))
        if adicionales:
            detalle.append("sobran: " + ", ".join(adicionales))
        if not detalle:
            detalle.append("el orden de las columnas no coincide")
        return _resultado(None, "ERR_08_PLANTILLA", "plantilla", "Formato de plantilla incorrecto (" + "; ".join(detalle) + ").")
    return ResultadoValidacion(True)


def combinar_errores(*resultados: ResultadoValidacion) -> tuple[ErrorValidacion, ...]:
    """Aplana los errores de varios campos para un reporte por fila."""
    return tuple(error for resultado in resultados for error in resultado.errores)
