-- =====================================================================
-- SGMA - Sistema de Gestión Académica
-- Esquema de base de datos v1.2 (conciliado con SRS v1.1 y Diccionario v1.1)
--
-- Motor objetivo : MySQL 8.0.16 o superior (InnoDB).
--                  Desde la 8.0.16 se hacen cumplir las restricciones CHECK;
--                  en versiones anteriores se aceptan pero se ignoran.
-- Uso            : script de una sola ejecución sobre un servidor limpio.
--                  Para recrearlo: DROP DATABASE gestion_academica;
-- Nombres        : tablas y campos en minúsculas con guion bajo.
--
-- Contenido      : 19 tablas, 2 procedimientos de legajo, 1 procedimiento de
--                  auditoría, 14 triggers y datos semilla (roles, parámetros).
-- =====================================================================

CREATE DATABASE IF NOT EXISTS gestion_academica
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE gestion_academica;

-- =====================================================================
-- 1. SEGURIDAD Y USUARIOS (RF-USR, RNF-03, RNF-04)
-- =====================================================================

CREATE TABLE roles (
  id_rol TINYINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(30) NOT NULL,
  CONSTRAINT uq_roles_nombre UNIQUE (nombre)
) ENGINE=InnoDB;

CREATE TABLE docentes (
  id_docente INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(50) NOT NULL,
  apellido VARCHAR(50) NOT NULL,
  dni VARCHAR(15) NOT NULL,
  email VARCHAR(100) NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT uq_docentes_dni UNIQUE (dni),
  CONSTRAINT chk_docentes_dni CHECK (dni REGEXP '^[0-9]+$')
) ENGINE=InnoDB;

