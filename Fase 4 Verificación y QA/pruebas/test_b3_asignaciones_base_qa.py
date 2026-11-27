"""B3 integration check: assign a teacher and enforce note access by subject/cycle.

Runs against the isolated gestion_academica_a1_qa MariaDB schema only. Test
assignments, enrollments, notes, cycle, and accounts are removed in finally.
"""
from __future__ import annotations
import os, secrets, sys
from pathlib import Path
import mysql.connector
from werkzeug.security import generate_password_hash

TARGET_DB = "gestion_academica_a1_qa"
def configure():
    if os.getenv("SGMA_DB_NAME", TARGET_DB) != TARGET_DB:
        raise RuntimeError(f"B3 solo permite {TARGET_DB}; se cancela.")
    os.environ["SGMA_DB_NAME"] = TARGET_DB
    os.environ.setdefault("SGMA_DB_HOST", "127.0.0.1")
    os.environ.setdefault("SGMA_DB_USER", "root")
    os.environ.setdefault("SGMA_DB_PASSWORD", "")
    os.environ.setdefault("SGMA_DB_PORT", "3306")
    os.environ.setdefault("SGMA_SECRET_KEY", secrets.token_urlsafe(32))

def connect():
    return mysql.connector.connect(host=os.environ["SGMA_DB_HOST"], port=int(os.environ["SGMA_DB_PORT"]),
        user=os.environ["SGMA_DB_USER"], password=os.environ.get("SGMA_DB_PASSWORD", ""),
        database=TARGET_DB, autocommit=False)

def fixture(tag):
    cn=connect(); cur=cn.cursor(); created={"users":[],"teacher":None,"cycle":None,"assignments":[],"enrollments":[]}
    try:
        cur.execute("SELECT VERSION(), DATABASE()"); version, db=cur.fetchone()
        if db != TARGET_DB: raise RuntimeError(f"Base inesperada: {db}")
        cur.execute("SELECT a.id_alumno, m1.id_materia, m1.codigo, m2.id_materia, m2.codigo "
            "FROM alumnos a JOIN materias m1 ON m1.activa=TRUE JOIN materias m2 "
            "ON m2.activa=TRUE AND m2.id_carrera=m1.id_carrera AND m2.id_materia<>m1.id_materia "
            "WHERE a.activo=TRUE ORDER BY a.id_alumno,m1.id_materia,m2.id_materia LIMIT 1")
        row=cur.fetchone()
        if not row: raise RuntimeError("QA necesita un alumno y dos materias activas de la misma carrera.")
        student, subject_a, code_a, subject_b, code_b=row
        cur.execute("SELECT anio FROM ciclos_lectivos"); used={int(x[0]) for x in cur.fetchall()}
        year=next((y for y in range(2090,2200) if y not in used),None)
        if year is None: raise RuntimeError("Sin a?o libre para ciclo de prueba.")
        cur.execute("INSERT INTO ciclos_lectivos(anio,fecha_inicio,fecha_fin) VALUES(%s,%s,%s)",(year,f"{year}-01-01",f"{year}-12-31")); created["cycle"]=int(cur.lastrowid)
        cur.execute("INSERT INTO docentes(nombre,apellido,dni,email) VALUES(%s,%s,%s,%s)",("Prueba","B3",str(800000000+secrets.randbelow(10000000)),None)); created["teacher"]=int(cur.lastrowid)
        cur.execute("SELECT id_rol,nombre FROM roles WHERE nombre IN ('PRECEPTOR','DOCENTE')")
        roles={name:int(rid) for rid,name in cur.fetchall()}
        if set(roles)!={"PRECEPTOR","DOCENTE"}: raise RuntimeError("Faltan roles PRECEPTOR/DOCENTE en QA.")
        for name, role, teacher_id in (("preceptor",roles["PRECEPTOR"],None),("docente",roles["DOCENTE"],created["teacher"])):
            cur.execute("INSERT INTO usuarios(username,password_hash,id_rol,id_docente) VALUES(%s,%s,%s,%s)",
                (f"b3_{name}_{tag}",generate_password_hash(secrets.token_urlsafe(20)),role,teacher_id))
            created["users"].append(int(cur.lastrowid))
        for subject in (subject_a,subject_b):
            cur.execute("INSERT INTO inscripciones(id_alumno,id_materia,id_ciclo) VALUES(%s,%s,%s)",(student,subject,created["cycle"]))
            created["enrollments"].append(int(cur.lastrowid))
        cn.commit()
        return str(version),student,int(subject_a),str(code_a),int(subject_b),str(code_b),year,created
    except Exception:
        cn.rollback(); raise
    finally: cur.close(); cn.close()

