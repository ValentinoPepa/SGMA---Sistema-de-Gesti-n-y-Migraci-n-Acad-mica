"""Disposable MariaDB/MySQL benchmark for SGMA migration and audit triggers.

Creates isolated schemas from the project DDL, applies the same ETL dataset
with/without the acta INSERT audit trigger, performs a concurrent write/read
workload, and drops every schema it created.
"""

from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
import csv
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import mysql.connector


ROOT = Path(__file__).resolve().parents[2]
DDL_FILE = ROOT / "Fase 2 Diseño y Base de Datos" / "gestion_academica.sql"
CODE_DIR = ROOT / "Fase 3 Implementación y Desarrollo" / "codigo"
MYSQL_CLI = Path(os.getenv("MYSQL_CLI", r"C:\xampp\mysql\bin\mysql.exe"))


def connection(database: str | None = None):
    return mysql.connector.connect(
        host=os.getenv("SGMA_DB_HOST", "127.0.0.1"),
        port=int(os.getenv("SGMA_DB_PORT", "3306")),
        user=os.getenv("SGMA_DB_USER", "root"),
        password=os.getenv("SGMA_DB_PASSWORD", ""),
        database=database,
        connection_timeout=10,
        autocommit=False,
    )


def run_ddl(database: str, triggers_on: bool) -> None:
    ddl = DDL_FILE.read_bytes().replace(b"gestion_academica", database.encode("ascii"))
    if not triggers_on:
        ddl += b"\nDROP TRIGGER trg_actas_ai;\n"
    command = [
        str(MYSQL_CLI),
        "--batch",
        f"--host={os.getenv('SGMA_DB_HOST', '127.0.0.1')}",
        f"--port={os.getenv('SGMA_DB_PORT', '3306')}",
        f"--user={os.getenv('SGMA_DB_USER', 'root')}",
        "--default-character-set=utf8mb4",
    ]
    env = os.environ.copy()
    password = os.getenv("SGMA_DB_PASSWORD", "")
    if password:
        env["MYSQL_PWD"] = password
    result = subprocess.run(command, input=ddl, capture_output=True, env=env)
    if result.returncode:
        raise RuntimeError(
            "No se pudo crear el esquema de benchmark: "
            + result.stderr.decode(errors="replace")[-3000:]
        )


def apply_etl(database: str, log_path: Path, acts_override: int | None = None) -> float:
    os.environ["SGMA_DB_HOST"] = os.getenv("SGMA_DB_HOST", "127.0.0.1")
    os.environ["SGMA_DB_USER"] = os.getenv("SGMA_DB_USER", "root")
    os.environ["SGMA_DB_PORT"] = os.getenv("SGMA_DB_PORT", "3306")
    os.environ["SGMA_DB_NAME"] = database
    if not os.getenv("SGMA_DB_PASSWORD"):
        os.environ.pop("SGMA_DB_PASSWORD", None)
    if str(CODE_DIR) not in sys.path:
        sys.path.insert(0, str(CODE_DIR))
    from sgma.etl import ARCHIVO_ACTAS, aplicar, preparar
    from sgma.errores import RegistroErrores

    errores = RegistroErrores()
    alumnos, carreras, materias, actas = preparar(errores)
    with ARCHIVO_ACTAS.open("r", encoding="utf-8-sig", newline="") as source:
        total_actas = sum(1 for _ in csv.DictReader(source))
    if acts_override is not None:
        if not actas:
            raise RuntimeError("No hay actas válidas para generar el ensayo escalado")
        actas = [
            {**actas[index % len(actas)], "libro": "C4", "folio": f"{index + 1:06d}"}
            for index in range(acts_override)
        ]
        total_actas = acts_override
    start = time.perf_counter()
    aplicar(alumnos, carreras, materias, actas, total_actas, errores)
    elapsed = time.perf_counter() - start
    errores.guardar(log_path)
    return elapsed


def baseline_counts(database: str) -> dict[str, int | str]:
    db = connection(database)
    try:
        cur = db.cursor()
        cur.execute("SELECT VERSION()")
        version = cur.fetchone()[0]
        counts: dict[str, int | str] = {"version": version}
        for table in ("alumnos", "carreras", "materias", "actas_examen"):
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(*) FROM auditoria "
            "WHERE tabla = 'actas_examen' AND operacion = 'INSERT'"
        )
        counts["audit_insert_actas"] = cur.fetchone()[0]
        cur.execute(
            "SELECT id_lote FROM lotes_carga "
            "WHERE tipo = 'MIGRACION' AND entidad = 'actas_examen' LIMIT 1"
        )
        row = cur.fetchone()
        if not row:
            raise RuntimeError(f"No se encontró el lote ETL en {database}")
        counts["lote_id"] = row[0]
        cur.close()
        return counts
    finally:
        db.close()