CREATE TABLE usuarios (
  id_usuario INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,           -- bcrypt / Argon2 (RNF-03)
  id_rol TINYINT UNSIGNED NOT NULL,
  id_docente INT NULL,                           -- obligatorio si el rol es DOCENTE (RF-USR-02)
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  ultimo_acceso DATETIME NULL,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_usuarios_username UNIQUE (username),
  CONSTRAINT uq_usuarios_docente UNIQUE (id_docente),
  CONSTRAINT fk_usuarios_rol FOREIGN KEY (id_rol)
    REFERENCES roles (id_rol) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_usuarios_docente FOREIGN KEY (id_docente)
    REFERENCES docentes (id_docente) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- =====================================================================
-- 2. ESTRUCTURA ACADÉMICA (RF-GAC-05 a 08)
-- =====================================================================

CREATE TABLE carreras (
  id_carrera INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  activa BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT uq_carreras_nombre UNIQUE (nombre)
) ENGINE=InnoDB;

CREATE TABLE materias (
  id_materia INT AUTO_INCREMENT PRIMARY KEY,
  id_carrera INT NOT NULL,                       -- una materia pertenece a una sola carrera
  codigo VARCHAR(10) NOT NULL,
  nombre VARCHAR(100) NOT NULL,
  anio_nivel TINYINT NOT NULL,
  activa BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT uq_materias_codigo UNIQUE (codigo),
  CONSTRAINT chk_materias_anio CHECK (anio_nivel BETWEEN 1 AND 5),
  CONSTRAINT fk_materias_carrera FOREIGN KEY (id_carrera)
    REFERENCES carreras (id_carrera) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- Materias que el alumno debe tener aprobadas para cursar/rendir id_materia (RF-GAC-03, 06)
CREATE TABLE correlatividades (
  id_materia INT NOT NULL,
  id_materia_requerida INT NOT NULL,
  PRIMARY KEY (id_materia, id_materia_requerida),
  CONSTRAINT chk_correl_distintas CHECK (id_materia <> id_materia_requerida),
  CONSTRAINT fk_correl_materia FOREIGN KEY (id_materia)
    REFERENCES materias (id_materia) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_correl_requerida FOREIGN KEY (id_materia_requerida)
    REFERENCES materias (id_materia) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE ciclos_lectivos (
  id_ciclo INT AUTO_INCREMENT PRIMARY KEY,
  anio SMALLINT NOT NULL,
  fecha_inicio DATE NOT NULL,
  fecha_fin DATE NOT NULL,
  CONSTRAINT uq_ciclos_anio UNIQUE (anio),
  CONSTRAINT chk_ciclos_fechas CHECK (fecha_fin > fecha_inicio)
) ENGINE=InnoDB;

-- Define qué materias puede cargar cada docente en cada ciclo (RF-USR-02, RNF-04)
CREATE TABLE asignaciones_docentes (
  id_docente INT NOT NULL,
  id_materia INT NOT NULL,
  id_ciclo INT NOT NULL,
  PRIMARY KEY (id_docente, id_materia, id_ciclo),
  CONSTRAINT fk_asig_docente FOREIGN KEY (id_docente)
    REFERENCES docentes (id_docente) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_asig_materia FOREIGN KEY (id_materia)
    REFERENCES materias (id_materia) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_asig_ciclo FOREIGN KEY (id_ciclo)
    REFERENCES ciclos_lectivos (id_ciclo) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- =====================================================================
-- 3. ALUMNOS Y MATRÍCULA (RF-GAC-01)
-- =====================================================================

CREATE TABLE alumnos (
  id_alumno INT AUTO_INCREMENT PRIMARY KEY,      -- clave interna, no visible
  legajo INT NOT NULL,                           -- asignado por sp_proximo_legajo (RF-GAC-01)
  dni VARCHAR(15) NOT NULL,
  nombre VARCHAR(50) NOT NULL,
  apellido VARCHAR(50) NOT NULL,
  fecha_nacimiento DATE NULL,
  email VARCHAR(100) NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,          -- borrado lógico
  origen ENUM('MANUAL','MASIVA','MIGRACION') NOT NULL DEFAULT 'MANUAL',
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_alumnos_legajo UNIQUE (legajo),  -- el UNIQUE ya crea el índice
  CONSTRAINT uq_alumnos_dni UNIQUE (dni),
  CONSTRAINT chk_alumnos_dni CHECK (dni REGEXP '^[0-9]+$')
) ENGINE=InnoDB;

-- A qué carrera pertenece cada alumno. Los alumnos migrados no tienen fila
-- hasta que se cargue (la planilla Alumnos_2026_Final.xlsx no trae carrera).
CREATE TABLE matriculas (
  id_matricula INT AUTO_INCREMENT PRIMARY KEY,
  id_alumno INT NOT NULL,
  id_carrera INT NOT NULL,
  anio_ingreso SMALLINT NOT NULL,
  estado ENUM('ACTIVA','EGRESADA','BAJA') NOT NULL DEFAULT 'ACTIVA',
  CONSTRAINT uq_matriculas_alumno_carrera UNIQUE (id_alumno, id_carrera),
  CONSTRAINT fk_matriculas_alumno FOREIGN KEY (id_alumno)
    REFERENCES alumnos (id_alumno) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_matriculas_carrera FOREIGN KEY (id_carrera)
    REFERENCES carreras (id_carrera) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- =====================================================================
-- 4. CURSADA Y ASISTENCIAS (RF-GAC-09, 10, RF-ASI)
-- =====================================================================

CREATE TABLE inscripciones (
  id_inscripcion INT AUTO_INCREMENT PRIMARY KEY,
  id_alumno INT NOT NULL,
  id_materia INT NOT NULL,
  id_ciclo INT NOT NULL,
  condicion_cursada ENUM('CURSANDO','REGULAR','PROMOCIONADO','LIBRE') NOT NULL DEFAULT 'CURSANDO',
  activo BOOLEAN NOT NULL DEFAULT TRUE,          -- anulación = baja lógica
  CONSTRAINT uq_inscripciones UNIQUE (id_alumno, id_materia, id_ciclo),
  CONSTRAINT fk_inscripciones_alumno FOREIGN KEY (id_alumno)
    REFERENCES alumnos (id_alumno) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_inscripciones_materia FOREIGN KEY (id_materia)
    REFERENCES materias (id_materia) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_inscripciones_ciclo FOREIGN KEY (id_ciclo)
    REFERENCES ciclos_lectivos (id_ciclo) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- Parciales y demás instancias de la cursada (RF-GAC-10)
CREATE TABLE notas_cursada (
  id_nota INT AUTO_INCREMENT PRIMARY KEY,
  id_inscripcion INT NOT NULL,
  instancia VARCHAR(30) NOT NULL,                -- por ejemplo: 'Parcial 1', 'Recuperatorio 1'
  nota DECIMAL(4,2) NOT NULL,
  fecha DATE NOT NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,          -- anulación = baja lógica
  CONSTRAINT uq_notas_instancia UNIQUE (id_inscripcion, instancia),
  CONSTRAINT chk_notas_rango CHECK (nota BETWEEN 1.00 AND 10.00),
  CONSTRAINT fk_notas_inscripcion FOREIGN KEY (id_inscripcion)
    REFERENCES inscripciones (id_inscripcion) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE asistencias (
  id_asistencia INT AUTO_INCREMENT PRIMARY KEY,
  id_inscripcion INT NOT NULL,
  fecha_clase DATE NOT NULL,
  estado ENUM('PRESENTE','AUSENTE','JUSTIFICADO') NOT NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,          -- anulación = baja lógica
  CONSTRAINT uq_asistencias UNIQUE (id_inscripcion, fecha_clase),
  CONSTRAINT fk_asistencias_inscripcion FOREIGN KEY (id_inscripcion)
    REFERENCES inscripciones (id_inscripcion) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- =====================================================================
-- 5. EXÁMENES Y ACTAS (RF-GAC-02, 08, 09)
-- =====================================================================

CREATE TABLE mesas_examen (
  id_mesa INT AUTO_INCREMENT PRIMARY KEY,
  id_materia INT NOT NULL,
  id_ciclo INT NOT NULL,
  fecha DATE NOT NULL,
  llamado TINYINT NOT NULL DEFAULT 1,
  activo BOOLEAN NOT NULL DEFAULT TRUE,          -- anulación = baja lógica
  CONSTRAINT uq_mesas UNIQUE (id_materia, fecha, llamado),
  CONSTRAINT chk_mesas_llamado CHECK (llamado >= 1),
  CONSTRAINT fk_mesas_materia FOREIGN KEY (id_materia)
    REFERENCES materias (id_materia) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_mesas_ciclo FOREIGN KEY (id_ciclo)
    REFERENCES ciclos_lectivos (id_ciclo) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE inscripciones_examen (
  id_alumno INT NOT NULL,
  id_mesa INT NOT NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,          -- anulación = baja lógica
  PRIMARY KEY (id_alumno, id_mesa),
  CONSTRAINT fk_insc_examen_alumno FOREIGN KEY (id_alumno)
    REFERENCES alumnos (id_alumno) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_insc_examen_mesa FOREIGN KEY (id_mesa)
    REFERENCES mesas_examen (id_mesa) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- Registro de cada carga masiva o migración (RF-CMA-04, RF-MIG-05)
CREATE TABLE lotes_carga (
  id_lote INT AUTO_INCREMENT PRIMARY KEY,
  tipo ENUM('MIGRACION','MASIVA') NOT NULL,
  entidad VARCHAR(30) NOT NULL,                  -- por ejemplo: 'alumnos', 'actas_examen'
  id_usuario INT NULL,
  archivo VARCHAR(200) NOT NULL,
  fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  filas_total INT NOT NULL DEFAULT 0,
  filas_ok INT NOT NULL DEFAULT 0,
  filas_error INT NOT NULL DEFAULT 0,
  CONSTRAINT chk_lotes_filas CHECK (filas_ok + filas_error <= filas_total),
  CONSTRAINT fk_lotes_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuarios (id_usuario) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE actas_examen (
  id_acta INT AUTO_INCREMENT PRIMARY KEY,
  id_alumno INT NOT NULL,
  id_materia INT NOT NULL,
  id_mesa INT NULL,                              -- NULL en las actas históricas migradas
  fecha_examen DATE NOT NULL,                    -- la migración rechaza filas sin fecha válida
  libro VARCHAR(20) NOT NULL,
  folio VARCHAR(20) NOT NULL,
  nota DECIMAL(4,2) NULL,                        -- NULL solo si el estado es AUSENTE
  estado ENUM('APROBADO','DESAPROBADO','AUSENTE') NOT NULL,
  origen ENUM('MANUAL','MASIVA','MIGRACION') NOT NULL DEFAULT 'MANUAL',
  id_lote INT NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,          -- borrado lógico
  CONSTRAINT chk_actas_nota_rango CHECK (nota BETWEEN 1.00 AND 10.00),
  CONSTRAINT chk_actas_nota_estado CHECK (
    (estado = 'AUSENTE' AND nota IS NULL) OR (estado <> 'AUSENTE' AND nota IS NOT NULL)
  ),
  INDEX idx_acta_alumno (id_alumno),
  CONSTRAINT fk_actas_alumno FOREIGN KEY (id_alumno)
    REFERENCES alumnos (id_alumno) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_actas_materia FOREIGN KEY (id_materia)
    REFERENCES materias (id_materia) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_actas_mesa FOREIGN KEY (id_mesa)
    REFERENCES mesas_examen (id_mesa) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_actas_lote FOREIGN KEY (id_lote)
    REFERENCES lotes_carga (id_lote) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- =====================================================================
-- 6. PARÁMETROS Y AUDITORÍA (RF-ASI-03, RNF-05)
-- =====================================================================

CREATE TABLE parametros (
  clave VARCHAR(50) PRIMARY KEY,
  valor VARCHAR(100) NOT NULL,
  descripcion VARCHAR(200) NULL
) ENGINE=InnoDB;

-- id_usuario queda NULL si el cambio se hizo sin pasar por la aplicación
-- (por ejemplo, una edición directa en la base). Ver la variable @app_user_id.
CREATE TABLE auditoria (
  id_evento BIGINT AUTO_INCREMENT PRIMARY KEY,
  id_usuario INT NULL,
  fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  tabla VARCHAR(50) NOT NULL,
  operacion ENUM('INSERT','UPDATE','DELETE') NOT NULL,
  id_registro INT NOT NULL,
  campo VARCHAR(50) NULL,
  valor_anterior VARCHAR(255) NULL,
  valor_nuevo VARCHAR(255) NULL,
  INDEX idx_auditoria_registro (tabla, id_registro),
  INDEX idx_auditoria_fecha (fecha_hora),
  CONSTRAINT fk_auditoria_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuarios (id_usuario) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- =====================================================================
-- 7. DATOS SEMILLA
-- =====================================================================

INSERT INTO roles (nombre) VALUES ('ADMIN'), ('PRECEPTOR'), ('DOCENTE'), ('DIRECTIVO');

INSERT INTO parametros (clave, valor, descripcion) VALUES
  ('ultimo_legajo', '0',
   'Último legajo asignado. Lo actualizan sp_proximo_legajo y sp_sincronizar_legajo.'),
  ('asistencia_minima', '75',
   'Porcentaje mínimo de asistencia (RF-ASI-03). VALOR PROVISORIO: confirmar con la institución.');

-- El primer usuario ADMIN se crea desde la aplicación o con un INSERT manual
-- que incluya un password_hash real. No se incluye acá para no dejar claves en el repositorio.

-- =====================================================================
-- 8. PROCEDIMIENTOS
-- =====================================================================
DELIMITER $$

-- Entrega el próximo legajo de forma segura ante cargas simultáneas.
-- La fila de parametros queda bloqueada hasta el fin de la transacción, de modo
-- que dos altas no reciben el mismo número ni quedan huecos si una se revierte.
-- Uso:  CALL sp_proximo_legajo(@legajo);  INSERT INTO alumnos (legajo, ...) VALUES (@legajo, ...);
CREATE PROCEDURE sp_proximo_legajo(OUT p_legajo INT)
BEGIN
  UPDATE parametros
     SET valor = LAST_INSERT_ID(CAST(valor AS UNSIGNED) + 1)
   WHERE clave = 'ultimo_legajo';
  SET p_legajo = LAST_INSERT_ID();
END$$

-- Se ejecuta al terminar la migración inicial (RF-MIG-06): el contador pasa a ser
-- el mayor legajo existente, y los alumnos nuevos continúan desde ahí.
CREATE PROCEDURE sp_sincronizar_legajo()
BEGIN
  UPDATE parametros
     SET valor = CAST((SELECT COALESCE(MAX(legajo), 0) FROM alumnos) AS CHAR)
   WHERE clave = 'ultimo_legajo';
END$$

-- Escribe un evento de auditoría. Lo llaman los triggers.
-- La aplicación debe ejecutar  SET @app_user_id = <id_usuario>;  al abrir cada conexión
-- o transacción. Si no lo hace, el evento se guarda con id_usuario NULL.
CREATE PROCEDURE sp_auditar(
  IN p_tabla VARCHAR(50), IN p_operacion VARCHAR(10), IN p_id INT,
  IN p_campo VARCHAR(50), IN p_anterior VARCHAR(255), IN p_nuevo VARCHAR(255))
BEGIN
  INSERT INTO auditoria (id_usuario, tabla, operacion, id_registro, campo, valor_anterior, valor_nuevo)
  VALUES (@app_user_id, p_tabla, p_operacion, p_id, p_campo, p_anterior, p_nuevo);
END$$

-- =====================================================================
-- 9. TRIGGERS
-- =====================================================================

-- RF-USR-02: un usuario con rol DOCENTE debe estar vinculado a un docente
CREATE TRIGGER trg_usuarios_bi BEFORE INSERT ON usuarios FOR EACH ROW
BEGIN
  IF NEW.id_docente IS NULL AND NEW.id_rol = (SELECT id_rol FROM roles WHERE nombre = 'DOCENTE') THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Un usuario con rol DOCENTE debe estar vinculado a un docente (RF-USR-02)';
  END IF;
END$$

CREATE TRIGGER trg_usuarios_bu BEFORE UPDATE ON usuarios FOR EACH ROW
BEGIN
  IF NEW.id_docente IS NULL AND NEW.id_rol = (SELECT id_rol FROM roles WHERE nombre = 'DOCENTE') THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Un usuario con rol DOCENTE debe estar vinculado a un docente (RF-USR-02)';
  END IF;
END$$

-- RNF-05: auditoría de calificaciones (actas y notas de cursada) y de asistencias
CREATE TRIGGER trg_actas_ai AFTER INSERT ON actas_examen FOR EACH ROW
BEGIN
  CALL sp_auditar('actas_examen', 'INSERT', NEW.id_acta, NULL, NULL,
    CONCAT('estado=', NEW.estado, ', nota=', IFNULL(CAST(NEW.nota AS CHAR), 'NULL')));
END$$

CREATE TRIGGER trg_actas_au AFTER UPDATE ON actas_examen FOR EACH ROW
BEGIN
  IF NOT (OLD.nota <=> NEW.nota) THEN
    CALL sp_auditar('actas_examen', 'UPDATE', NEW.id_acta, 'nota',
                    CAST(OLD.nota AS CHAR), CAST(NEW.nota AS CHAR));
  END IF;
  IF OLD.estado <> NEW.estado THEN
    CALL sp_auditar('actas_examen', 'UPDATE', NEW.id_acta, 'estado', OLD.estado, NEW.estado);
  END IF;
  IF OLD.fecha_examen <> NEW.fecha_examen THEN
    CALL sp_auditar('actas_examen', 'UPDATE', NEW.id_acta, 'fecha_examen',
                    CAST(OLD.fecha_examen AS CHAR), CAST(NEW.fecha_examen AS CHAR));
  END IF;
  IF OLD.libro <> NEW.libro THEN
    CALL sp_auditar('actas_examen', 'UPDATE', NEW.id_acta, 'libro', OLD.libro, NEW.libro);
  END IF;
  IF OLD.folio <> NEW.folio THEN
    CALL sp_auditar('actas_examen', 'UPDATE', NEW.id_acta, 'folio', OLD.folio, NEW.folio);
  END IF;
  IF OLD.activo <> NEW.activo THEN
    CALL sp_auditar('actas_examen', 'UPDATE', NEW.id_acta, 'activo',
                    CAST(OLD.activo AS CHAR), CAST(NEW.activo AS CHAR));
  END IF;
END$$

CREATE TRIGGER trg_actas_ad AFTER DELETE ON actas_examen FOR EACH ROW
BEGIN
  CALL sp_auditar('actas_examen', 'DELETE', OLD.id_acta, NULL,
    CONCAT('estado=', OLD.estado, ', nota=', IFNULL(CAST(OLD.nota AS CHAR), 'NULL')), NULL);
END$$

CREATE TRIGGER trg_notas_ai AFTER INSERT ON notas_cursada FOR EACH ROW
BEGIN
  CALL sp_auditar('notas_cursada', 'INSERT', NEW.id_nota, 'nota', NULL, CAST(NEW.nota AS CHAR));
END$$

CREATE TRIGGER trg_notas_au AFTER UPDATE ON notas_cursada FOR EACH ROW
BEGIN
  IF OLD.nota <> NEW.nota THEN
    CALL sp_auditar('notas_cursada', 'UPDATE', NEW.id_nota, 'nota',
                    CAST(OLD.nota AS CHAR), CAST(NEW.nota AS CHAR));
  END IF;
  IF OLD.activo <> NEW.activo THEN
    CALL sp_auditar('notas_cursada', 'UPDATE', NEW.id_nota, 'activo',
                    CAST(OLD.activo AS CHAR), CAST(NEW.activo AS CHAR));
  END IF;
END$$

CREATE TRIGGER trg_notas_ad AFTER DELETE ON notas_cursada FOR EACH ROW
BEGIN
  CALL sp_auditar('notas_cursada', 'DELETE', OLD.id_nota, 'nota', CAST(OLD.nota AS CHAR), NULL);
END$$

CREATE TRIGGER trg_asistencias_ai AFTER INSERT ON asistencias FOR EACH ROW
BEGIN
  CALL sp_auditar('asistencias', 'INSERT', NEW.id_asistencia, 'estado', NULL, NEW.estado);
END$$

CREATE TRIGGER trg_asistencias_au AFTER UPDATE ON asistencias FOR EACH ROW
BEGIN
  IF OLD.estado <> NEW.estado THEN
    CALL sp_auditar('asistencias', 'UPDATE', NEW.id_asistencia, 'estado', OLD.estado, NEW.estado);
  END IF;
  IF OLD.activo <> NEW.activo THEN
    CALL sp_auditar('asistencias', 'UPDATE', NEW.id_asistencia, 'activo',
                    CAST(OLD.activo AS CHAR), CAST(NEW.activo AS CHAR));
  END IF;
END$$

CREATE TRIGGER trg_asistencias_ad AFTER DELETE ON asistencias FOR EACH ROW
BEGIN
  CALL sp_auditar('asistencias', 'DELETE', OLD.id_asistencia, 'estado', OLD.estado, NULL);
END$$

-- Datos sensibles de alumnos y usuarios: cambios de legajo, DNI, baja, rol y vinculación docente.
-- (No se audita ultimo_acceso, para no llenar la tabla en cada inicio de sesión.)
CREATE TRIGGER trg_alumnos_au AFTER UPDATE ON alumnos FOR EACH ROW
BEGIN
  IF OLD.legajo <> NEW.legajo THEN
    CALL sp_auditar('alumnos', 'UPDATE', NEW.id_alumno, 'legajo',
                    CAST(OLD.legajo AS CHAR), CAST(NEW.legajo AS CHAR));
  END IF;
  IF OLD.dni <> NEW.dni THEN
    CALL sp_auditar('alumnos', 'UPDATE', NEW.id_alumno, 'dni', OLD.dni, NEW.dni);
  END IF;
  IF OLD.activo <> NEW.activo THEN
    CALL sp_auditar('alumnos', 'UPDATE', NEW.id_alumno, 'activo',
                    CAST(OLD.activo AS CHAR), CAST(NEW.activo AS CHAR));
  END IF;
END$$

CREATE TRIGGER trg_usuarios_ai AFTER INSERT ON usuarios FOR EACH ROW
BEGIN
  CALL sp_auditar('usuarios', 'INSERT', NEW.id_usuario, 'id_rol', NULL, CAST(NEW.id_rol AS CHAR));
END$$

CREATE TRIGGER trg_usuarios_au AFTER UPDATE ON usuarios FOR EACH ROW
BEGIN
  IF OLD.id_rol <> NEW.id_rol THEN
    CALL sp_auditar('usuarios', 'UPDATE', NEW.id_usuario, 'id_rol',
                    CAST(OLD.id_rol AS CHAR), CAST(NEW.id_rol AS CHAR));
  END IF;
  IF NOT (OLD.id_docente <=> NEW.id_docente) THEN
    CALL sp_auditar('usuarios', 'UPDATE', NEW.id_usuario, 'id_docente',
                    CAST(OLD.id_docente AS CHAR), CAST(NEW.id_docente AS CHAR));
  END IF;
  IF OLD.activo <> NEW.activo THEN
    CALL sp_auditar('usuarios', 'UPDATE', NEW.id_usuario, 'activo',
                    CAST(OLD.activo AS CHAR), CAST(NEW.activo AS CHAR));
  END IF;
END$$

DELIMITER ;
