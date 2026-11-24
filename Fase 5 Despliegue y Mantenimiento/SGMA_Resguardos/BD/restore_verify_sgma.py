"""Restore one SGMA dump into a disposable schema and compare its structure/data."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import mysql.connector


MYSQL_CLI_DEFAULT = Path(r"C:\xampp\mysql\bin\mysql.exe")


def connect(database: str | None = None):
    return mysql.connector.connect(
        host=os.getenv("SGMA_DB_HOST", "127.0.0.1"),
        port=int(os.getenv("SGMA_DB_PORT", "3306")),
        user=os.getenv("SGMA_DB_USER", "root"),
        password=os.getenv("SGMA_DB_PASSWORD", ""),
        database=database,
        connection_timeout=10,
    )


def snapshot(database: str) -> dict:
    db = connect()
    try:
        cur = db.cursor()
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema=%s AND table_type='BASE TABLE' ORDER BY table_name",
            (database,),
        )
        tables = [row[0] for row in cur.fetchall()]
        counts = {}
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM `{database}`.`{table}`")
            counts[table] = cur.fetchone()[0]

        cur.execute(
            "SELECT trigger_name FROM information_schema.triggers "
            "WHERE trigger_schema=%s ORDER BY trigger_name",
            (database,),
        )
        triggers = [row[0] for row in cur.fetchall()]
        cur.execute(
            "SELECT routine_name, routine_type FROM information_schema.routines "
            "WHERE routine_schema=%s ORDER BY routine_name, routine_type",
            (database,),
        )
        routines = [tuple(row) for row in cur.fetchall()]
        cur.execute(
            "SELECT event_name FROM information_schema.events "
            "WHERE event_schema=%s ORDER BY event_name",
            (database,),
        )
        events = [row[0] for row in cur.fetchall()]
        cur.close()
        return {"tables": tables, "counts": counts, "triggers": triggers, "routines": routines, "events": events}
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Prueba de restauración aislada del SGMA")
    parser.add_argument("dump", type=Path, help="archivo .sql generado por mysqldump")
    parser.add_argument("--restore-schema", required=True, help="esquema temporal nuevo para restaurar")
    parser.add_argument("--mysql-cli", type=Path, default=MYSQL_CLI_DEFAULT)
    parser.add_argument("--source-schema", default="gestion_academica_v2")
    args = parser.parse_args()

    if not re.fullmatch(r"[A-Za-z0-9_]+", args.restore_schema):
        raise SystemExit("El nombre del esquema de restauración solo puede tener letras, números y guion bajo.")
    if args.restore_schema == args.source_schema:
        raise SystemExit("El esquema de restauración debe ser distinto del origen.")
    if not args.dump.is_file() or args.dump.stat().st_size == 0:
        raise SystemExit(f"El dump no existe o está vacío: {args.dump}")
    if not args.mysql_cli.is_file():
        raise SystemExit(f"No se encontró mysql.exe: {args.mysql_cli}")

    db = connect()
    try:
        cur = db.cursor()
        cur.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name=%s", (args.restore_schema,))
        if cur.fetchone():
            raise SystemExit(f"El esquema de prueba ya existe; no se modificó: {args.restore_schema}")
        cur.execute(f"CREATE DATABASE `{args.restore_schema}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        db.commit()
        cur.close()
    finally:
        db.close()

    ok = False
    try:
        source = snapshot(args.source_schema)
        cli_args = [
            str(args.mysql_cli),
            f"--host={os.getenv('SGMA_DB_HOST', '127.0.0.1')}",
            f"--port={os.getenv('SGMA_DB_PORT', '3306')}",
            f"--user={os.getenv('SGMA_DB_USER', 'root')}",
            "--default-character-set=utf8mb4",
            f"--database={args.restore_schema}",
        ]
        cli_env = os.environ.copy()
        password = os.getenv("SGMA_DB_PASSWORD", "")
        if password:
            cli_env["MYSQL_PWD"] = password
        restored = subprocess.run(
            cli_args,
            input=args.dump.read_bytes(),
            capture_output=True,
            env=cli_env,
        )
        if restored.returncode:
            detail = restored.stderr.decode(errors="replace")[-1200:]
            raise RuntimeError(f"mysql.exe no pudo restaurar el dump: {detail}")

        target = snapshot(args.restore_schema)
        differences = []
        for key in ("tables", "counts", "triggers", "routines", "events"):
            if source[key] != target[key]:
                differences.append(key)
        if differences:
            raise RuntimeError("La restauración difiere del origen en: " + ", ".join(differences))

        print(f"RESTAURACION_OK schema={args.restore_schema}")
        print(f"TABLES={len(target['tables'])} TRIGGERS={len(target['triggers'])} ROUTINES={len(target['routines'])} EVENTS={len(target['events'])}")
        for table in ("alumnos", "carreras", "materias", "actas_examen", "auditoria", "lotes_carga"):
            print(f"ROWS_{table.upper()}={target['counts'].get(table, 'N/A')}")
        ok = True
        return 0
    finally:
        cleanup = connect()
        try:
            cur = cleanup.cursor()
            cur.execute(f"DROP DATABASE IF EXISTS `{args.restore_schema}`")
            cleanup.commit()
            cur.close()
        finally:
            cleanup.close()
        print(f"RESTORE_TEST_SCHEMA_REMOVED={args.restore_schema}")
        if not ok:
            print("RESTORE_TEST_FAILED")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
