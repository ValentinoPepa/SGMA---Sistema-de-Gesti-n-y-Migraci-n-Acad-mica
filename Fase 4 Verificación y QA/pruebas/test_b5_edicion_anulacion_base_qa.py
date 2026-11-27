"""B5 integration test against isolated gestion_academica_a1_qa."""
from __future__ import annotations
import os,secrets,sys
from pathlib import Path
import mysql.connector
from werkzeug.security import generate_password_hash
TARGET_DB="gestion_academica_a1_qa"
def configure():
    if os.getenv("SGMA_DB_NAME",TARGET_DB)!=TARGET_DB: raise RuntimeError(f"B5 solo permite {TARGET_DB}; se cancela.")
    os.environ["SGMA_DB_NAME"]=TARGET_DB; os.environ.setdefault("SGMA_DB_HOST","127.0.0.1"); os.environ.setdefault("SGMA_DB_USER","root")
    os.environ.setdefault("SGMA_DB_PASSWORD",""); os.environ.setdefault("SGMA_DB_PORT","3306"); os.environ.setdefault("SGMA_SECRET_KEY",secrets.token_urlsafe(32))
def connect():
    return mysql.connector.connect(host=os.environ["SGMA_DB_HOST"],port=int(os.environ["SGMA_DB_PORT"]),user=os.environ["SGMA_DB_USER"],password=os.environ.get("SGMA_DB_PASSWORD",""),database=TARGET_DB,autocommit=False)
def fixture(tag):
    cn=connect(); c=cn.cursor(); d={"users":[],"teacher":None,"cycle":None,"enrollment":None,"note":None,"act":None,"act_cancel":None}
    try:
        c.execute("SELECT VERSION(),DATABASE()"); version,db=c.fetchone()
        if db!=TARGET_DB: raise RuntimeError(f"Base inesperada: {db}")
        c.execute("SELECT id_alumno FROM alumnos WHERE activo=TRUE ORDER BY id_alumno LIMIT 1"); r=c.fetchone()
        if not r: raise RuntimeError("La QA requiere al menos un alumno activo.")
        student=int(r[0])
        c.execute("SELECT id_materia FROM materias WHERE activa=TRUE ORDER BY id_materia LIMIT 1"); r=c.fetchone()
        if not r: raise RuntimeError("La QA requiere al menos una materia activa.")
        subject=int(r[0])
        c.execute("SELECT anio FROM ciclos_lectivos"); used={int(x[0]) for x in c.fetchall()}
        year=next((y for y in range(2090,2200) if y not in used),None)
        if year is None: raise RuntimeError("No hay a?o libre para la cursada de prueba.")
        c.execute("INSERT INTO ciclos_lectivos(anio,fecha_inicio,fecha_fin) VALUES(%s,%s,%s)",(year,f"{year}-01-01",f"{year}-12-31")); d["cycle"]=int(c.lastrowid)
        c.execute("INSERT INTO docentes(nombre,apellido,dni) VALUES('B5','Prueba',%s)",(str(810000000+secrets.randbelow(10000000)),)); d["teacher"]=int(c.lastrowid)
        c.execute("SELECT id_rol,nombre FROM roles WHERE nombre IN ('PRECEPTOR','DOCENTE')"); roles={name:int(rid) for rid,name in c.fetchall()}
        if set(roles)!={"PRECEPTOR","DOCENTE"}: raise RuntimeError("Faltan roles para probar correcci?n exclusiva del PRECEPTOR.")
        for name,teacher in (("preceptor",None),("docente",d["teacher"])):
            c.execute("INSERT INTO usuarios(username,password_hash,id_rol,id_docente) VALUES(%s,%s,%s,%s)",(f"b5_{name}_{tag}",generate_password_hash(secrets.token_urlsafe(20)),roles[name.upper()],teacher)); d["users"].append(int(c.lastrowid))
        c.execute("INSERT INTO inscripciones(id_alumno,id_materia,id_ciclo) VALUES(%s,%s,%s)",(student,subject,d["cycle"])); d["enrollment"]=int(c.lastrowid)
        c.execute("INSERT INTO notas_cursada(id_inscripcion,instancia,nota,fecha) VALUES(%s,'B5 QA',7,'2026-11-26')",(d["enrollment"],)); d["note"]=int(c.lastrowid)
        c.execute("INSERT INTO actas_examen(id_alumno,id_materia,fecha_examen,libro,folio,nota,estado,origen) VALUES(%s,%s,'2026-11-20','B5QA','1',8,'APROBADO','MANUAL')",(student,subject)); d["act"]=int(c.lastrowid)
        c.execute("INSERT INTO actas_examen(id_alumno,id_materia,fecha_examen,libro,folio,nota,estado,origen) VALUES(%s,%s,'2026-11-21','B5QA','2',6,'DESAPROBADO','MANUAL')",(student,subject)); d["act_cancel"]=int(c.lastrowid)
        cn.commit(); return str(version),d
    except Exception: cn.rollback(); raise
    finally: cn.close()
