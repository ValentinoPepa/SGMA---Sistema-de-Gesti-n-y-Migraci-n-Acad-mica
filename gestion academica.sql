CREATE DATABASE IF NOT EXISTS gestion_academica;
USE gestion_academica;

-- 1. Tabla de Carreras
CREATE TABLE Carreras (
    id_carrera INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- 2. Tabla de Materias
CREATE TABLE Materias (
    id_materia INT AUTO_INCREMENT PRIMARY KEY,
    id_carrera INT NOT NULL,
    codigo VARCHAR(10) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    anio_nivel TINYINT NOT NULL CHECK (anio_nivel BETWEEN 1 AND 5),
    FOREIGN KEY (id_carrera) REFERENCES Carreras(id_carrera) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 3. Tabla de Alumnos
CREATE TABLE Alumnos (
    id_alumno INT AUTO_INCREMENT PRIMARY KEY,
    legajo INT NOT NULL UNIQUE,
    dni VARCHAR(15) NOT NULL UNIQUE,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    fecha_nacimiento DATE NULL,
    email VARCHAR(100) NULL,
    INDEX idx_dni (dni),
    INDEX idx_legajo (legajo)
) ENGINE=InnoDB;

-- 4. Tabla de Inscripciones / Cursadas
CREATE TABLE Inscripciones (
    id_inscripcion INT AUTO_INCREMENT PRIMARY KEY,
    id_alumno INT NOT NULL,
    id_materia INT NOT NULL,
    anio_lectivo SMALLINT NOT NULL,
    estado ENUM('CURSANDO', 'REGULAR', 'PROMOCIONADO', 'LIBRE') DEFAULT 'CURSANDO',
    FOREIGN KEY (id_alumno) REFERENCES Alumnos(id_alumno) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (id_materia) REFERENCES Materias(id_materia) ON DELETE RESTRICT ON UPDATE CASCADE,
    UNIQUE KEY uk_alumno_materia_anio (id_alumno, id_materia, anio_lectivo)
) ENGINE=InnoDB;

-- 5. Tabla de Actas de Examen
CREATE TABLE Actas_Examen (
    id_acta INT AUTO_INCREMENT PRIMARY KEY,
    id_alumno INT NOT NULL,
    id_materia INT NOT NULL,
    nota DECIMAL(4,2) NULL CHECK (nota BETWEEN 1.00 AND 10.00),
    fecha_examen DATE NOT NULL,
    libro VARCHAR(20) NOT NULL,
    folio VARCHAR(20) NOT NULL,
    estado ENUM('APROBADO', 'DESAPROBADO', 'AUSENTE') NOT NULL,
    FOREIGN KEY (id_alumno) REFERENCES Alumnos(id_alumno) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (id_materia) REFERENCES Materias(id_materia) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_acta_alumno (id_alumno)
) ENGINE=InnoDB;

-- 6. Tabla de Auditoría (Cumplimiento de RNF-05)
CREATE TABLE Auditoria (
    id_auditoria INT AUTO_INCREMENT PRIMARY KEY,
    tabla_afectada VARCHAR(50) NOT NULL,
    operacion ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    id_registro INT NOT NULL,
    usuario VARCHAR(50) DEFAULT (CURRENT_USER()),
    fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    detalle VARCHAR(255) NULL
) ENGINE=InnoDB;