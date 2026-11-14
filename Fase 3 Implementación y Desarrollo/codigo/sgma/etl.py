"""Migración inicial de planillas heredadas al esquema MySQL del SGMA.

La ejecución predeterminada es una vista previa sin conexiones ni escrituras.
Para aplicar cambios se requiere ``--apply`` y las variables SGMA_DB_*.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import unicodedata
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from .errores import RegistroErrores
from .rutas import buscar_carpeta_v11
from .validaciones import (
    normalizar_dni,
    normalizar_email,
    normalizar_fecha,
    normalizar_nombre,
    normalizar_nota,
    separar_nombre_completo,
)


BASE_V11 = buscar_carpeta_v11()
DIRECTORIO_FUENTES = Path(os.getenv("SGMA_FUENTES_DIR", BASE_V11)).expanduser().resolve()
ARCHIVO_ALUMNOS = DIRECTORIO_FUENTES / "Alumnos_2026_Final.xlsx"
ARCHIVO_PLAN = DIRECTORIO_FUENTES / "Plan_Estudios.xlsx"
ARCHIVO_ACTAS = DIRECTORIO_FUENTES / "Actas_Historicas.csv"
LOG_DEFAULT = Path(__file__).resolve().parents[1] / "errores_migracion.log"


def _texto(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _clave(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).strip().casefold()


def _codigo_materia(valor: Any) -> str:
    return re.sub(r"[\s-]+", "", _texto(valor)).upper()


def _anio_nivel(valor: Any) -> int | None:
    match = re.search(r"[1-5]", _texto(valor))
    return int(match.group()) if match else None


def _legajo_legacy(valor: Any) -> int | None:
    if isinstance(valor, int) and not isinstance(valor, bool):
        return valor if valor >= 0 else None
    if isinstance(valor, float) and valor.is_integer():
        return int(valor) if valor >= 0 else None
    digitos = re.sub(r"\D", "", _texto(valor))
    return int(digitos) if digitos else None


def _registros_excel(archivo: Path, hoja: str) -> list[tuple[int, dict[str, Any]]]:
    libro = load_workbook(archivo, read_only=True, data_only=True)
    try:
        ws = libro[hoja]
        filas = ws.iter_rows(values_only=True)
        encabezados = [str(valor).strip() if valor is not None else "" for valor in next(filas)]
        return [
            (numero, dict(zip(encabezados, fila)))
            for numero, fila in enumerate(filas, start=2)
            if any(valor is not None for valor in fila)
        ]
    finally:
        libro.close()


def transformar_alumnos(archivo: Path, errores: RegistroErrores) -> list[dict[str, Any]]:
    salida: list[dict[str, Any]] = []
    dnis: set[str] = set()
    legajos: set[int] = set()
    registros = _registros_excel(archivo, "Hoja1")
    legajos_origen = [_legajo_legacy(registro.get("Legajo_Old")) for _, registro in registros]
    proximo_legajo = max((valor for valor in legajos_origen if valor is not None), default=0) + 1

    for fila, registro in registros:
        dni = normalizar_dni(registro.get("Documento"))
        if not dni.valido:
            for error in dni.errores:
                errores.agregar(archivo.name, fila, error.campo, error.codigo, error.mensaje)
            continue
        if dni.valor in dnis:
            errores.agregar(archivo.name, fila, "dni", "ERR_01_DNI_DUP", "El DNI está repetido en la fuente; se omitió la fila.")
            continue

        persona = separar_nombre_completo(registro.get("Nombre_Y_Apellido"))
        if persona.valido:
            apellido, nombre = persona.valor["apellido"], persona.valor["nombre"]
        else:
            # En nombres sin coma se interpreta el primer término como nombre y
            # el resto como apellido, según el formato legado definido en el diccionario.
            partes = _texto(registro.get("Nombre_Y_Apellido")).split()
            if len(partes) < 2:
                errores.agregar(archivo.name, fila, "nombre", None, "No se puede separar el nombre y el apellido.")
                continue
            nombre_resultado = normalizar_nombre(partes[0], "nombre")
            apellido_resultado = normalizar_nombre(" ".join(partes[1:]), "apellido")
            if not nombre_resultado.valido or not apellido_resultado.valido:
                errores.agregar(archivo.name, fila, "nombre", None, "Nombre o apellido vacío o mayor a 50 caracteres.")
                continue
            nombre, apellido = nombre_resultado.valor, apellido_resultado.valor

        dnis.add(dni.valor)

        legajo = _legajo_legacy(registro.get("Legajo_Old"))
        if legajo is None or legajo in legajos:
            while proximo_legajo in legajos:
                proximo_legajo += 1
            legajo = proximo_legajo
            proximo_legajo += 1
        legajos.add(legajo)

        fecha_resultado = normalizar_fecha(registro.get("Fecha_Nac"), campo="fecha_nacimiento")
        fecha_nacimiento = fecha_resultado.valor if fecha_resultado.valido else None
        if not fecha_resultado.valido:
            for error in fecha_resultado.errores:
                errores.agregar(archivo.name, fila, error.campo, error.codigo, error.mensaje)

        email_resultado = normalizar_email(registro.get("E-mail"))
        email = email_resultado.valor if email_resultado.valido else None
        if not email_resultado.valido:
            for error in email_resultado.errores:
                errores.agregar(archivo.name, fila, error.campo, error.codigo, error.mensaje)

        salida.append({
            "legajo": legajo,
            "dni": dni.valor,
            "apellido": apellido,
            "nombre": nombre,
            "fecha_nacimiento": fecha_nacimiento,
            "email": email,
        })
    return salida


def transformar_plan(archivo: Path, errores: RegistroErrores) -> tuple[list[str], list[dict[str, Any]]]:
    carreras: dict[str, str] = {}
    materias: dict[str, dict[str, Any]] = {}
    for fila, registro in _registros_excel(archivo, "Materias"):
        carrera = re.sub(r"\s+", " ", _texto(registro.get("Nom_Carrera"))).strip().title()
        codigo = _codigo_materia(registro.get("Cod_Mat"))
        nombre = re.sub(r"\s+", " ", _texto(registro.get("Nombre_Materia"))).strip().title()
        anio = _anio_nivel(registro.get("Año_Cursada"))
        if not carrera or not codigo or not nombre or anio is None:
            errores.agregar(archivo.name, fila, "materia", None, "Carrera, código, nombre o año inválido; se omitió la fila.")
            continue
        carreras[_clave(carrera)] = carrera
        if codigo in materias:
            errores.agregar(archivo.name, fila, "Cod_Mat", None, "Materia duplicada en la fuente; se conserva la primera aparición.")
            continue
        materias[codigo] = {"carrera": carrera, "codigo": codigo, "nombre": nombre, "anio_nivel": anio}
    return list(carreras.values()), list(materias.values())


def transformar_actas(archivo: Path, dnis: set[str], codigos: set[str], errores: RegistroErrores) -> list[dict[str, Any]]:
    estados = {
        "APROBADO": "APROBADO", "AP": "APROBADO", "PROM": "APROBADO",
        "DESAPROBADO": "DESAPROBADO", "DES": "DESAPROBADO",
        "AUSENTE": "AUSENTE", "A": "AUSENTE",
    }
    salida: list[dict[str, Any]] = []
    with archivo.open("r", encoding="utf-8-sig", newline="") as origen:
        for fila, registro in enumerate(csv.DictReader(origen), start=2):
            dni = normalizar_dni(registro.get("DNI_Alumno"))
            codigo = _codigo_materia(registro.get("Cod_Materia"))
            if not dni.valido:
                errores.agregar(archivo.name, fila, "DNI_Alumno", "ERR_01_DNI_DUP" if dni.errores and dni.errores[0].codigo else None, "DNI de acta inválido.")
                continue
            if dni.valor not in dnis or codigo not in codigos:
                faltante = "alumno" if dni.valor not in dnis else "materia"
                errores.agregar(archivo.name, fila, faltante, "ERR_02_FK_NOTFOUND", f"No se encontró la referencia de {faltante}.")
                continue

            fecha = normalizar_fecha(registro.get("Fecha_Examen"), campo="fecha_examen", no_futura=True)
            if not fecha.valido:
                for error in fecha.errores:
                    errores.agregar(archivo.name, fila, error.campo, error.codigo, error.mensaje)
                continue

            condicion = estados.get(_texto(registro.get("Condición")).upper())
            nota_origen = _texto(registro.get("Nota_Final"))
            ausente = condicion == "AUSENTE" or nota_origen.upper() in {"A", "AUSENTE"}
            if ausente:
                nota = None
                condicion = "AUSENTE"
            else:
                resultado_nota = normalizar_nota(nota_origen)
                if not resultado_nota.valido or condicion is None:
                    mensaje = resultado_nota.errores[0].mensaje if resultado_nota.errores else "Condición de acta desconocida."
                    codigo_error = resultado_nota.errores[0].codigo if resultado_nota.errores else None
                    errores.agregar(archivo.name, fila, "nota/condicion", codigo_error, mensaje)
                    continue
                nota = resultado_nota.valor

            partes_libro_folio = _texto(registro.get("Libro_Folio")).split("-", maxsplit=1)
            if len(partes_libro_folio) != 2 or not all(partes_libro_folio):
                errores.agregar(archivo.name, fila, "Libro_Folio", None, "El campo debe tener formato libro-folio.")
                continue
            salida.append({
                "dni": dni.valor,
                "codigo_materia": codigo,
                "fecha_examen": fecha.valor,
                "libro": partes_libro_folio[0].strip(),
                "folio": partes_libro_folio[1].strip(),
                "nota": nota,
                "estado": condicion,
            })
    return salida


def preparar(errores: RegistroErrores) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]], list[dict[str, Any]]]:
    carreras, materias = transformar_plan(ARCHIVO_PLAN, errores)
    alumnos = transformar_alumnos(ARCHIVO_ALUMNOS, errores)
    dnis = {fila["dni"] for fila in alumnos}
    codigos = {fila["codigo"] for fila in materias}
    actas = transformar_actas(ARCHIVO_ACTAS, dnis, codigos, errores)
    return alumnos, carreras, materias, actas


def _conexion_mysql():
    try:
        import mysql.connector
    except ImportError as exc:
        raise RuntimeError("Falta mysql-connector-python. Instale las dependencias de codigo/requirements.txt.") from exc
    requeridas = ("SGMA_DB_HOST", "SGMA_DB_USER", "SGMA_DB_PASSWORD")
    faltantes = [nombre for nombre in requeridas if not os.getenv(nombre)]
    if faltantes:
        raise RuntimeError("Faltan variables de entorno: " + ", ".join(faltantes))
    return mysql.connector.connect(
        host=os.environ["SGMA_DB_HOST"],
        port=int(os.getenv("SGMA_DB_PORT", "3306")),
        user=os.environ["SGMA_DB_USER"],
        password=os.environ["SGMA_DB_PASSWORD"],
        database=os.getenv("SGMA_DB_NAME", "gestion_academica"),
        autocommit=False,
    )


def aplicar(alumnos: list[dict[str, Any]], carreras: list[str], materias: list[dict[str, Any]], actas: list[dict[str, Any]], total_actas: int, errores: RegistroErrores) -> None:
    """Aplica el lote en una transacción; ante una falla se revierte todo."""
    conexion = _conexion_mysql()
    try:
        cursor = conexion.cursor()
        try:
            cursor.execute(
                "SELECT id_lote FROM lotes_carga WHERE tipo = 'MIGRACION' AND entidad = 'actas_examen' AND archivo = %s LIMIT 1",
                (ARCHIVO_ACTAS.name,),
            )
            if cursor.fetchone():
                raise RuntimeError("Ya existe una migración de Actas_Historicas.csv; revise el lote antes de volver a ejecutarla.")

            cursor.execute("SELECT id_carrera, nombre FROM carreras")
            id_carreras = {_clave(nombre): id_ for id_, nombre in cursor.fetchall()}
            for carrera in carreras:
                if _clave(carrera) not in id_carreras:
                    cursor.execute("INSERT INTO carreras (nombre) VALUES (%s)", (carrera,))
                    id_carreras[_clave(carrera)] = cursor.lastrowid

            cursor.execute("SELECT id_materia, codigo FROM materias")
            id_materias = {codigo: id_ for id_, codigo in cursor.fetchall()}
            for materia in materias:
                if materia["codigo"] not in id_materias:
                    cursor.execute(
                        "INSERT INTO materias (id_carrera, codigo, nombre, anio_nivel) VALUES (%s, %s, %s, %s)",
                        (id_carreras[_clave(materia["carrera"])], materia["codigo"], materia["nombre"], materia["anio_nivel"]),
                    )
                    id_materias[materia["codigo"]] = cursor.lastrowid

            cursor.execute("SELECT id_alumno, legajo, dni FROM alumnos")
            por_dni = {dni: (id_, legajo) for id_, legajo, dni in cursor.fetchall()}
            legajos_existentes = {legajo for _, legajo in por_dni.values()}
            siguiente = max(legajos_existentes, default=0) + 1
            for alumno in alumnos:
                if alumno["dni"] in por_dni:
                    errores.agregar(ARCHIVO_ALUMNOS.name, 0, "dni", "ERR_01_DNI_DUP", "El DNI ya existe en la base; se omitió el alumno.")
                    continue
                legajo = alumno["legajo"]
                if legajo in legajos_existentes:
                    while siguiente in legajos_existentes:
                        siguiente += 1
                    legajo = siguiente
                    siguiente += 1
                cursor.execute(
                    "INSERT INTO alumnos (legajo, dni, nombre, apellido, fecha_nacimiento, email, origen) VALUES (%s, %s, %s, %s, %s, %s, 'MIGRACION')",
                    (legajo, alumno["dni"], alumno["nombre"], alumno["apellido"], alumno["fecha_nacimiento"], alumno["email"]),
                )
                por_dni[alumno["dni"]] = (cursor.lastrowid, legajo)
                legajos_existentes.add(legajo)

            cursor.execute(
                "INSERT INTO lotes_carga (tipo, entidad, archivo, filas_total, filas_ok, filas_error) VALUES ('MIGRACION', 'actas_examen', %s, %s, 0, 0)",
                (ARCHIVO_ACTAS.name, total_actas),
            )
            id_lote = cursor.lastrowid
            actas_ok = 0
            for acta in actas:
                id_alumno = por_dni.get(acta["dni"], (None, None))[0]
                id_materia = id_materias.get(acta["codigo_materia"])
                if id_alumno is None or id_materia is None:
                    errores.agregar(ARCHIVO_ACTAS.name, 0, "referencia", "ERR_02_FK_NOTFOUND", "No se encontró alumno o materia en la base.")
                    continue
                cursor.execute(
                    "INSERT INTO actas_examen (id_alumno, id_materia, fecha_examen, libro, folio, nota, estado, origen, id_lote) VALUES (%s, %s, %s, %s, %s, %s, %s, 'MIGRACION', %s)",
                    (id_alumno, id_materia, acta["fecha_examen"], acta["libro"], acta["folio"], acta["nota"], acta["estado"], id_lote),
                )
                actas_ok += 1
            cursor.execute(
                "UPDATE lotes_carga SET filas_ok = %s, filas_error = %s WHERE id_lote = %s",
                (actas_ok, max(0, total_actas - actas_ok), id_lote),
            )
            cursor.callproc("sp_sincronizar_legajo")
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
        finally:
            cursor.close()
    finally:
        conexion.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Migración inicial de datos heredados del SGMA.")
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--dry-run", action="store_true", help="prepara y valida los datos sin conectarse ni escribir en MySQL (predeterminado)")
    modo.add_argument("--apply", action="store_true", help="inserta datos en MySQL dentro de una transacción")
    parser.add_argument("--log", type=Path, default=LOG_DEFAULT, help="ruta del log de errores")
    args = parser.parse_args()

    errores = RegistroErrores()
    alumnos, carreras, materias, actas = preparar(errores)
    if args.apply:
        with ARCHIVO_ACTAS.open("r", encoding="utf-8-sig", newline="") as origen:
            total_actas = sum(1 for _ in csv.DictReader(origen))
        aplicar(alumnos, carreras, materias, actas, total_actas, errores)

    errores.guardar(args.log)
    print(f"Alumnos preparados: {len(alumnos)}")
    print(f"Carreras preparadas: {len(carreras)}")
    print(f"Materias preparadas: {len(materias)}")
    print(f"Actas preparadas: {len(actas)}")
    print(f"Errores registrados: {len(errores.errores)} ({args.log})")
    if not args.apply:
        print("Vista previa: no se modificó la base de datos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
