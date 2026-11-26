"""Resolución opcional de rutas sin acoplar el arranque a la estructura de fases."""

from __future__ import annotations

import os
from pathlib import Path


def buscar_carpeta_v11_opcional(origen: Path | None = None) -> Path | None:
    """Devuelve la raíz del proyecto si existen las carpetas de fases, o ``None``."""
    inicio = (origen or Path(__file__)).resolve()
    for carpeta in (inicio, *inicio.parents):
        if (
            (carpeta / "Fase 2 Diseño y Base de Datos").is_dir()
            and (carpeta / "Fase 3 Implementación y Desarrollo").is_dir()
        ):
            return carpeta
    return None


def buscar_carpeta_v11(origen: Path | None = None) -> Path:
    """Encuentra la raíz de v1.1 aunque el código esté agrupado por fases."""
    carpeta = buscar_carpeta_v11_opcional(origen)
    if carpeta is not None:
        return carpeta
    raise FileNotFoundError("No se encontró la raíz del proyecto con sus fases 2 y 3.")


def resolver_carpeta_plantillas(origen: Path | None = None) -> Path | None:
    """Resuelve la carpeta de plantillas sin requerir las planillas legadas."""
    desde_entorno = os.getenv("SGMA_PLANTILLAS_DIR", "").strip()
    if desde_entorno:
        ruta = Path(desde_entorno).expanduser().resolve()
        if ruta.is_dir():
            return ruta
    local = (origen or Path(__file__)).resolve().parent / "plantillas"
    if local.is_dir():
        return local
    raiz = buscar_carpeta_v11_opcional(origen)
    if raiz is not None:
        fase2 = raiz / "Fase 2 Diseño y Base de Datos"
        if fase2.is_dir():
            return fase2
    return None


def resolver_directorio_fuentes(origen: Path | None = None) -> Path:
    """Resuelve la carpeta de fuentes ETL sin fallar si no existen las carpetas de fases."""
    desde_entorno = os.getenv("SGMA_FUENTES_DIR", "").strip()
    if desde_entorno:
        return Path(desde_entorno).expanduser().resolve()
    raiz = buscar_carpeta_v11_opcional(origen)
    if raiz is not None:
        return raiz
    return Path.cwd().resolve()