def concurrent_workload(database: str, workers: int, rows_each: int) -> dict[str, float | int]:
    info = baseline_counts(database)
    lote_id = int(info["lote_id"])
    insert_latencies: list[float] = []
    read_latencies: list[float] = []

    def worker(worker_id: int) -> tuple[float, list[float], list[float]]:
        db = connection(database)
        cur = db.cursor()
        local_latencies: list[float] = []
        local_read_latencies: list[float] = []
        start = time.perf_counter()
        try:
            for row_index in range(rows_each):
                alumno_id = 1 + ((worker_id * rows_each + row_index) % int(info["alumnos"]))
                materia_id = 1 + ((worker_id * rows_each + row_index) % int(info["materias"]))
                read_start = time.perf_counter()
                cur.execute(
                    "SELECT COUNT(*) FROM actas_examen WHERE id_alumno = %s",
                    (alumno_id,),
                )
                cur.fetchone()
                local_read_latencies.append((time.perf_counter() - read_start) * 1000)
                sql_start = time.perf_counter()
                cur.execute(
                    "INSERT INTO actas_examen "
                    "(id_alumno,id_materia,id_mesa,fecha_examen,libro,folio,nota,estado,origen,id_lote) "
                    "VALUES (%s,%s,NULL,'2026-10-01',%s,%s,6.50,'APROBADO','MASIVA',%s)",
                    (alumno_id, materia_id, f"C4-{worker_id:02d}", f"{row_index + 1:04d}", lote_id),
                )
                local_latencies.append((time.perf_counter() - sql_start) * 1000)
            db.commit()
            return time.perf_counter() - start, local_latencies, local_read_latencies
        except Exception:
            db.rollback()
            raise
        finally:
            cur.close()
            db.close()

    wall_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(worker, idx) for idx in range(workers)]
        worker_results = [future.result() for future in futures]
    wall_seconds = time.perf_counter() - wall_start
    for _, latencies, reads in worker_results:
        insert_latencies.extend(latencies)
        read_latencies.extend(reads)
    transactions = [duration for duration, _, _ in worker_results]
    return {
        "workers": workers,
        "rows": workers * rows_each,
        "wall_seconds": wall_seconds,
        "throughput_rows_s": (workers * rows_each) / wall_seconds,
        "worker_tx_p50_ms": statistics.median(transactions) * 1000,
        "worker_tx_max_ms": max(transactions) * 1000,
        "insert_p50_ms": statistics.median(insert_latencies),
        "insert_p95_ms": sorted(insert_latencies)[int(0.95 * (len(insert_latencies) - 1))],
        "read_p50_ms": statistics.median(read_latencies),
        "read_p95_ms": sorted(read_latencies)[int(0.95 * (len(read_latencies) - 1))],
    }


def drop_schema(database: str) -> None:
    if not database.startswith("sgma_c4_"):
        raise ValueError(f"Refusing to drop a non-benchmark schema: {database}")
    db = connection()
    try:
        cur = db.cursor()
        cur.execute(f"DROP DATABASE IF EXISTS `{database}`")
        db.commit()
        cur.close()
    finally:
        db.close()


