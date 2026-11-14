"""Resolución de rutas de los archivos compartidos de v1.1."""

from pathlib import Path


def buscar_carpeta_v11(origen: Path | None = None) -> Path:
    """Encuentra la raíz de v1.1 aunque el código esté agrupado por fases."""
    inicio = (origen or Path(__file__)).resolve()
    for carpeta in (inicio, *inicio.parents):
        if (
            (carpeta / "Fase 2 Diseño y Base de Datos").is_dir()
            and (carpeta / "Fase 3 Implementación y Desarrollo").is_dir()
        ):
            return carpeta
    raise FileNotFoundError("No se encontró la raíz del proyecto con sus fases 2 y 3.")
