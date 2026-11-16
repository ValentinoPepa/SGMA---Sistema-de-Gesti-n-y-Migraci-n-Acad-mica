"""Mide el parseo y la transformación ETL con fuentes sintéticas, sin MySQL."""

from __future__ import annotations

import argparse
import csv
import os
import sys
import tempfile
import time
from pathlib import Path

from openpyxl import Workbook


def crear_plan(path: Path) -> None:
    libro = Workbook(write_only=True)
    hoja = libro.create_sheet("Materias")
    hoja.append(["Nom_Carrera", "Cod_Mat", "Nombre_Materia", "Año_Cursada"])
    hoja.append(["Sistemas", "SIS101", "Introduccion", "1"])
    libro.save(path)
    libro.close()


def crear_alumnos(path: Path, cantidad: int) -> None:
    libro = Workbook(write_only=True)
    hoja = libro.create_sheet("Hoja1")
    hoja.append(["Documento", "Nombre_Y_Apellido", "Fecha_Nac", "E-mail", "Legajo_Old"])
    for indice in range(cantidad):
        hoja.append([
            20_000_000 + indice,
            f"Apellido {indice}, Alumno {indice}",
            "2000-01-01",
            f"alumno{indice}@ejemplo.edu",
            100_000 + indice,
        ])
    libro.save(path)
    libro.close()


def crear_actas(path: Path, cantidad: int) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as archivo:
        writer = csv.writer(archivo)
        writer.writerow(["DNI_Alumno", "Cod_Materia", "Fecha_Examen", "Condición", "Nota_Final", "Libro_Folio"])
        for indice in range(cantidad):
            writer.writerow([20_000_000 + indice, "SIS101", "2024-06-10", "APROBADO", "8", f"1-{indice + 1}"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=50_000, help="filas sintéticas de alumnos y actas (predeterminado: 50000)")
    parser.add_argument("--max-seconds", type=float, default=600, help="límite RNF-02 en segundos (predeterminado: 600)")
    args = parser.parse_args()
    if args.rows < 1 or args.max_seconds <= 0:
        parser.error("--rows y --max-seconds deben ser positivos")

    with tempfile.TemporaryDirectory(prefix="sgma-benchmark-") as temporal:
        fuentes = Path(temporal)
        crear_plan(fuentes / "Plan_Estudios.xlsx")
        crear_alumnos(fuentes / "Alumnos_2026_Final.xlsx", args.rows)
        crear_actas(fuentes / "Actas_Historicas.csv", args.rows)

        os.environ["SGMA_FUENTES_DIR"] = str(fuentes)
        project_root = Path(__file__).resolve().parents[2]
        sys.path.insert(0, str(project_root / "Fase 3 Implementación y Desarrollo" / "codigo"))
        from sgma.errores import RegistroErrores
        from sgma.etl import preparar

        inicio = time.perf_counter()
        alumnos, carreras, materias, actas = preparar(RegistroErrores())
        transcurrido = time.perf_counter() - inicio

    correcto = len(alumnos) == args.rows and len(actas) == args.rows and len(carreras) == 1 and len(materias) == 1
    dentro_del_limite = transcurrido <= args.max_seconds
    print("Datos sintéticos; no se leyó ni escribió en una base MySQL.")
    print(f"Alumnos transformados: {len(alumnos)}")
    print(f"Actas transformadas: {len(actas)}")
    print(f"Carreras/materias transformadas: {len(carreras)}/{len(materias)}")
    print(f"Tiempo de parseo y transformación: {transcurrido:.2f} s (límite: {args.max_seconds:.0f} s)")
    print("Resultado: " + ("APROBADO para el ensayo local ETL" if correcto and dentro_del_limite else "REVISAR"))
    print("Nota: este benchmark no mide inserción MySQL, el panel web, consultas ni concurrencia.")
    return 0 if correcto and dentro_del_limite else 1


if __name__ == "__main__":
    raise SystemExit(main())