def cleanup(data):
    cn=connect()
    try:
        c=cn.cursor()
        for enrollment in data["enrollments"]:
            c.execute("DELETE FROM notas_cursada WHERE id_inscripcion=%s",(enrollment,))
            c.execute("DELETE FROM inscripciones WHERE id_inscripcion=%s",(enrollment,))
        for teacher in data["assignments"]:
            c.execute("DELETE FROM asignaciones_docentes WHERE id_docente=%s AND id_materia=%s AND id_ciclo=%s",teacher)
        if data["cycle"] is not None: c.execute("DELETE FROM ciclos_lectivos WHERE id_ciclo=%s",(data["cycle"],))
        if data["users"]: c.executemany("UPDATE usuarios SET activo=FALSE WHERE id_usuario=%s",[(uid,) for uid in data["users"]])
        if data["teacher"] is not None: c.execute("UPDATE docentes SET activo=FALSE WHERE id_docente=%s",(data["teacher"],))
        cn.commit()
    except Exception: cn.rollback(); raise
    finally: cn.close()

def main():
    configure(); project=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(next(project.glob("Fase 3*/codigo"))))
    tag=secrets.token_hex(5); data={"users":[],"teacher":None,"cycle":None,"assignments":[],"enrollments":[]}
    try:
        version,student,sub_a,code_a,sub_b,code_b,year,data=fixture(tag)
        from sgma.web import create_app
        app=create_app({"TESTING":True,"SECRET_KEY":secrets.token_urlsafe(32)})
        pre=app.test_client()
        with pre.session_transaction() as s: s["usuario_id"]=data["users"][0]; s["csrf"]="b3-token"
        page=pre.get("/asignaciones-docentes")
        if page.status_code!=200 or b"Nueva asignaci" not in page.data: raise RuntimeError("PRECEPTOR no ve formulario B3.")
        response=pre.post("/asignaciones-docentes",data={"csrf_token":"b3-token","id_docente":str(data["teacher"]),"id_materia":str(sub_a),"id_ciclo":str(data["cycle"])},follow_redirects=True)
        if response.status_code!=200 or "Docente asignado" not in response.get_data(as_text=True): raise RuntimeError("No se guard? la asignaci?n.")
        data["assignments"].append((data["teacher"],sub_a,data["cycle"]))
        teacher=app.test_client()
        with teacher.session_transaction() as s: s["usuario_id"]=data["users"][1]; s["csrf"]="b3-token"
        listed=teacher.get("/cursadas")
        if listed.status_code!=200 or code_a.encode() not in listed.data or code_b.encode() in listed.data: raise RuntimeError("DOCENTE no queda limitado a la materia asignada en la lista de cursadas.")
        note=teacher.post("/cursadas",data={"csrf_token":"b3-token","accion":"registrar_nota","id_inscripcion":str(data["enrollments"][0]),"instancia":"B3 test","nota":"8","fecha":"2026-11-26"},follow_redirects=True)
        if note.status_code!=200 or "Registro acad" not in note.get_data(as_text=True): raise RuntimeError("No se pudo guardar nota en materia asignada.")
        denied=teacher.post("/cursadas",data={"csrf_token":"b3-token","accion":"registrar_nota","id_inscripcion":str(data["enrollments"][1]),"instancia":"B3 test no autorizada","nota":"8","fecha":"2026-11-26"})
        if denied.status_code!=403: raise RuntimeError(f"La nota en otra materia no fue bloqueada: HTTP {denied.status_code}.")
        cn=connect()
        try:
            c=cn.cursor(); c.execute("SELECT COUNT(*) FROM notas_cursada WHERE id_inscripcion IN (%s,%s)",tuple(data["enrollments"]))
            count=int(c.fetchone()[0])
            if count!=1: raise RuntimeError(f"Qued? cantidad inesperada de notas de prueba: {count}.")
        finally: cn.close()
        print(f"Motor/base: {version} / {TARGET_DB}")
        print("PRECEPTOR: abre la pantalla y crea asignaci?n (HTTP 200)")
        print(f"DOCENTE: ve {code_a} asignada y no ve {code_b} no asignada")
        print("Nota en materia asignada: aceptada; nota en otra materia: HTTP 403")
        print("Resultado B3: CUMPLE")
        return 0
    finally: cleanup(data)
if __name__=="__main__": raise SystemExit(main())
