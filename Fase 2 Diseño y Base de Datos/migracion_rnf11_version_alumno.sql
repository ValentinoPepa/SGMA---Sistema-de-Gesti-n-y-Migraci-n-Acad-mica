-- Ejecutar una sola vez sobre la base de datos SGMA seleccionada en Workbench.
-- Agrega control optimista de concurrencia a la edicion de alumnos.
-- Antes de ejecutar, verificar con SELECT DATABASE() que la base elegida es correcta.

SELECT DATABASE() AS base_destino;

ALTER TABLE alumnos
  ADD COLUMN version INT NOT NULL DEFAULT 1 AFTER activo;

DROP TRIGGER IF EXISTS trg_alumnos_au;

DELIMITER $$
CREATE TRIGGER trg_alumnos_au AFTER UPDATE ON alumnos FOR EACH ROW
BEGIN
  IF OLD.legajo <> NEW.legajo THEN
    CALL sp_auditar('alumnos', 'UPDATE', NEW.id_alumno, 'legajo',
                    CAST(OLD.legajo AS CHAR), CAST(NEW.legajo AS CHAR));
  END IF;
  IF OLD.dni <> NEW.dni THEN
    CALL sp_auditar('alumnos', 'UPDATE', NEW.id_alumno, 'dni', OLD.dni, NEW.dni);
  END IF;
  IF OLD.nombre <> NEW.nombre THEN
    CALL sp_auditar('alumnos', 'UPDATE', NEW.id_alumno, 'nombre', OLD.nombre, NEW.nombre);
  END IF;
  IF OLD.apellido <> NEW.apellido THEN
    CALL sp_auditar('alumnos', 'UPDATE', NEW.id_alumno, 'apellido', OLD.apellido, NEW.apellido);
  END IF;
  IF NOT (OLD.email <=> NEW.email) THEN
    CALL sp_auditar('alumnos', 'UPDATE', NEW.id_alumno, 'email', OLD.email, NEW.email);
  END IF;
  IF OLD.activo <> NEW.activo THEN
    CALL sp_auditar('alumnos', 'UPDATE', NEW.id_alumno, 'activo',
                    CAST(OLD.activo AS CHAR), CAST(NEW.activo AS CHAR));
  END IF;
END$$
DELIMITER ;