def cleanup(d):
    cn=connect()
    try:
        c=cn.cursor()
        if d["act"]: c.execute("DELETE FROM actas_examen WHERE id_acta=%s",(d["act"],))
        if d.get("act_cancel"): c.execute("DELETE FROM actas_examen WHERE id_acta=%s",(d["act_cancel"],))
        if d["note"]: c.execute("DELETE FROM notas_cursada WHERE id_nota=%s",(d["note"],))
        if d["enrollment"]: c.execute("DELETE FROM inscripciones WHERE id_inscripcion=%s",(d["enrollment"],))
        if d["cycle"]: c.execute("DELETE FROM ciclos_lectivos WHERE id_ciclo=%s",(d["cycle"],))
        if d["users"]: c.executemany("UPDATE usuarios SET activo=FALSE WHERE id_usuario=%s",[(u,) for u in d["users"]])
        if d["teacher"]: c.execute("UPDATE docentes SET activo=FALSE WHERE id_docente=%s",(d["teacher"],))
        cn.commit()
    except Exception: cn.rollback(); raise
    finally: cn.close()
def main():
    configure(); project=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(next(project.glob("Fase 3*/codigo"))))
    tag=secrets.token_hex(5); d={"users":[]};
    try:
        version,d=fixture(tag)
        from sgma.web import create_app
        app=create_app({"TESTING":True,"SECRET_KEY":secrets.token_urlsafe(32)})
        pre=app.test_client()
        with pre.session_transaction() as s: s["usuario_id"]=d["users"][0]; s["csrf"]="b5-token"
        page=pre.get("/cursadas")
        if page.status_code!=200 or b"Guardar correcci" not in page.data or b"Anular acta" not in page.data: raise RuntimeError("PRECEPTOR no ve controles de correcci?n/anulaci?n.")
        updated=pre.post("/cursadas",data={"csrf_token":"b5-token","accion":"corregir_acta","id_acta":str(d["act"]),"fecha_examen":"2026-11-20","libro":"B5QA","folio":"1","nota":"9","estado":"APROBADO"},follow_redirects=True)
        if updated.status_code!=200 or "actualizado" not in updated.get_data(as_text=True): raise RuntimeError("PRECEPTOR no pudo corregir el acta.")
        canceled_act=pre.post("/cursadas",data={"csrf_token":"b5-token","accion":"anular_acta","id_acta":str(d["act_cancel"])},follow_redirects=True)
        if canceled_act.status_code!=200 or "anulado" not in canceled_act.get_data(as_text=True): raise RuntimeError("No se anul? el acta.")
        canceled_note=pre.post("/cursadas",data={"csrf_token":"b5-token","accion":"anular_nota","id_nota":str(d["note"])},follow_redirects=True)
        if canceled_note.status_code!=200 or "anulado" not in canceled_note.get_data(as_text=True): raise RuntimeError("No se anul? la nota.")
        canceled_inscription=pre.post("/cursadas",data={"csrf_token":"b5-token","accion":"anular_inscripcion","id_inscripcion":str(d["enrollment"])},follow_redirects=True)
        if canceled_inscription.status_code!=200 or "anulado" not in canceled_inscription.get_data(as_text=True): raise RuntimeError("No se anul? la inscripci?n.")
        teacher=app.test_client()
        with teacher.session_transaction() as s: s["usuario_id"]=d["users"][1]; s["csrf"]="b5-token"
        denied=teacher.post("/cursadas",data={"csrf_token":"b5-token","accion":"corregir_acta","id_acta":str(d["act"]),"fecha_examen":"2026-11-20","libro":"BAD","folio":"1","nota":"2","estado":"DESAPROBADO"})
        if denied.status_code!=403: raise RuntimeError(f"DOCENTE pudo corregir acta: HTTP {denied.status_code}.")
        cn=connect()
        try:
            c=cn.cursor()
            c.execute("SELECT nota,activo FROM actas_examen WHERE id_acta=%s",(d["act"],)); act=c.fetchone()
            c.execute("SELECT activo FROM notas_cursada WHERE id_nota=%s",(d["note"],)); note=c.fetchone()
            c.execute("SELECT activo FROM actas_examen WHERE id_acta=%s",(d["act_cancel"],)); act_cancel=c.fetchone()
            c.execute("SELECT activo FROM inscripciones WHERE id_inscripcion=%s",(d["enrollment"],)); ins=c.fetchone()
            if not act or float(act[0])!=9.0 or int(act[1])!=1 or not act_cancel or int(act_cancel[0])!=0 or not note or int(note[0])!=0 or not ins or int(ins[0])!=0: raise RuntimeError("El estado final de edici?n/anulaci?n no coincide.")
            c.execute("SELECT COUNT(*) FROM auditoria WHERE id_usuario=%s AND tabla='actas_examen' AND id_registro=%s AND campo='nota' AND valor_anterior='8.00' AND valor_nuevo='9.00'",(d["users"][0],d["act"]))
            act_audit=int(c.fetchone()[0])
            c.execute("SELECT COUNT(*) FROM auditoria WHERE id_usuario=%s AND tabla='actas_examen' AND id_registro=%s AND campo='activo' AND valor_nuevo='0'",(d["users"][0],d["act_cancel"]))
            cancel_act_audit=int(c.fetchone()[0])
            c.execute("SELECT COUNT(*) FROM auditoria WHERE id_usuario=%s AND tabla='notas_cursada' AND id_registro=%s AND campo='activo' AND valor_nuevo='0'",(d["users"][0],d["note"]))
            note_audit=int(c.fetchone()[0])
            c.execute("SELECT COUNT(*) FROM auditoria WHERE id_usuario=%s AND tabla='inscripciones' AND id_registro=%s AND campo='activo' AND valor_nuevo='0'",(d["users"][0],d["enrollment"]))
            ins_audit=int(c.fetchone()[0])
            if min(act_audit,cancel_act_audit,note_audit,ins_audit)<1: raise RuntimeError(f"Auditor?a incompleta: acta={act_audit}, anulaci?n_acta={cancel_act_audit}, nota={note_audit}, inscripci?n={ins_audit}.")
        finally: cn.close()
        print(f"Motor/base: {version} / {TARGET_DB}")
        print("PRECEPTOR: corrige acta y anula acta/nota/inscripci?n; activo=0 confirmado")
        print("Auditor?a de acta, nota e inscripci?n registra el usuario PRECEPTOR")
        print("DOCENTE: intento de corregir acta rechazado con HTTP 403")
        print("Resultado B5: CUMPLE")
        return 0
    finally:
        if d.get("users"): cleanup(d)
if __name__=="__main__": raise SystemExit(main())
