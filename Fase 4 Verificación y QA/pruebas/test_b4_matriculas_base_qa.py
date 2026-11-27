"""B4 integration check against isolated gestion_academica_a1_qa MariaDB."""
from __future__ import annotations
import os, secrets, sys
from pathlib import Path
import mysql.connector
from werkzeug.security import generate_password_hash
TARGET_DB="gestion_academica_a1_qa"
def configure():
    if os.getenv("SGMA_DB_NAME",TARGET_DB)!=TARGET_DB: raise RuntimeError(f"B4 solo permite {TARGET_DB}; se cancela.")
    os.environ["SGMA_DB_NAME"]=TARGET_DB
    os.environ.setdefault("SGMA_DB_HOST","127.0.0.1"); os.environ.setdefault("SGMA_DB_USER","root")
    os.environ.setdefault("SGMA_DB_PASSWORD",""); os.environ.setdefault("SGMA_DB_PORT","3306")
    os.environ.setdefault("SGMA_SECRET_KEY",secrets.token_urlsafe(32))
def connect():
    return mysql.connector.connect(host=os.environ["SGMA_DB_HOST"],port=int(os.environ["SGMA_DB_PORT"]),user=os.environ["SGMA_DB_USER"],password=os.environ.get("SGMA_DB_PASSWORD",""),database=TARGET_DB,autocommit=False)
def fixture(tag):
    cn=connect(); c=cn.cursor(); users=[]; enrollment=None
    try:
        c.execute("SELECT VERSION(),DATABASE()"); version,db=c.fetchone()
        if db!=TARGET_DB: raise RuntimeError(f"Base inesperada: {db}")
        c.execute("SELECT a.id_alumno,c.id_carrera,c.nombre FROM alumnos a CROSS JOIN carreras c "
          "WHERE a.activo=TRUE AND c.activa=TRUE AND NOT EXISTS "
          "(SELECT 1 FROM matriculas m WHERE m.id_alumno=a.id_alumno AND m.id_carrera=c.id_carrera) "
          "ORDER BY a.id_alumno,c.id_carrera LIMIT 1")
        row=c.fetchone()
        if not row: raise RuntimeError("QA necesita un alumno y una carrera activa sin v?nculo previo.")
        student,career,career_name=row
        c.execute("SELECT id_rol,nombre FROM roles WHERE nombre IN ('ADMIN','PRECEPTOR')")
        roles={name:int(rid) for rid,name in c.fetchall()}
        if set(roles)!={"ADMIN","PRECEPTOR"}: raise RuntimeError("Faltan roles ADMIN/PRECEPTOR en QA.")
        for name in ("preceptor","admin"):
            c.execute("INSERT INTO usuarios(username,password_hash,id_rol) VALUES(%s,%s,%s)",(f"b4_{name}_{tag}",generate_password_hash(secrets.token_urlsafe(20)),roles[name.upper()]))
            users.append(int(c.lastrowid))
        cn.commit()
        return str(version),int(student),int(career),str(career_name),tuple(users),None
    except Exception: cn.rollback(); raise
    finally: cn.close()
def cleanup(student,career,users,matricula_id):
    cn=connect()
    try:
        c=cn.cursor()
        if matricula_id is not None: c.execute("DELETE FROM matriculas WHERE id_matricula=%s",(matricula_id,))
        if users: c.executemany("UPDATE usuarios SET activo=FALSE WHERE id_usuario=%s",[(u,) for u in users])
        cn.commit()
    except Exception: cn.rollback(); raise
    finally: cn.close()
def main():
    configure(); project=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(next(project.glob("Fase 3*/codigo"))))
    tag=secrets.token_hex(5); student=career=None; users=(); matricula=None
    try:
        version,student,career,career_name,users,matricula=fixture(tag)
        from sgma.web import create_app
        app=create_app({"TESTING":True,"SECRET_KEY":secrets.token_urlsafe(32)})
        pre=app.test_client()
        with pre.session_transaction() as s: s["usuario_id"]=users[0]; s["csrf"]="b4-token"
        page=pre.get("/matriculas")
        if page.status_code!=200 or b"Alta de matr" not in page.data: raise RuntimeError("PRECEPTOR no ve el formulario B4.")
        saved=pre.post("/matriculas",data={"csrf_token":"b4-token","id_alumno":str(student),"id_carrera":str(career),"anio_ingreso":"2026"},follow_redirects=True)
        if saved.status_code!=200 or "Matr?cula registrada" not in saved.get_data(as_text=True) or career_name not in saved.get_data(as_text=True): raise RuntimeError("La matr?cula no se guard? o no aparece en consulta.")
        cn=connect()
        try:
            c=cn.cursor(); c.execute("SELECT id_matricula FROM matriculas WHERE id_alumno=%s AND id_carrera=%s",(student,career)); row=c.fetchone()
            if not row: raise RuntimeError("No existe la matr?cula reci?n ingresada en base QA.")
            matricula=int(row[0])
        finally: cn.close()
        duplicate=pre.post("/matriculas",data={"csrf_token":"b4-token","id_alumno":str(student),"id_carrera":str(career),"anio_ingreso":"2026"},follow_redirects=True)
        if "ya tiene una matr" not in duplicate.get_data(as_text=True): raise RuntimeError("No se detect? matr?cula duplicada.")
        admin=app.test_client()
        with admin.session_transaction() as s: s["usuario_id"]=users[1]; s["csrf"]="b4-token"
        view=admin.get("/matriculas")
        if view.status_code!=200 or b"Esta pantalla es de consulta" not in view.data or career_name not in view.get_data(as_text=True): raise RuntimeError("ADMIN no tiene consulta de matr?cula.")
        denied=admin.post("/matriculas",data={"csrf_token":"b4-token","id_alumno":str(student),"id_carrera":str(career),"anio_ingreso":"2026"})
        if denied.status_code!=403: raise RuntimeError(f"ADMIN pudo editar matr?culas: HTTP {denied.status_code}.")
        print(f"Motor/base: {version} / {TARGET_DB}")
        print("PRECEPTOR: registra y consulta la matr?cula (HTTP 200)")
        print("Duplicado alumno/carrera: rechazado")
        print("ADMIN: consulta permitida; POST de alta rechazado con HTTP 403")
        print("Resultado B4: CUMPLE")
        return 0
    finally:
        if student is not None: cleanup(student,career,users,matricula)
if __name__=="__main__": raise SystemExit(main())
