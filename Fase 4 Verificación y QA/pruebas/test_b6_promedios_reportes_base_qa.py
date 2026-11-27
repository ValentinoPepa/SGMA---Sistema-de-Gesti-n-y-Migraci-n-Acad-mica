"""B6 integration check: exam averages and subject/cycle academic reports."""
from __future__ import annotations
import os,secrets,sys
from io import BytesIO
from pathlib import Path
import mysql.connector
from openpyxl import load_workbook
from werkzeug.security import generate_password_hash
TARGET_DB="gestion_academica_a1_qa"
def configure():
    if os.getenv("SGMA_DB_NAME",TARGET_DB)!=TARGET_DB: raise RuntimeError(f"B6 solo permite {TARGET_DB}; se cancela.")
    os.environ["SGMA_DB_NAME"]=TARGET_DB; os.environ.setdefault("SGMA_DB_HOST","127.0.0.1"); os.environ.setdefault("SGMA_DB_USER","root")
    os.environ.setdefault("SGMA_DB_PASSWORD",""); os.environ.setdefault("SGMA_DB_PORT","3306"); os.environ.setdefault("SGMA_SECRET_KEY",secrets.token_urlsafe(32))
def connect():
    return mysql.connector.connect(host=os.environ["SGMA_DB_HOST"],port=int(os.environ["SGMA_DB_PORT"]),user=os.environ["SGMA_DB_USER"],password=os.environ.get("SGMA_DB_PASSWORD",""),database=TARGET_DB,autocommit=False)
def fixture(tag):
    cn=connect(); c=cn.cursor(); d={"users":[],"teacher":None,"cycle":None,"mesa":None,"enrollment":None,"acts":[],"attendance":[]}
    try:
        c.execute("SELECT VERSION(),DATABASE()"); version,db=c.fetchone()
        if db!=TARGET_DB: raise RuntimeError(f"Base inesperada: {db}")
        c.execute("SELECT id_alumno,legajo FROM alumnos WHERE activo=TRUE ORDER BY id_alumno LIMIT 1"); r=c.fetchone()
        if not r: raise RuntimeError("QA necesita un alumno activo.")
        student,legajo=int(r[0]),int(r[1])
        c.execute("SELECT id_materia FROM materias WHERE activa=TRUE ORDER BY id_materia LIMIT 1"); r=c.fetchone()
        if not r: raise RuntimeError("QA necesita una materia activa.")
        subject=int(r[0])
        c.execute("SELECT anio FROM ciclos_lectivos"); used={int(x[0]) for x in c.fetchall()}
        year=next((y for y in range(2090,2200) if y not in used),None)
        if year is None: raise RuntimeError("No hay a?o libre de prueba para el ciclo.")
        c.execute("INSERT INTO ciclos_lectivos(anio,fecha_inicio,fecha_fin) VALUES(%s,%s,%s)",(year,f"{year}-01-01",f"{year}-12-31")); d["cycle"]=int(c.lastrowid)
        exam_date=f"{year}-06-15"
        c.execute("INSERT INTO mesas_examen(id_materia,id_ciclo,fecha,llamado) VALUES(%s,%s,%s,1)",(subject,d["cycle"],exam_date)); d["mesa"]=int(c.lastrowid)
        c.execute("INSERT INTO inscripciones(id_alumno,id_materia,id_ciclo) VALUES(%s,%s,%s)",(student,subject,d["cycle"])); d["enrollment"]=int(c.lastrowid)
        c.execute("SELECT COALESCE(SUM(nota),0),COUNT(nota),COALESCE(SUM(CASE WHEN estado='APROBADO' THEN nota ELSE 0 END),0),SUM(CASE WHEN estado='APROBADO' AND nota IS NOT NULL THEN 1 ELSE 0 END) FROM actas_examen WHERE id_alumno=%s AND activo=TRUE",(student,))
        d["base_actas"]=tuple(str(v or 0) for v in c.fetchone())
        exams=[(8,"APROBADO","B6P"),(2,"DESAPROBADO","B6F"),(None,"AUSENTE","B6A")]
        for score,state,book in exams:
            c.execute("INSERT INTO actas_examen(id_alumno,id_materia,id_mesa,fecha_examen,libro,folio,nota,estado,origen) VALUES(%s,%s,%s,%s,%s,'1',%s,%s,'MANUAL')",(student,subject,d["mesa"],exam_date,book,score,state)); d["acts"].append(int(c.lastrowid))
        for n,state in enumerate(("PRESENTE","PRESENTE","AUSENTE","JUSTIFICADO"),1):
            c.execute("INSERT INTO asistencias(id_inscripcion,fecha_clase,estado) VALUES(%s,%s,%s)",(d["enrollment"],f"{year}-03-{n:02d}",state)); d["attendance"].append(int(c.lastrowid))
        c.execute("SELECT id_rol,nombre FROM roles WHERE nombre IN ('ADMIN','DOCENTE')"); roles={name:int(rid) for rid,name in c.fetchall()}
        if set(roles)!={"ADMIN","DOCENTE"}: raise RuntimeError("Faltan roles ADMIN/DOCENTE.")
        c.execute("INSERT INTO docentes(nombre,apellido,dni) VALUES('B6','Prueba',%s)",(str(820000000+secrets.randbelow(10000000)),)); d["teacher"]=int(c.lastrowid)
        for name,teacher_id in (("admin",None),("docente",d["teacher"])):
            c.execute("INSERT INTO usuarios(username,password_hash,id_rol,id_docente) VALUES(%s,%s,%s,%s)",(f"b6_{name}_{tag}",generate_password_hash(secrets.token_urlsafe(20)),roles[name.upper()],teacher_id)); d["users"].append(int(c.lastrowid))
        cn.commit(); d.update(student=student,legajo=legajo,subject=subject,year=year)
        return str(version),d
    except Exception: cn.rollback(); raise
    finally: cn.close()
