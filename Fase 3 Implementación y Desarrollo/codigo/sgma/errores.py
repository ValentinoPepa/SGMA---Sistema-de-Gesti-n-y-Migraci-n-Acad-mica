"""Registro uniforme de errores de migración sin copiar datos personales."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class ErrorMigracion:
    archivo: str
    fila: int
    campo: str
    codigo: str
    mensaje: str


class RegistroErrores:
    """Acumula errores por fila y los escribe como log delimitado por tabuladores."""

    def __init__(self) -> None:
        self.errores: list[ErrorMigracion] = []

    def agregar(self, archivo: str, fila: int, campo: str, codigo: str | None, mensaje: str) -> None:
        self.errores.append(ErrorMigracion(archivo, fila, campo, codigo or "VALIDACION", mensaje))

    def guardar(self, destino: Path) -> None:
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("w", encoding="utf-8", newline="") as salida:
            writer = csv.writer(salida, delimiter="\t", lineterminator="\n")
            writer.writerow(("fecha_hora", "archivo", "fila", "campo", "codigo", "mensaje"))
            fecha = datetime.now().astimezone().isoformat(timespec="seconds")
            for error in self.errores:
                writer.writerow((fecha, error.archivo, error.fila, error.campo, error.codigo, error.mensaje))
