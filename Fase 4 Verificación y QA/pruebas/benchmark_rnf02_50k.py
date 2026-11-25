"""End-to-end C4/RNF-02 load benchmark, isolated to gestion_academica_rnf02.

Builds 50,000 valid synthetic historical-act rows from the local test fixtures,
then times the current ETL preparation, database writes and COMMIT. The runner
refuses any database other than the dedicated QA schema and refuses non-empty
business tables. It never drops data or disables audit triggers.
"""

from __future__ import annotations

import csv
import os
import shutil
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Any


TARGET_DB = "gestion_academica_rnf02"
DEFAULT_ROWS = 50_000


def source_directory() -> Path:
    configured = os.getenv("SGMA_ORIGINAL_FUENTES_DIR")
    if configured:
        candidate = Path(configured).expanduser().resolve()
        if all((candidate / name).is_file() for name in (
            "Alumnos_2026_Final.xlsx", "Plan_Estudios.xlsx", "Actas_Historicas.csv"
        )):
            return candidate
        raise FileNotFoundError("SGMA_ORIGINAL_FUENTES_DIR no contiene las tres fuentes esperadas.")

    downloads = Path.home() / "Downloads"
    candidates = [
        item.parent for item in downloads.rglob("Actas_Historicas.csv")
        if (item.parent / "Alumnos_2026_Final.xlsx").is_file()
        and (item.parent / "Plan_Estudios.xlsx").is_file()
    ]
    if len(candidates) != 1:
        raise FileNotFoundError(
            "No se pudo identificar una única carpeta fuente. Defina SGMA_ORIGINAL_FUENTES_DIR."
        )
    return candidates[0]


def connect_test_database():
    if os.getenv("SGMA_DB_NAME", TARGET_DB) != TARGET_DB:
        raise RuntimeError(f"Este benchmark solo admite la base aislada {TARGET_DB}.")
    try:
        import mysql.connector
    except ImportError as exc:
        raise RuntimeError("Falta mysql-connector-python en el Python usado para SGMA.") from exc
    return mysql.connector.connect(
        host=os.getenv("SGMA_DB_HOST", "127.0.0.1"),
        port=int(os.getenv("SGMA_DB_PORT", "3306")),
        user=os.getenv("SGMA_DB_USER", "root"),
        password=os.getenv("SGMA_DB_PASSWORD", ""),
        database=TARGET_DB,
        autocommit=False,
    )


def empty_schema_counts() -> dict[str, int]:
    connection = connect_test_database()
    try:
        cursor = connection.cursor()
        try:
            tables = ("alumnos", "carreras", "materias", "actas_examen", "lotes_carga", "auditoria")
            result: dict[str, int] = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                result[table] = int(cursor.fetchone()[0])
            cursor.execute("SELECT VERSION()")
            result["_version"] = cursor.fetchone()[0]
            return result
        finally:
            cursor.close()
    finally:
        connection.close()


def generate_actas(csv_path: Path, rows: int, temp_dir: Path, etl: Any) -> None:
    """Repeat only valid normalized actas, varying book/folio for each row."""
    errors = etl.RegistroErrores()
    _, materias = etl.transformar_plan(temp_dir / "Plan_Estudios.xlsx", errors)
    alumnos = etl.transformar_alumnos(temp_dir / "Alumnos_2026_Final.xlsx", errors)
    dnis = {row["dni"] for row in alumnos}
    codes = {row["codigo"] for row in materias}
    base_rows = etl.transformar_actas(csv_path, dnis, codes, errors)
    if len(base_rows) < 1:
        raise RuntimeError("La fuente no tiene actas válidas para formar la muestra sintética.")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
        fields = next(csv.reader(source))
    condition_field = next((field for field in fields if field.casefold().startswith("condici")), None)
    required = {"DNI_Alumno", "Cod_Materia", "Fecha_Examen", "Libro_Folio", "Nota_Final"}
    if not required.issubset(fields) or condition_field is None:
        raise RuntimeError("Los encabezados del CSV no coinciden con el formato heredado esperado.")

    with csv_path.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        for index in range(rows):
            source_row = base_rows[index % len(base_rows)]
            date_value = source_row["fecha_examen"]
            writer.writerow({
                "DNI_Alumno": source_row["dni"],
                "Cod_Materia": source_row["codigo_materia"],
                "Fecha_Examen": date_value.isoformat() if hasattr(date_value, "isoformat") else str(date_value),
                "Libro_Folio": f"C4RNF02-{index + 1:08d}",
                "Nota_Final": str(source_row["nota"]) if source_row["nota"] is not None else "AUSENTE",
                condition_field: source_row["estado"],
            })