def cleanup(d):
    cn=connect()
    try:
        c=cn.cursor()
        for aid in d["acts"]: c.execute("DELETE FROM actas_examen WHERE id_acta=%s",(aid,))
        for aid in d["attendance"]: c.execute("DELETE FROM asistencias WHERE id_asistencia=%s",(aid,))
        if d["enrollment"]: c.execute("DELETE FROM inscripciones WHERE id_inscripcion=%s",(d["enrollment"],))
        if d["mesa"]: c.execute("DELETE FROM mesas_examen WHERE id_mesa=%s",(d["mesa"],))
        if d["cycle"]: c.execute("DELETE FROM ciclos_lectivos WHERE id_ciclo=%s",(d["cycle"],))
        if d["users"]: c.executemany("UPDATE usuarios SET activo=FALSE WHERE id_usuario=%s",[(u,) for u in d["users"]])
        if d["teacher"]: c.execute("UPDATE docentes SET activo=FALSE WHERE id_docente=%s",(d["teacher"],))
        cn.commit()
    except Exception: cn.rollback(); raise
    finally: cn.close()
def main():
    configure(); project=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(next(project.glob("Fase 3*/codigo"))))
    tag=secrets.token_hex(5); d={"users":[]}
    try:
        version,d=fixture(tag)
        from sgma.web import create_app
        app=create_app({"TESTING":True,"SECRET_KEY":secrets.token_urlsafe(32)})
        client=app.test_client()
        with client.session_transaction() as s: s["usuario_id"]=d["users"][0]
        analytic=client.get(f"/reportes/alumnos/{d['student']}/analitico.xlsx")
        if analytic.status_code!=200: raise RuntimeError(f"Exportaci?n de anal?tico fall?: HTTP {analytic.status_code}.")
        workbook=load_workbook(BytesIO(analytic.data),data_only=True)
        sheet=workbook["Resumen"]
        values={sheet.cell(row,1).value:sheet.cell(row,2).value for row in range(1,sheet.max_row+1)}
        with_aplazos=values.get("Promedio examenes (con aplazos)")
        no_aplazos=values.get("Promedio examenes (sin aplazos)")
        total,count,aprobadas,aprobadas_count=(float(v) for v in d["base_actas"])
        expected_with=(total+10)/(count+2)
        expected_without=(aprobadas+8)/(aprobadas_count+1)
        if with_aplazos is None or no_aplazos is None or abs(float(with_aplazos)-expected_with)>0.0001 or abs(float(no_aplazos)-expected_without)>0.0001: raise RuntimeError(f"Promedios incorrectos: con={with_aplazos} (esperado {expected_with}), sin={no_aplazos} (esperado {expected_without}).")
        search=client.get(f"/busqueda?q={d['legajo']}")
        if search.status_code!=200 or b"sin aplazos" not in search.data: raise RuntimeError("Busqueda no muestra el promedio sin aplazos.")
        general=client.get("/reportes/alumnos.xlsx")
        if general.status_code!=200: raise RuntimeError("El reporte general de alumnos no pudo exportarse.")
        general_sheet=load_workbook(BytesIO(general.data),data_only=True).active
        headings=[cell.value for cell in general_sheet[1]]
        if "Promedio examenes sin aplazos" not in headings: raise RuntimeError("Falta el promedio sin aplazos en el reporte general.")
        general_row=next((row for row in general_sheet.iter_rows(min_row=2,values_only=True) if row[0]==d["legajo"]),None)
        if not general_row or abs(float(general_row[7])-expected_without)>0.0001: raise RuntimeError("El reporte general no coincide en el promedio sin aplazos.")
        url=f"/reportes/academicos?materia={d['subject']}&anio={d['year']}"
        report=client.get(url)
        if report.status_code!=200: raise RuntimeError(f"Reporte no carga: HTTP {report.status_code}.")
        html=report.get_data(as_text=True)
        if "66.7%" not in html or "B6P" not in html or "B6F" not in html: raise RuntimeError("Reportes no incluyen las actas filtradas o el resumen de asistencia esperado.")
        actas_filter=f"materia={d['subject']}&anio={d['year']}"
        acts=client.get(f"/reportes/actas.xlsx?{actas_filter}")
        attendance=client.get(f"/reportes/asistencia-materia.xlsx?{actas_filter}")
        acts_pdf=client.get(f"/reportes/actas.pdf?{actas_filter}")
        attendance_pdf=client.get(f"/reportes/asistencia-materia.pdf?{actas_filter}")
        if any(r.status_code!=200 for r in (acts,attendance,acts_pdf,attendance_pdf)): raise RuntimeError("Fall? una exportaci?n PDF/Excel.")
        if not acts_pdf.data.startswith(b"%PDF") or not attendance_pdf.data.startswith(b"%PDF"): raise RuntimeError("La exportaci?n PDF no tiene formato v?lido.")
        acts_wb=load_workbook(BytesIO(acts.data),data_only=True); attendance_wb=load_workbook(BytesIO(attendance.data),data_only=True)
        if acts_wb.active.max_row!=4 or attendance_wb.active.max_row!=2: raise RuntimeError("Los Excel no reflejan los datos del filtro QA.")
        doc=app.test_client()
        with doc.session_transaction() as s: s["usuario_id"]=d["users"][1]
        denied=doc.get("/reportes/academicos")
        if denied.status_code!=403: raise RuntimeError(f"DOCENTE accedi? al reporte general: HTTP {denied.status_code}.")
        print(f"Motor/base: {version} / {TARGET_DB}")
        print(f"Promedio de actas: con aplazos={float(with_aplazos):.2f}; sin aplazos (solo APROBADO)={float(no_aplazos):.2f}")
        print("Reporte de actas: filtra por materia/ciclo y exporta Excel")
        print("Asistencia por materia: 2 presentes, 1 ausente, 1 justificada; porcentaje 66.7%")
        print("Exportaciones PDF y Excel verificadas; DOCENTE sin acceso al reporte general (HTTP 403)")
        print("Resultado B6: CUMPLE")
        return 0
    finally:
        if d.get("users"): cleanup(d)
if __name__=="__main__": raise SystemExit(main())