def main() -> int:
    runs = int(os.getenv("C4_RUNS", "5"))
    workers = int(os.getenv("C4_WORKERS", "10"))
    rows_each = int(os.getenv("C4_ROWS_PER_WORKER", "20"))
    etl_acts = int(os.getenv("C4_ETL_ACTS", "189"))
    if not MYSQL_CLI.is_file():
        raise SystemExit(f"No se encontró mysql.exe: {MYSQL_CLI}; configure MYSQL_CLI.")
    names: list[str] = []
    observations: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="sgma-c4-") as temp:
        try:
            for trial in range(1, runs + 1):
                pair: dict[str, dict] = {}
                order = ("on", "off") if trial % 2 else ("off", "on")
                for mode in order:
                    database = f"sgma_c4_{os.getpid()}_{trial}_{mode}"
                    names.append(database)
                    run_ddl(database, triggers_on=(mode == "on"))
                    etl_seconds = apply_etl(
                        database,
                        Path(temp) / f"{trial}_{mode}_etl.log",
                        None if etl_acts == 189 else etl_acts,
                    )
                    counts = baseline_counts(database)
                    expected_audit = etl_acts if mode == "on" else 0
                    if (
                        counts["alumnos"] != 80
                        or counts["carreras"] != 2
                        or counts["materias"] != 24
                        or counts["actas_examen"] != etl_acts
                        or counts["audit_insert_actas"] != expected_audit
                    ):
                        raise RuntimeError(
                            f"Conteos inesperados en {database}: {counts}"
                        )
                    concurrent = concurrent_workload(database, workers, rows_each)
                    counts_after = baseline_counts(database)
                    expected_after = etl_acts + workers * rows_each
                    expected_audit_after = expected_audit + (
                        workers * rows_each if mode == "on" else 0
                    )
                    if (
                        counts_after["actas_examen"] != expected_after
                        or counts_after["audit_insert_actas"] != expected_audit_after
                    ):
                        raise RuntimeError(
                            f"Conteos concurrentes inesperados en {database}: {counts_after}"
                        )
                    pair[mode] = {
                        "etl_seconds": etl_seconds,
                        "counts_before_concurrency": counts,
                        "counts_after_concurrency": counts_after,
                        "concurrency": concurrent,
                    }
                pair["trigger_overhead_percent"] = (
                    (pair["on"]["etl_seconds"] - pair["off"]["etl_seconds"])
                    / pair["off"]["etl_seconds"]
                    * 100
                )
                observations.append(pair)
        finally:
            for database in reversed(names):
                drop_schema(database)

    on_times = [item["on"]["etl_seconds"] for item in observations]
    off_times = [item["off"]["etl_seconds"] for item in observations]
    overhead = [item["trigger_overhead_percent"] for item in observations]
    paired_overheads = [item["trigger_overhead_percent"] for item in observations]
    report = {
        "server": observations[-1]["on"]["counts_before_concurrency"]["version"],
        "runs": runs,
        "etl_actas_per_run": etl_acts,
        "etl_baseline_dataset": {
            "students": 80,
            "programs": 2,
            "subjects": 24,
            "acts": etl_acts,
            "audit_events_with_trigger": etl_acts,
            "audit_events_without_insert_trigger": 0,
        },
        "etl_seconds_with_audit_trigger_median": statistics.median(on_times),
        "etl_seconds_with_audit_trigger_range": [min(on_times), max(on_times)],
        "etl_seconds_without_acta_insert_trigger_median": statistics.median(off_times),
        "etl_seconds_without_acta_insert_trigger_range": [min(off_times), max(off_times)],
        "etl_trigger_overhead_percent_median": statistics.median(paired_overheads),
        "etl_trigger_overhead_percent_range": [min(paired_overheads), max(paired_overheads)],
        "concurrency": {
            "workers": workers,
            "rows_per_worker": rows_each,
            "total_rows_per_run": workers * rows_each,
            "with_trigger_median_wall_seconds": statistics.median(
                item["on"]["concurrency"]["wall_seconds"] for item in observations
            ),
            "without_trigger_median_wall_seconds": statistics.median(
                item["off"]["concurrency"]["wall_seconds"] for item in observations
            ),
            "with_trigger_median_throughput_rows_s": statistics.median(
                item["on"]["concurrency"]["throughput_rows_s"] for item in observations
            ),
            "without_trigger_median_throughput_rows_s": statistics.median(
                item["off"]["concurrency"]["throughput_rows_s"] for item in observations
            ),
            "with_trigger_insert_p95_ms_median": statistics.median(
                item["on"]["concurrency"]["insert_p95_ms"] for item in observations
            ),
            "without_trigger_insert_p95_ms_median": statistics.median(
                item["off"]["concurrency"]["insert_p95_ms"] for item in observations
            ),
            "with_trigger_read_p95_ms_median": statistics.median(
                item["on"]["concurrency"]["read_p95_ms"] for item in observations
            ),
            "without_trigger_read_p95_ms_median": statistics.median(
                item["off"]["concurrency"]["read_p95_ms"] for item in observations
            ),
        },
        "per_run": [
            {
                "on_etl_seconds": item["on"]["etl_seconds"],
                "off_etl_seconds": item["off"]["etl_seconds"],
                "paired_trigger_overhead_percent": item["trigger_overhead_percent"],
                "on_concurrency_seconds": item["on"]["concurrency"]["wall_seconds"],
                "off_concurrency_seconds": item["off"]["concurrency"]["wall_seconds"],
                "on_concurrency_insert_p95_ms": item["on"]["concurrency"]["insert_p95_ms"],
                "off_concurrency_insert_p95_ms": item["off"]["concurrency"]["insert_p95_ms"],
            }
            for item in observations
        ],
        "temporary_schemas_removed": names,
    }
    serialized = json.dumps(report, indent=2)
    result_file = os.getenv("C4_RESULT_FILE")
    if result_file:
        Path(result_file).write_text(serialized + "\n", encoding="utf-8")
    print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