def main() -> int:
    rows = int(os.getenv("C4_RNF02_ROWS", str(DEFAULT_ROWS)))
    if rows != DEFAULT_ROWS:
        raise RuntimeError(f"RNF-02 debe probar exactamente {DEFAULT_ROWS:,} registros en esta ejecución.")

    source = source_directory()
    code_dir = next(Path(__file__).resolve().parents[2].glob("Fase 3*/codigo"))
    sys.path.insert(0, str(code_dir))

    temp_dir = Path(tempfile.mkdtemp(prefix="sgma_rnf02_"))
    try:
        for name in ("Alumnos_2026_Final.xlsx", "Plan_Estudios.xlsx", "Actas_Historicas.csv"):
            shutil.copy2(source / name, temp_dir / name)
        os.environ["SGMA_FUENTES_DIR"] = str(temp_dir)
        os.environ["SGMA_DB_NAME"] = TARGET_DB
        os.environ.setdefault("SGMA_DB_HOST", "127.0.0.1")
        os.environ.setdefault("SGMA_DB_USER", "root")
        os.environ.setdefault("SGMA_DB_PASSWORD", "")
        os.environ.setdefault("SGMA_DB_PORT", "3306")

        from sgma import etl

        generate_actas(temp_dir / "Actas_Historicas.csv", rows, temp_dir, etl)

        baseline = empty_schema_counts()
        business_tables = ("alumnos", "carreras", "materias", "actas_examen", "lotes_carga", "auditoria")
        populated = {name: baseline[name] for name in business_tables if baseline[name] != 0}
        if populated:
            raise RuntimeError(
                "La base de prueba ya contiene datos; se cancela para evitar duplicarlos: "
                + ", ".join(f"{key}={value}" for key, value in populated.items())
            )

        errors = etl.RegistroErrores()
        start = time.perf_counter()
        alumnos, carreras, materias, actas = etl.preparar(errors)
        rejected_acta_errors = [e for e in errors.errores if e.archivo == "Actas_Historicas.csv"]
        if len(actas) != rows or rejected_acta_errors:
            raise RuntimeError(
                f"Preparación no válida: actas={len(actas)}, rechazos de acta={len(rejected_acta_errors)}."
            )
        etl.aplicar(alumnos, carreras, materias, actas, rows, errors)
        elapsed = time.perf_counter() - start

        connection = connect_test_database()
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM actas_examen")
            acta_count = int(cursor.fetchone()[0])
            cursor.execute(
                "SELECT filas_total, filas_ok, filas_error FROM lotes_carga "
                "WHERE tipo='MIGRACION' AND entidad='actas_examen' AND archivo='Actas_Historicas.csv'"
            )
            lot = cursor.fetchone()
            cursor.execute(
                "SELECT COUNT(*) FROM auditoria WHERE tabla='actas_examen' AND operacion='INSERT'"
            )
            audit_count = int(cursor.fetchone()[0])
            cursor.close()
        finally:
            connection.close()

        if acta_count != rows or not lot or tuple(int(value) for value in lot) != (rows, rows, 0):
            raise RuntimeError(
                f"Verificación de escritura falló: actas={acta_count}, lote={lot}."
            )

        print(f"Motor: {baseline['_version']}")
        print(f"Base aislada: {TARGET_DB}")
        print(f"Actas válidas preparadas: {len(actas):,}")
        print(f"Actas escritas: {acta_count:,}")
        print(f"Lote (total/ok/error): {lot[0]}/{lot[1]}/{lot[2]}")
        print(f"Eventos de auditoría de acta: {audit_count:,}")
        print(f"Errores de validación de fuentes auxiliares: {len(errors.errores)}")
        print(f"Tiempo ETL (preparación + escritura + COMMIT): {elapsed:.3f} s")
        print(f"Rendimiento ETL: {rows / elapsed:.1f} registros/s")
        print("Objetivo RNF-02: menos de 600 s")
        print("Resultado: CUMPLE" if elapsed < 600 else "Resultado: NO CUMPLE")
        if audit_count != rows:
            print("Nota: verificar el conteo de auditoría; no coincide con las actas escritas.")
        return 0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
