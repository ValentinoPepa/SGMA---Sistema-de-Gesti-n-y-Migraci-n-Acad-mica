-- =====================================================================
-- SGMA - Cuenta de base de datos de la aplicación (sgma_app)
-- Diseño: "Diseño de Seguridad v1.1", sección 5.
--
-- Cómo ejecutarlo (con la cuenta de administración, DESPUÉS de gestion_academica.sql):
--     mysql -u root -p < crear_cuentas_bd.sql
--
-- ANTES DE EJECUTARLO: cambie 'CAMBIAR_ESTA_CLAVE' por una clave real.
-- No suba la clave real al repositorio.
--
-- Qué puede y qué no puede hacer sgma_app:
--   - SELECT, INSERT y UPDATE sobre las tablas de trabajo.
--   - SELECT sobre roles y auditoria (no puede escribir en la auditoría).
--   - EXECUTE sobre los procedimientos (sp_proximo_legajo, etc.).
--   - DELETE solo sobre correlatividades y asignaciones_docentes (son configuración).
--   - Sin DELETE sobre registros académicos y sin permisos de estructura (DDL).
-- =====================================================================

CREATE USER IF NOT EXISTS 'sgma_app'@'localhost' IDENTIFIED BY 'CAMBIAR_ESTA_CLAVE';

GRANT SELECT, INSERT, UPDATE ON gestion_academica.alumnos TO 'sgma_app'@'localhost';
GRANT SELECT, INSERT, UPDATE ON gestion_academica.matriculas TO 'sgma_app'@'localhost';
GRANT SELECT, INSERT, UPDATE ON gestion_academica.docentes TO 'sgma_app'@'localhost';
GRANT SELECT, INSERT, UPDATE ON gestion_academica.usuarios TO 'sgma_app'@'localhost';
GRANT SELECT, INSERT, UPDATE ON gestion_academica.carreras TO 'sgma_app'@'localhost';
GRANT SELECT, INSERT, UPDATE ON gestion_academica.materias TO 'sgma_app'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON gestion_academica.correlatividades TO 'sgma_app'@'localhost';
GRANT SELECT, INSERT, UPDATE ON gestion_academica.ciclos_lectivos TO 'sgma_app'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON gestion_academica.asignaciones_docentes TO 'sgma_app'@'localhost';
GRANT SELECT, INSERT, UPDATE ON gestion_academica.inscripciones TO 'sgma_app'@'localhost';
GRANT SELECT, INSERT, UPDATE ON gestion_academica.notas_cursada TO 'sgma_app'@'localhost';
GRANT SELECT, INSERT, UPDATE ON gestion_academica.asistencias TO 'sgma_app'@'localhost';
GRANT SELECT, INSERT, UPDATE ON gestion_academica.mesas_examen TO 'sgma_app'@'localhost';
GRANT SELECT, INSERT, UPDATE ON gestion_academica.inscripciones_examen TO 'sgma_app'@'localhost';
GRANT SELECT, INSERT, UPDATE ON gestion_academica.lotes_carga TO 'sgma_app'@'localhost';
GRANT SELECT, INSERT, UPDATE ON gestion_academica.actas_examen TO 'sgma_app'@'localhost';
GRANT SELECT, INSERT, UPDATE ON gestion_academica.parametros TO 'sgma_app'@'localhost';
GRANT SELECT ON gestion_academica.roles TO 'sgma_app'@'localhost';
GRANT SELECT ON gestion_academica.auditoria TO 'sgma_app'@'localhost';
GRANT EXECUTE ON gestion_academica.* TO 'sgma_app'@'localhost';

-- Verificación: debe listar los permisos de arriba.
SHOW GRANTS FOR 'sgma_app'@'localhost';
