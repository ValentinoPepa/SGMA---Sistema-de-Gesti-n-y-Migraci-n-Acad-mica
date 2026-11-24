-- MariaDB dump 10.19  Distrib 10.4.32-MariaDB, for Win64 (AMD64)
--
-- Host: 127.0.0.1    Database: gestion_academica_v2
-- ------------------------------------------------------
-- Server version	10.4.32-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `actas_examen`
--

DROP TABLE IF EXISTS `actas_examen`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `actas_examen` (
  `id_acta` int(11) NOT NULL AUTO_INCREMENT,
  `id_alumno` int(11) NOT NULL,
  `id_materia` int(11) NOT NULL,
  `id_mesa` int(11) DEFAULT NULL,
  `fecha_examen` date NOT NULL,
  `libro` varchar(20) NOT NULL,
  `folio` varchar(20) NOT NULL,
  `nota` decimal(4,2) DEFAULT NULL,
  `estado` enum('APROBADO','DESAPROBADO','AUSENTE') NOT NULL,
  `origen` enum('MANUAL','MASIVA','MIGRACION') NOT NULL DEFAULT 'MANUAL',
  `id_lote` int(11) DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id_acta`),
  KEY `idx_acta_alumno` (`id_alumno`),
  KEY `fk_actas_materia` (`id_materia`),
  KEY `fk_actas_mesa` (`id_mesa`,`id_materia`),
  KEY `fk_actas_lote` (`id_lote`),
  CONSTRAINT `fk_actas_alumno` FOREIGN KEY (`id_alumno`) REFERENCES `alumnos` (`id_alumno`),
  CONSTRAINT `fk_actas_lote` FOREIGN KEY (`id_lote`) REFERENCES `lotes_carga` (`id_lote`),
  CONSTRAINT `fk_actas_materia` FOREIGN KEY (`id_materia`) REFERENCES `materias` (`id_materia`),
  CONSTRAINT `fk_actas_mesa` FOREIGN KEY (`id_mesa`, `id_materia`) REFERENCES `mesas_examen` (`id_mesa`, `id_materia`),
  CONSTRAINT `chk_actas_nota_rango` CHECK (`nota` between 1.00 and 10.00),
  CONSTRAINT `chk_actas_nota_estado` CHECK (`estado` = 'AUSENTE' and `nota` is null or `estado` <> 'AUSENTE' and `nota` is not null)
) ENGINE=InnoDB AUTO_INCREMENT=190 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `actas_examen`
--

LOCK TABLES `actas_examen` WRITE;
/*!40000 ALTER TABLE `actas_examen` DISABLE KEYS */;
INSERT INTO `actas_examen` VALUES (1,65,13,NULL,'2026-02-05','L4','F106',6.50,'APROBADO','MIGRACION',1,1),(2,56,14,NULL,'2024-08-12','L24','F53',7.00,'APROBADO','MIGRACION',1,1),(3,44,10,NULL,'2022-04-28','L23','F194',7.00,'APROBADO','MIGRACION',1,1),(4,47,8,NULL,'2022-05-31','L13','F100',1.00,'DESAPROBADO','MIGRACION',1,1),(5,17,3,NULL,'2025-09-23','L30','F186',1.00,'DESAPROBADO','MIGRACION',1,1),(6,68,20,NULL,'2022-04-13','L10','F8',10.00,'APROBADO','MIGRACION',1,1),(7,1,1,NULL,'2022-07-14','L11','F127',8.50,'APROBADO','MIGRACION',1,1),(8,42,13,NULL,'2024-11-27','L18','F64',1.00,'DESAPROBADO','MIGRACION',1,1),(9,31,2,NULL,'2022-11-04','L18','F62',NULL,'AUSENTE','MIGRACION',1,1),(10,74,7,NULL,'2025-05-08','L4','F55',4.50,'APROBADO','MIGRACION',1,1),(11,53,6,NULL,'2026-03-16','L27','F12',8.50,'APROBADO','MIGRACION',1,1),(12,72,5,NULL,'2025-05-16','L3','F49',6.00,'APROBADO','MIGRACION',1,1),(13,30,17,NULL,'2026-07-30','L13','F84',NULL,'AUSENTE','MIGRACION',1,1),(14,54,2,NULL,'2026-01-16','L29','F26',8.50,'APROBADO','MIGRACION',1,1),(15,76,4,NULL,'2023-09-11','L26','F5',10.00,'APROBADO','MIGRACION',1,1),(16,17,7,NULL,'2023-08-30','L26','F174',6.50,'APROBADO','MIGRACION',1,1),(17,70,20,NULL,'2024-07-09','L21','F30',8.50,'APROBADO','MIGRACION',1,1),(18,57,4,NULL,'2024-02-06','L17','F142',4.50,'APROBADO','MIGRACION',1,1),(19,55,16,NULL,'2022-11-02','L16','F161',6.50,'APROBADO','MIGRACION',1,1),(20,10,3,NULL,'2026-02-17','L21','F59',9.50,'APROBADO','MIGRACION',1,1),(21,64,12,NULL,'2022-12-06','L4','F72',8.00,'APROBADO','MIGRACION',1,1),(22,69,7,NULL,'2025-07-15','L10','F103',3.00,'DESAPROBADO','MIGRACION',1,1),(23,69,4,NULL,'2025-01-06','L4','F150',8.50,'APROBADO','MIGRACION',1,1),(24,17,2,NULL,'2022-06-08','L20','F118',3.00,'DESAPROBADO','MIGRACION',1,1),(25,37,16,NULL,'2026-10-12','L8','F34',5.00,'APROBADO','MIGRACION',1,1),(26,6,15,NULL,'2025-03-21','L27','F51',10.00,'APROBADO','MIGRACION',1,1),(27,61,22,NULL,'2024-06-10','L30','F87',4.00,'APROBADO','MIGRACION',1,1),(28,26,14,NULL,'2022-11-09','L27','F32',8.50,'APROBADO','MIGRACION',1,1),(29,28,1,NULL,'2023-12-13','L21','F37',2.00,'DESAPROBADO','MIGRACION',1,1),(30,62,3,NULL,'2024-05-01','L5','F122',1.00,'DESAPROBADO','MIGRACION',1,1),(31,7,15,NULL,'2023-02-09','L25','F180',NULL,'AUSENTE','MIGRACION',1,1),(32,49,3,NULL,'2025-06-30','L16','F145',5.00,'APROBADO','MIGRACION',1,1),(33,25,12,NULL,'2026-03-12','L25','F141',8.50,'APROBADO','MIGRACION',1,1),(34,20,3,NULL,'2023-05-23','L17','F87',2.00,'DESAPROBADO','MIGRACION',1,1),(35,25,8,NULL,'2022-05-09','L15','F70',6.00,'APROBADO','MIGRACION',1,1),(36,79,16,NULL,'2024-10-09','L11','F182',7.00,'APROBADO','MIGRACION',1,1),(37,37,18,NULL,'2023-09-13','L17','F3',9.50,'APROBADO','MIGRACION',1,1),(38,25,1,NULL,'2023-09-01','L25','F107',9.50,'APROBADO','MIGRACION',1,1),(39,57,8,NULL,'2022-11-29','L29','F137',3.00,'DESAPROBADO','MIGRACION',1,1),(40,78,15,NULL,'2025-11-06','L28','F16',6.00,'APROBADO','MIGRACION',1,1),(41,13,13,NULL,'2026-08-11','L13','F50',2.00,'DESAPROBADO','MIGRACION',1,1),(42,40,20,NULL,'2023-10-13','L16','F40',1.00,'DESAPROBADO','MIGRACION',1,1),(43,64,1,NULL,'2022-10-28','L19','F76',3.00,'DESAPROBADO','MIGRACION',1,1),(44,49,4,NULL,'2026-04-13','L29','F42',7.00,'APROBADO','MIGRACION',1,1),(45,41,3,NULL,'2022-03-28','L3','F135',6.00,'APROBADO','MIGRACION',1,1),(46,59,16,NULL,'2026-07-08','L3','F47',9.00,'APROBADO','MIGRACION',1,1),(47,17,8,NULL,'2023-02-01','L9','F147',9.50,'APROBADO','MIGRACION',1,1),(48,80,7,NULL,'2024-04-04','L26','F93',1.00,'DESAPROBADO','MIGRACION',1,1),(49,47,2,NULL,'2024-07-05','L13','F110',6.50,'APROBADO','MIGRACION',1,1),(50,50,19,NULL,'2022-11-01','L30','F141',3.00,'DESAPROBADO','MIGRACION',1,1),(51,33,2,NULL,'2023-03-03','L28','F93',10.00,'APROBADO','MIGRACION',1,1),(52,10,5,NULL,'2023-10-16','L10','F150',8.00,'APROBADO','MIGRACION',1,1),(53,11,4,NULL,'2025-07-24','L11','F25',7.00,'APROBADO','MIGRACION',1,1),(54,14,19,NULL,'2024-03-21','L2','F110',7.50,'APROBADO','MIGRACION',1,1),(55,28,11,NULL,'2023-12-06','L5','F94',8.50,'APROBADO','MIGRACION',1,1),(56,29,17,NULL,'2025-09-01','L16','F20',9.00,'APROBADO','MIGRACION',1,1),(57,3,14,NULL,'2026-05-22','L14','F93',5.00,'APROBADO','MIGRACION',1,1),(58,60,4,NULL,'2026-03-13','L27','F6',5.00,'APROBADO','MIGRACION',1,1),(59,22,19,NULL,'2025-04-17','L24','F136',6.00,'APROBADO','MIGRACION',1,1),(60,31,11,NULL,'2023-06-05','L26','F88',8.00,'APROBADO','MIGRACION',1,1),(61,12,12,NULL,'2024-04-11','L14','F150',9.00,'APROBADO','MIGRACION',1,1),(62,42,19,NULL,'2022-11-24','L23','F148',NULL,'AUSENTE','MIGRACION',1,1),(63,80,8,NULL,'2022-04-26','L17','F102',8.50,'APROBADO','MIGRACION',1,1),(64,51,16,NULL,'2026-09-22','L25','F154',4.50,'APROBADO','MIGRACION',1,1),(65,15,18,NULL,'2026-04-14','L23','F100',4.00,'APROBADO','MIGRACION',1,1),(66,75,23,NULL,'2025-09-08','L23','F82',10.00,'APROBADO','MIGRACION',1,1),(67,5,24,NULL,'2024-06-12','L26','F96',3.00,'DESAPROBADO','MIGRACION',1,1),(68,74,3,NULL,'2022-03-14','L14','F155',NULL,'AUSENTE','MIGRACION',1,1),(69,49,1,NULL,'2025-06-10','L9','F8',6.00,'APROBADO','MIGRACION',1,1),(70,23,14,NULL,'2025-12-29','L9','F81',2.00,'DESAPROBADO','MIGRACION',1,1),(71,30,20,NULL,'2024-10-09','L6','F53',4.00,'APROBADO','MIGRACION',1,1),(72,52,16,NULL,'2026-05-13','L11','F190',10.00,'APROBADO','MIGRACION',1,1),(73,59,22,NULL,'2022-05-09','L4','F38',3.00,'DESAPROBADO','MIGRACION',1,1),(74,15,16,NULL,'2022-11-15','L9','F49',2.00,'DESAPROBADO','MIGRACION',1,1),(75,44,9,NULL,'2022-08-19','L7','F47',1.00,'DESAPROBADO','MIGRACION',1,1),(76,9,22,NULL,'2025-05-28','L21','F17',9.50,'APROBADO','MIGRACION',1,1),(77,61,13,NULL,'2023-09-05','L14','F17',8.50,'APROBADO','MIGRACION',1,1),(78,39,16,NULL,'2026-09-14','L26','F40',9.00,'APROBADO','MIGRACION',1,1),(79,80,2,NULL,'2024-11-26','L8','F62',3.00,'DESAPROBADO','MIGRACION',1,1),(80,41,7,NULL,'2025-05-02','L8','F41',4.50,'APROBADO','MIGRACION',1,1),(81,51,20,NULL,'2022-12-08','L26','F166',4.50,'APROBADO','MIGRACION',1,1),(82,11,3,NULL,'2025-07-01','L15','F78',9.00,'APROBADO','MIGRACION',1,1),(83,9,13,NULL,'2023-08-24','L12','F75',7.50,'APROBADO','MIGRACION',1,1),(84,55,22,NULL,'2022-06-20','L10','F130',7.00,'APROBADO','MIGRACION',1,1),(85,15,17,NULL,'2026-08-13','L13','F113',7.50,'APROBADO','MIGRACION',1,1),(86,13,20,NULL,'2026-02-20','L30','F70',6.50,'APROBADO','MIGRACION',1,1),(87,77,13,NULL,'2026-01-30','L1','F136',7.00,'APROBADO','MIGRACION',1,1),(88,19,13,NULL,'2022-08-05','L3','F146',5.00,'APROBADO','MIGRACION',1,1),(89,66,5,NULL,'2023-10-09','L23','F66',8.00,'APROBADO','MIGRACION',1,1),(90,70,18,NULL,'2024-07-02','L11','F58',6.00,'APROBADO','MIGRACION',1,1),(91,23,17,NULL,'2025-06-17','L4','F31',9.00,'APROBADO','MIGRACION',1,1),(92,39,19,NULL,'2022-11-21','L13','F166',9.00,'APROBADO','MIGRACION',1,1),(93,61,14,NULL,'2025-04-08','L13','F169',7.50,'APROBADO','MIGRACION',1,1),(94,67,16,NULL,'2024-11-28','L10','F57',9.50,'APROBADO','MIGRACION',1,1),(95,72,7,NULL,'2022-05-31','L19','F195',7.00,'APROBADO','MIGRACION',1,1),(96,70,15,NULL,'2023-03-01','L23','F16',NULL,'AUSENTE','MIGRACION',1,1),(97,24,14,NULL,'2024-03-06','L16','F198',8.50,'APROBADO','MIGRACION',1,1),(98,43,18,NULL,'2026-01-21','L10','F2',10.00,'APROBADO','MIGRACION',1,1),(99,68,23,NULL,'2022-03-23','L17','F6',4.00,'APROBADO','MIGRACION',1,1),(100,50,16,NULL,'2024-11-26','L29','F65',8.50,'APROBADO','MIGRACION',1,1),(101,18,20,NULL,'2023-03-28','L16','F16',9.50,'APROBADO','MIGRACION',1,1),(102,25,2,NULL,'2025-04-11','L15','F51',7.00,'APROBADO','MIGRACION',1,1),(103,57,2,NULL,'2025-09-08','L23','F69',1.00,'DESAPROBADO','MIGRACION',1,1),(104,32,5,NULL,'2026-09-02','L29','F100',4.00,'APROBADO','MIGRACION',1,1),(105,67,20,NULL,'2026-02-12','L7','F71',3.00,'DESAPROBADO','MIGRACION',1,1),(106,3,13,NULL,'2022-04-12','L2','F8',10.00,'APROBADO','MIGRACION',1,1),(107,52,14,NULL,'2026-09-10','L21','F68',1.00,'DESAPROBADO','MIGRACION',1,1),(108,18,14,NULL,'2023-04-25','L17','F52',9.50,'APROBADO','MIGRACION',1,1),(109,33,4,NULL,'2023-04-12','L3','F154',8.00,'APROBADO','MIGRACION',1,1),(110,73,5,NULL,'2025-02-24','L24','F40',10.00,'APROBADO','MIGRACION',1,1),(111,66,8,NULL,'2022-03-25','L14','F29',6.00,'APROBADO','MIGRACION',1,1),(112,34,6,NULL,'2026-02-11','L15','F94',8.00,'APROBADO','MIGRACION',1,1),(113,34,7,NULL,'2026-06-29','L14','F14',9.50,'APROBADO','MIGRACION',1,1),(114,29,18,NULL,'2023-04-18','L13','F91',8.00,'APROBADO','MIGRACION',1,1),(115,16,20,NULL,'2023-10-09','L11','F142',9.00,'APROBADO','MIGRACION',1,1),(116,27,24,NULL,'2022-09-01','L26','F84',8.50,'APROBADO','MIGRACION',1,1),(117,68,16,NULL,'2023-06-02','L21','F27',10.00,'APROBADO','MIGRACION',1,1),(118,8,20,NULL,'2026-07-27','L10','F68',1.00,'DESAPROBADO','MIGRACION',1,1),(119,74,1,NULL,'2023-02-06','L5','F29',4.50,'APROBADO','MIGRACION',1,1),(120,4,16,NULL,'2022-07-04','L10','F140',9.00,'APROBADO','MIGRACION',1,1),(121,46,10,NULL,'2024-12-03','L14','F11',2.00,'DESAPROBADO','MIGRACION',1,1),(122,42,15,NULL,'2022-06-21','L14','F130',9.50,'APROBADO','MIGRACION',1,1),(123,55,18,NULL,'2025-01-30','L17','F29',6.50,'APROBADO','MIGRACION',1,1),(124,12,7,NULL,'2024-09-13','L21','F89',7.50,'APROBADO','MIGRACION',1,1),(125,58,13,NULL,'2022-11-18','L15','F102',10.00,'APROBADO','MIGRACION',1,1),(126,44,3,NULL,'2022-05-19','L3','F117',NULL,'AUSENTE','MIGRACION',1,1),(127,14,21,NULL,'2023-06-12','L3','F134',3.00,'DESAPROBADO','MIGRACION',1,1),(128,51,22,NULL,'2022-09-14','L7','F90',10.00,'APROBADO','MIGRACION',1,1),(129,19,16,NULL,'2022-03-21','L15','F88',8.50,'APROBADO','MIGRACION',1,1),(130,9,23,NULL,'2022-08-17','L24','F172',7.50,'APROBADO','MIGRACION',1,1),(131,59,14,NULL,'2024-03-11','L21','F198',3.00,'DESAPROBADO','MIGRACION',1,1),(132,42,20,NULL,'2022-05-27','L23','F16',8.50,'APROBADO','MIGRACION',1,1),(133,53,1,NULL,'2026-03-04','L21','F66',9.50,'APROBADO','MIGRACION',1,1),(134,50,13,NULL,'2025-06-30','L20','F89',8.00,'APROBADO','MIGRACION',1,1),(135,65,19,NULL,'2022-11-23','L20','F87',1.00,'DESAPROBADO','MIGRACION',1,1),(136,51,13,NULL,'2026-07-28','L17','F116',6.00,'APROBADO','MIGRACION',1,1),(137,39,22,NULL,'2022-11-01','L10','F178',8.00,'APROBADO','MIGRACION',1,1),(138,79,14,NULL,'2023-01-16','L26','F166',6.00,'APROBADO','MIGRACION',1,1),(139,35,7,NULL,'2026-07-24','L18','F56',5.00,'APROBADO','MIGRACION',1,1),(140,15,13,NULL,'2022-12-06','L1','F48',6.50,'APROBADO','MIGRACION',1,1),(141,15,19,NULL,'2023-06-13','L24','F104',1.00,'DESAPROBADO','MIGRACION',1,1),(142,11,5,NULL,'2026-03-30','L17','F12',8.50,'APROBADO','MIGRACION',1,1),(143,69,2,NULL,'2024-10-07','L25','F118',3.00,'DESAPROBADO','MIGRACION',1,1),(144,63,2,NULL,'2022-03-04','L28','F149',2.00,'DESAPROBADO','MIGRACION',1,1),(145,51,24,NULL,'2023-04-06','L22','F35',9.50,'APROBADO','MIGRACION',1,1),(146,68,13,NULL,'2026-03-23','L18','F68',2.00,'DESAPROBADO','MIGRACION',1,1),(147,44,2,NULL,'2023-11-16','L25','F128',NULL,'AUSENTE','MIGRACION',1,1),(148,77,18,NULL,'2024-09-02','L2','F121',5.00,'APROBADO','MIGRACION',1,1),(149,8,18,NULL,'2023-08-11','L2','F30',10.00,'APROBADO','MIGRACION',1,1),(150,18,13,NULL,'2024-10-02','L13','F48',6.00,'APROBADO','MIGRACION',1,1),(151,70,16,NULL,'2022-05-31','L1','F86',4.50,'APROBADO','MIGRACION',1,1),(152,3,21,NULL,'2024-10-10','L29','F185',5.00,'APROBADO','MIGRACION',1,1),(153,74,12,NULL,'2024-06-12','L21','F92',4.00,'APROBADO','MIGRACION',1,1),(154,61,18,NULL,'2024-03-19','L19','F23',2.00,'DESAPROBADO','MIGRACION',1,1),(155,56,19,NULL,'2023-02-28','L17','F26',9.00,'APROBADO','MIGRACION',1,1),(156,38,15,NULL,'2024-10-07','L8','F108',5.00,'APROBADO','MIGRACION',1,1),(157,80,5,NULL,'2022-11-16','L18','F190',7.50,'APROBADO','MIGRACION',1,1),(158,35,8,NULL,'2023-04-03','L11','F62',6.00,'APROBADO','MIGRACION',1,1),(159,32,7,NULL,'2023-03-03','L13','F78',5.00,'APROBADO','MIGRACION',1,1),(160,3,15,NULL,'2025-04-01','L12','F157',10.00,'APROBADO','MIGRACION',1,1),(161,31,3,NULL,'2023-05-12','L20','F33',8.50,'APROBADO','MIGRACION',1,1),(162,66,11,NULL,'2024-05-02','L4','F101',9.00,'APROBADO','MIGRACION',1,1),(163,50,15,NULL,'2026-10-13','L14','F12',8.00,'APROBADO','MIGRACION',1,1),(164,76,6,NULL,'2026-09-17','L10','F95',2.00,'DESAPROBADO','MIGRACION',1,1),(165,12,6,NULL,'2026-10-12','L25','F112',8.50,'APROBADO','MIGRACION',1,1),(166,21,15,NULL,'2025-04-25','L28','F99',3.00,'DESAPROBADO','MIGRACION',1,1),(167,66,2,NULL,'2024-11-19','L2','F28',8.00,'APROBADO','MIGRACION',1,1),(168,11,11,NULL,'2022-11-07','L14','F192',10.00,'APROBADO','MIGRACION',1,1),(169,33,11,NULL,'2022-08-31','L3','F162',9.00,'APROBADO','MIGRACION',1,1),(170,39,17,NULL,'2022-10-31','L6','F86',6.50,'APROBADO','MIGRACION',1,1),(171,17,1,NULL,'2026-10-08','L1','F192',8.50,'APROBADO','MIGRACION',1,1),(172,2,16,NULL,'2025-10-09','L7','F76',1.00,'DESAPROBADO','MIGRACION',1,1),(173,27,15,NULL,'2022-07-18','L23','F158',10.00,'APROBADO','MIGRACION',1,1),(174,36,16,NULL,'2023-05-26','L11','F122',7.00,'APROBADO','MIGRACION',1,1),(175,30,18,NULL,'2025-10-07','L6','F39',4.50,'APROBADO','MIGRACION',1,1),(176,13,19,NULL,'2024-06-24','L4','F166',7.50,'APROBADO','MIGRACION',1,1),(177,77,14,NULL,'2026-01-30','L9','F180',4.50,'APROBADO','MIGRACION',1,1),(178,74,6,NULL,'2023-02-24','L19','F150',6.00,'APROBADO','MIGRACION',1,1),(179,71,16,NULL,'2024-12-26','L4','F4',10.00,'APROBADO','MIGRACION',1,1),(180,76,2,NULL,'2022-12-19','L20','F15',2.00,'DESAPROBADO','MIGRACION',1,1),(181,29,19,NULL,'2024-11-25','L18','F61',4.00,'APROBADO','MIGRACION',1,1),(182,30,22,NULL,'2025-11-10','L19','F134',5.00,'APROBADO','MIGRACION',1,1),(183,55,15,NULL,'2022-03-23','L17','F116',9.00,'APROBADO','MIGRACION',1,1),(184,14,15,NULL,'2023-04-27','L19','F19',5.00,'APROBADO','MIGRACION',1,1),(185,27,13,NULL,'2026-02-05','L29','F132',4.00,'APROBADO','MIGRACION',1,1),(186,79,13,NULL,'2024-05-20','L22','F184',7.50,'APROBADO','MIGRACION',1,1),(187,53,12,NULL,'2023-01-11','L3','F104',NULL,'AUSENTE','MIGRACION',1,1),(188,78,18,NULL,'2023-02-16','L10','F111',3.00,'DESAPROBADO','MIGRACION',1,1),(189,49,7,NULL,'2023-04-07','L9','F115',6.00,'APROBADO','MIGRACION',1,1);
/*!40000 ALTER TABLE `actas_examen` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_actas_ai AFTER INSERT ON actas_examen FOR EACH ROW
BEGIN
  CALL sp_auditar('actas_examen', 'INSERT', NEW.id_acta, NULL, NULL,
    CONCAT('estado=', NEW.estado, ', nota=', IFNULL(CAST(NEW.nota AS CHAR), 'NULL')));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_actas_au AFTER UPDATE ON actas_examen FOR EACH ROW
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
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_actas_ad AFTER DELETE ON actas_examen FOR EACH ROW
BEGIN
  CALL sp_auditar('actas_examen', 'DELETE', OLD.id_acta, NULL,
    CONCAT('estado=', OLD.estado, ', nota=', IFNULL(CAST(OLD.nota AS CHAR), 'NULL')), NULL);
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `alumnos`
--

DROP TABLE IF EXISTS `alumnos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `alumnos` (
  `id_alumno` int(11) NOT NULL AUTO_INCREMENT,
  `legajo` int(11) NOT NULL,
  `dni` varchar(15) NOT NULL,
  `nombre` varchar(50) NOT NULL,
  `apellido` varchar(50) NOT NULL,
  `fecha_nacimiento` date DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  `origen` enum('MANUAL','MASIVA','MIGRACION') NOT NULL DEFAULT 'MANUAL',
  `creado_en` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_alumno`),
  UNIQUE KEY `uq_alumnos_legajo` (`legajo`),
  UNIQUE KEY `uq_alumnos_dni` (`dni`),
  CONSTRAINT `chk_alumnos_dni` CHECK (`dni` regexp '^[0-9]+$')
) ENGINE=InnoDB AUTO_INCREMENT=81 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alumnos`
--

LOCK TABLES `alumnos` WRITE;
/*!40000 ALTER TABLE `alumnos` DISABLE KEYS */;
INSERT INTO `alumnos` VALUES (1,1001,'39998500','Bruno','Vega','2004-11-28','bruno.vega@outlook.com',1,'MIGRACION','2026-11-24 12:17:54'),(2,1002,'41746093','Brenda','Quiroga','2004-07-26','brenda.quiroga@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(3,1003,'45400346','Julieta','González','2005-02-04','julieta.gonzalez@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(4,1004,'39645033','Daniela','González','2006-08-22','daniela.gonzalez@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(5,1005,'41526984','María','Acosta','2001-06-26','maria.acosta@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(6,1006,'39280435','Gonzalo','Sánchez','2004-09-10','gonzalo.sanchez@gmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(7,1007,'45674700','Facundo','Navarro','2000-01-28','facundo.navarro@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(8,1008,'44099226','Natalia','Morales','1997-07-19','natalia.morales@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(9,1009,'39953672','Romina','Vega','2008-10-16','romina.vega@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(10,1010,'42339316','Paula','Navarro','2003-09-17',NULL,1,'MIGRACION','2026-11-24 12:17:54'),(11,1011,'41766902','Agustín','López','2007-09-22','agustin.lopez@gmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(12,1012,'45204296','Ramiro','Romero','2003-04-28',NULL,1,'MIGRACION','2026-11-24 12:17:54'),(13,1013,'45663770','Ramiro','Ledesma','2000-09-13','ramiro.ledesma@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(14,1014,'46420478','Ramiro','Rojas','2002-04-10','ramiro.rojas@gmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(15,1015,'38155640','Lucas','Romero','2006-10-15','lucas.romero@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(16,1016,'44038721','Camila','Acosta','2007-08-15',NULL,1,'MIGRACION','2026-11-24 12:17:54'),(17,1017,'45285161','Candela','Fernández','2000-06-15','candela.fernandez@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(18,1018,'45355987','Leandro','Acosta','2003-03-14','leandro.acosta@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(19,1019,'39078693','Agustina','Sosa','2001-02-07','agustina.sosa@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(20,1020,'40455491','Daniela','González','1997-01-15','daniela.gonzalez@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(21,1021,'41335171','Julieta','Gómez','2005-01-25','julieta.gomez@outlook.com',1,'MIGRACION','2026-11-24 12:17:54'),(22,1022,'43993671','Facundo','González','2001-11-19','facundo.gonzalez@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(23,1023,'40262652','Emiliano','Flores','2003-10-05','emiliano.flores@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(24,1084,'39416554','Paula','Álvarez','1998-10-10','paula.alvarez@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(25,1025,'44549947','Facundo','Luna','2008-04-13','facundo.luna@outlook.com',1,'MIGRACION','2026-11-24 12:17:54'),(26,1026,'39780632','Ana','Martínez','1996-06-21','ana.martinez@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(27,1027,'38432688','Martín','Vega','2003-06-22','martin.vega@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(28,1028,'45552102','Bruno','Gómez','2003-08-19','bruno.gomez@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(29,1029,'40581855','Rocío','Luna','1999-07-20','rocio.luna@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(30,1030,'45697676','Brenda','Flores',NULL,'brenda.flores@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(31,1031,'38572987','Camila','Torres','1996-11-18','camila.torres@gmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(32,1082,'43900575','Candela','Navarro','2008-09-07','candela.navarro@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(33,1032,'45580296','Camila','Cabrera','2007-11-01','camila.cabrera@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(34,1033,'41669571','Matías','Díaz','1998-11-28','matias.diaz@outlook.com',1,'MIGRACION','2026-11-24 12:17:54'),(35,1034,'44542635','Agustina','Morales','2004-07-28','agustina.morales@gmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(36,1085,'44428783','Carolina','Torres','2001-03-09','carolina.torres@gmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(37,1086,'46348383','Paula','Herrera','2003-03-11','paula.herrera@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(38,1037,'45458863','Tomás','Luna','2008-09-26',NULL,1,'MIGRACION','2026-11-24 12:17:54'),(39,1038,'39586554','Lucía','Flores','1996-02-15','lucia.flores@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(40,1081,'44286867','Ezequiel','Peralta','2006-08-18','ezequiel.peralta@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(41,1039,'44845145','Emiliano','Torres','1996-06-28',NULL,1,'MIGRACION','2026-11-24 12:17:54'),(42,1041,'42705543','Candela','Navarro','2007-04-19','candela.navarro@gmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(43,1042,'42497983','Candela','Díaz','1997-05-04','candela.diaz@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(44,1043,'40873519','Franco','López','2008-06-24','franco.lopez@gmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(45,1044,'39783754','Leandro','Aguirre','2000-10-27','leandro.aguirre@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(46,1045,'42882776','Bruno','Álvarez','2000-05-03',NULL,1,'MIGRACION','2026-11-24 12:17:54'),(47,1046,'44906212','Florencia','Ríos','1996-01-04',NULL,1,'MIGRACION','2026-11-24 12:17:54'),(48,1047,'38385501','Carolina','Gómez','1997-11-18','carolina.gomez@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(49,1048,'43284394','Natalia','Videla','2006-11-23','natalia.videla@gmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(50,1049,'44781192','Bruno','Videla','1999-10-15','bruno.videla@outlook.com',1,'MIGRACION','2026-11-24 12:17:54'),(51,1050,'40003874','Federico','Vega','2006-05-13','federico.vega@gmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(52,1051,'43978022','Mateo','Morales',NULL,'mateo.morales@gmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(53,1052,'42857938','Tomás','Suárez','2008-07-11','tomas.suarez@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(54,1053,'43745925','Camila','Correa','1996-12-04','camila.correa@outlook.com',1,'MIGRACION','2026-11-24 12:17:54'),(55,1054,'40058316','Tomás','Fernández','1998-09-12','tomas.fernandez@outlook.com',1,'MIGRACION','2026-11-24 12:17:54'),(56,1055,'38483086','Romina','Funes','1998-06-14','romina.funes@gmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(57,1056,'44328066','Julieta','Ríos','2006-04-25','julieta.rios@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(58,1057,'41078067','Emiliano','Rodríguez','2006-12-18','emiliano.rodriguez@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(59,1058,'42277759','Facundo','Flores','1996-01-09','facundo.flores@gmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(60,1059,'45010859','Florencia','Aguirre','1998-11-19','florencia.aguirre@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(61,1060,'41008192','Candela','Fernández','2006-09-27','candela.fernandez@gmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(62,1061,'43716215','Matías','Aguirre','1996-11-27','matias.aguirre@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(63,1062,'42073617','Ramiro','López','1999-11-17','ramiro.lopez@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(64,1063,'44695356','Federico','Flores','2004-05-11','federico.flores@gmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(65,1065,'43237740','Camila','Álvarez','2006-07-05','camila.alvarez@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(66,1066,'38089117','Ezequiel','Luna','2007-07-26','ezequiel.luna@gmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(67,1067,'40895290','Nicolás','Suárez','2001-09-24','nicolas.suarez@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(68,1068,'40314594','Franco','Rodríguez','2004-04-28','franco.rodriguez@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(69,1087,'38748986','María','Molina','2004-09-26',NULL,1,'MIGRACION','2026-11-24 12:17:54'),(70,1070,'39760290','Nicolás','Romero','2007-07-11','nicolas.romero@outlook.com',1,'MIGRACION','2026-11-24 12:17:54'),(71,1071,'43207979','Lucas','Funes','2006-04-06','lucas.funes@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(72,1072,'42954175','Emiliano','Herrera','2001-03-13','emiliano.herrera@gmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(73,1073,'38158525','Brenda','Cabrera','2002-06-26','brenda.cabrera@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(74,1074,'38495142','Valentina','Aguirre','2004-03-06','valentina.aguirre@yahoo.com.ar',1,'MIGRACION','2026-11-24 12:17:54'),(75,1075,'39957858','Leandro','González','2001-02-12','leandro.gonzalez@gmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(76,1076,'41627088','Emiliano','Romero','2005-10-08',NULL,1,'MIGRACION','2026-11-24 12:17:54'),(77,1077,'39782899','Bruno','Sosa','1997-12-03','bruno.sosa@gmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(78,1078,'42405213','Belén','Suárez','2006-02-12','belen.suarez@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(79,1079,'46367626','Tomás','Correa','2004-04-27','tomas.correa@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54'),(80,1080,'45649300','Rocío','Ortiz','1997-02-25','rocio.ortiz@hotmail.com',1,'MIGRACION','2026-11-24 12:17:54');
/*!40000 ALTER TABLE `alumnos` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_alumnos_au AFTER UPDATE ON alumnos FOR EACH ROW
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
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `asignaciones_docentes`
--

DROP TABLE IF EXISTS `asignaciones_docentes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `asignaciones_docentes` (
  `id_docente` int(11) NOT NULL,
  `id_materia` int(11) NOT NULL,
  `id_ciclo` int(11) NOT NULL,
  PRIMARY KEY (`id_docente`,`id_materia`,`id_ciclo`),
  KEY `fk_asig_materia` (`id_materia`),
  KEY `fk_asig_ciclo` (`id_ciclo`),
  CONSTRAINT `fk_asig_ciclo` FOREIGN KEY (`id_ciclo`) REFERENCES `ciclos_lectivos` (`id_ciclo`),
  CONSTRAINT `fk_asig_docente` FOREIGN KEY (`id_docente`) REFERENCES `docentes` (`id_docente`),
  CONSTRAINT `fk_asig_materia` FOREIGN KEY (`id_materia`) REFERENCES `materias` (`id_materia`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `asignaciones_docentes`
--

LOCK TABLES `asignaciones_docentes` WRITE;
/*!40000 ALTER TABLE `asignaciones_docentes` DISABLE KEYS */;
/*!40000 ALTER TABLE `asignaciones_docentes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `asistencias`
--

DROP TABLE IF EXISTS `asistencias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `asistencias` (
  `id_asistencia` int(11) NOT NULL AUTO_INCREMENT,
  `id_inscripcion` int(11) NOT NULL,
  `fecha_clase` date NOT NULL,
  `estado` enum('PRESENTE','AUSENTE','JUSTIFICADO') NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id_asistencia`),
  UNIQUE KEY `uq_asistencias` (`id_inscripcion`,`fecha_clase`),
  CONSTRAINT `fk_asistencias_inscripcion` FOREIGN KEY (`id_inscripcion`) REFERENCES `inscripciones` (`id_inscripcion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `asistencias`
--

LOCK TABLES `asistencias` WRITE;
/*!40000 ALTER TABLE `asistencias` DISABLE KEYS */;
/*!40000 ALTER TABLE `asistencias` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_asistencias_ai AFTER INSERT ON asistencias FOR EACH ROW
BEGIN
  CALL sp_auditar('asistencias', 'INSERT', NEW.id_asistencia, 'estado', NULL, NEW.estado);
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_asistencias_au AFTER UPDATE ON asistencias FOR EACH ROW
BEGIN
  IF OLD.estado <> NEW.estado THEN
    CALL sp_auditar('asistencias', 'UPDATE', NEW.id_asistencia, 'estado', OLD.estado, NEW.estado);
  END IF;
  IF OLD.activo <> NEW.activo THEN
    CALL sp_auditar('asistencias', 'UPDATE', NEW.id_asistencia, 'activo',
                    CAST(OLD.activo AS CHAR), CAST(NEW.activo AS CHAR));
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_asistencias_ad AFTER DELETE ON asistencias FOR EACH ROW
BEGIN
  CALL sp_auditar('asistencias', 'DELETE', OLD.id_asistencia, 'estado', OLD.estado, NULL);
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `auditoria`
--

DROP TABLE IF EXISTS `auditoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auditoria` (
  `id_evento` bigint(20) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) DEFAULT NULL,
  `fecha_hora` datetime NOT NULL DEFAULT current_timestamp(),
  `tabla` varchar(50) NOT NULL,
  `operacion` enum('INSERT','UPDATE','DELETE') NOT NULL,
  `id_registro` int(11) NOT NULL,
  `campo` varchar(50) DEFAULT NULL,
  `valor_anterior` varchar(255) DEFAULT NULL,
  `valor_nuevo` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_evento`),
  KEY `idx_auditoria_registro` (`tabla`,`id_registro`),
  KEY `idx_auditoria_fecha` (`fecha_hora`),
  KEY `fk_auditoria_usuario` (`id_usuario`),
  CONSTRAINT `fk_auditoria_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`)
) ENGINE=InnoDB AUTO_INCREMENT=191 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auditoria`
--

LOCK TABLES `auditoria` WRITE;
/*!40000 ALTER TABLE `auditoria` DISABLE KEYS */;
INSERT INTO `auditoria` VALUES (1,NULL,'2026-11-23 15:57:21','usuarios','INSERT',1,'id_rol',NULL,'1'),(2,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',1,NULL,NULL,'estado=APROBADO, nota=6.50'),(3,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',2,NULL,NULL,'estado=APROBADO, nota=7.00'),(4,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',3,NULL,NULL,'estado=APROBADO, nota=7.00'),(5,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',4,NULL,NULL,'estado=DESAPROBADO, nota=1.00'),(6,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',5,NULL,NULL,'estado=DESAPROBADO, nota=1.00'),(7,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',6,NULL,NULL,'estado=APROBADO, nota=10.00'),(8,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',7,NULL,NULL,'estado=APROBADO, nota=8.50'),(9,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',8,NULL,NULL,'estado=DESAPROBADO, nota=1.00'),(10,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',9,NULL,NULL,'estado=AUSENTE, nota=NULL'),(11,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',10,NULL,NULL,'estado=APROBADO, nota=4.50'),(12,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',11,NULL,NULL,'estado=APROBADO, nota=8.50'),(13,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',12,NULL,NULL,'estado=APROBADO, nota=6.00'),(14,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',13,NULL,NULL,'estado=AUSENTE, nota=NULL'),(15,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',14,NULL,NULL,'estado=APROBADO, nota=8.50'),(16,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',15,NULL,NULL,'estado=APROBADO, nota=10.00'),(17,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',16,NULL,NULL,'estado=APROBADO, nota=6.50'),(18,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',17,NULL,NULL,'estado=APROBADO, nota=8.50'),(19,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',18,NULL,NULL,'estado=APROBADO, nota=4.50'),(20,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',19,NULL,NULL,'estado=APROBADO, nota=6.50'),(21,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',20,NULL,NULL,'estado=APROBADO, nota=9.50'),(22,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',21,NULL,NULL,'estado=APROBADO, nota=8.00'),(23,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',22,NULL,NULL,'estado=DESAPROBADO, nota=3.00'),(24,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',23,NULL,NULL,'estado=APROBADO, nota=8.50'),(25,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',24,NULL,NULL,'estado=DESAPROBADO, nota=3.00'),(26,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',25,NULL,NULL,'estado=APROBADO, nota=5.00'),(27,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',26,NULL,NULL,'estado=APROBADO, nota=10.00'),(28,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',27,NULL,NULL,'estado=APROBADO, nota=4.00'),(29,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',28,NULL,NULL,'estado=APROBADO, nota=8.50'),(30,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',29,NULL,NULL,'estado=DESAPROBADO, nota=2.00'),(31,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',30,NULL,NULL,'estado=DESAPROBADO, nota=1.00'),(32,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',31,NULL,NULL,'estado=AUSENTE, nota=NULL'),(33,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',32,NULL,NULL,'estado=APROBADO, nota=5.00'),(34,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',33,NULL,NULL,'estado=APROBADO, nota=8.50'),(35,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',34,NULL,NULL,'estado=DESAPROBADO, nota=2.00'),(36,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',35,NULL,NULL,'estado=APROBADO, nota=6.00'),(37,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',36,NULL,NULL,'estado=APROBADO, nota=7.00'),(38,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',37,NULL,NULL,'estado=APROBADO, nota=9.50'),(39,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',38,NULL,NULL,'estado=APROBADO, nota=9.50'),(40,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',39,NULL,NULL,'estado=DESAPROBADO, nota=3.00'),(41,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',40,NULL,NULL,'estado=APROBADO, nota=6.00'),(42,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',41,NULL,NULL,'estado=DESAPROBADO, nota=2.00'),(43,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',42,NULL,NULL,'estado=DESAPROBADO, nota=1.00'),(44,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',43,NULL,NULL,'estado=DESAPROBADO, nota=3.00'),(45,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',44,NULL,NULL,'estado=APROBADO, nota=7.00'),(46,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',45,NULL,NULL,'estado=APROBADO, nota=6.00'),(47,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',46,NULL,NULL,'estado=APROBADO, nota=9.00'),(48,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',47,NULL,NULL,'estado=APROBADO, nota=9.50'),(49,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',48,NULL,NULL,'estado=DESAPROBADO, nota=1.00'),(50,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',49,NULL,NULL,'estado=APROBADO, nota=6.50'),(51,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',50,NULL,NULL,'estado=DESAPROBADO, nota=3.00'),(52,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',51,NULL,NULL,'estado=APROBADO, nota=10.00'),(53,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',52,NULL,NULL,'estado=APROBADO, nota=8.00'),(54,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',53,NULL,NULL,'estado=APROBADO, nota=7.00'),(55,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',54,NULL,NULL,'estado=APROBADO, nota=7.50'),(56,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',55,NULL,NULL,'estado=APROBADO, nota=8.50'),(57,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',56,NULL,NULL,'estado=APROBADO, nota=9.00'),(58,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',57,NULL,NULL,'estado=APROBADO, nota=5.00'),(59,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',58,NULL,NULL,'estado=APROBADO, nota=5.00'),(60,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',59,NULL,NULL,'estado=APROBADO, nota=6.00'),(61,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',60,NULL,NULL,'estado=APROBADO, nota=8.00'),(62,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',61,NULL,NULL,'estado=APROBADO, nota=9.00'),(63,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',62,NULL,NULL,'estado=AUSENTE, nota=NULL'),(64,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',63,NULL,NULL,'estado=APROBADO, nota=8.50'),(65,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',64,NULL,NULL,'estado=APROBADO, nota=4.50'),(66,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',65,NULL,NULL,'estado=APROBADO, nota=4.00'),(67,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',66,NULL,NULL,'estado=APROBADO, nota=10.00'),(68,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',67,NULL,NULL,'estado=DESAPROBADO, nota=3.00'),(69,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',68,NULL,NULL,'estado=AUSENTE, nota=NULL'),(70,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',69,NULL,NULL,'estado=APROBADO, nota=6.00'),(71,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',70,NULL,NULL,'estado=DESAPROBADO, nota=2.00'),(72,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',71,NULL,NULL,'estado=APROBADO, nota=4.00'),(73,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',72,NULL,NULL,'estado=APROBADO, nota=10.00'),(74,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',73,NULL,NULL,'estado=DESAPROBADO, nota=3.00'),(75,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',74,NULL,NULL,'estado=DESAPROBADO, nota=2.00'),(76,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',75,NULL,NULL,'estado=DESAPROBADO, nota=1.00'),(77,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',76,NULL,NULL,'estado=APROBADO, nota=9.50'),(78,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',77,NULL,NULL,'estado=APROBADO, nota=8.50'),(79,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',78,NULL,NULL,'estado=APROBADO, nota=9.00'),(80,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',79,NULL,NULL,'estado=DESAPROBADO, nota=3.00'),(81,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',80,NULL,NULL,'estado=APROBADO, nota=4.50'),(82,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',81,NULL,NULL,'estado=APROBADO, nota=4.50'),(83,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',82,NULL,NULL,'estado=APROBADO, nota=9.00'),(84,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',83,NULL,NULL,'estado=APROBADO, nota=7.50'),(85,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',84,NULL,NULL,'estado=APROBADO, nota=7.00'),(86,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',85,NULL,NULL,'estado=APROBADO, nota=7.50'),(87,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',86,NULL,NULL,'estado=APROBADO, nota=6.50'),(88,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',87,NULL,NULL,'estado=APROBADO, nota=7.00'),(89,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',88,NULL,NULL,'estado=APROBADO, nota=5.00'),(90,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',89,NULL,NULL,'estado=APROBADO, nota=8.00'),(91,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',90,NULL,NULL,'estado=APROBADO, nota=6.00'),(92,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',91,NULL,NULL,'estado=APROBADO, nota=9.00'),(93,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',92,NULL,NULL,'estado=APROBADO, nota=9.00'),(94,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',93,NULL,NULL,'estado=APROBADO, nota=7.50'),(95,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',94,NULL,NULL,'estado=APROBADO, nota=9.50'),(96,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',95,NULL,NULL,'estado=APROBADO, nota=7.00'),(97,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',96,NULL,NULL,'estado=AUSENTE, nota=NULL'),(98,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',97,NULL,NULL,'estado=APROBADO, nota=8.50'),(99,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',98,NULL,NULL,'estado=APROBADO, nota=10.00'),(100,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',99,NULL,NULL,'estado=APROBADO, nota=4.00'),(101,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',100,NULL,NULL,'estado=APROBADO, nota=8.50'),(102,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',101,NULL,NULL,'estado=APROBADO, nota=9.50'),(103,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',102,NULL,NULL,'estado=APROBADO, nota=7.00'),(104,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',103,NULL,NULL,'estado=DESAPROBADO, nota=1.00'),(105,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',104,NULL,NULL,'estado=APROBADO, nota=4.00'),(106,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',105,NULL,NULL,'estado=DESAPROBADO, nota=3.00'),(107,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',106,NULL,NULL,'estado=APROBADO, nota=10.00'),(108,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',107,NULL,NULL,'estado=DESAPROBADO, nota=1.00'),(109,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',108,NULL,NULL,'estado=APROBADO, nota=9.50'),(110,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',109,NULL,NULL,'estado=APROBADO, nota=8.00'),(111,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',110,NULL,NULL,'estado=APROBADO, nota=10.00'),(112,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',111,NULL,NULL,'estado=APROBADO, nota=6.00'),(113,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',112,NULL,NULL,'estado=APROBADO, nota=8.00'),(114,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',113,NULL,NULL,'estado=APROBADO, nota=9.50'),(115,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',114,NULL,NULL,'estado=APROBADO, nota=8.00'),(116,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',115,NULL,NULL,'estado=APROBADO, nota=9.00'),(117,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',116,NULL,NULL,'estado=APROBADO, nota=8.50'),(118,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',117,NULL,NULL,'estado=APROBADO, nota=10.00'),(119,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',118,NULL,NULL,'estado=DESAPROBADO, nota=1.00'),(120,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',119,NULL,NULL,'estado=APROBADO, nota=4.50'),(121,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',120,NULL,NULL,'estado=APROBADO, nota=9.00'),(122,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',121,NULL,NULL,'estado=DESAPROBADO, nota=2.00'),(123,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',122,NULL,NULL,'estado=APROBADO, nota=9.50'),(124,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',123,NULL,NULL,'estado=APROBADO, nota=6.50'),(125,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',124,NULL,NULL,'estado=APROBADO, nota=7.50'),(126,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',125,NULL,NULL,'estado=APROBADO, nota=10.00'),(127,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',126,NULL,NULL,'estado=AUSENTE, nota=NULL'),(128,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',127,NULL,NULL,'estado=DESAPROBADO, nota=3.00'),(129,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',128,NULL,NULL,'estado=APROBADO, nota=10.00'),(130,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',129,NULL,NULL,'estado=APROBADO, nota=8.50'),(131,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',130,NULL,NULL,'estado=APROBADO, nota=7.50'),(132,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',131,NULL,NULL,'estado=DESAPROBADO, nota=3.00'),(133,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',132,NULL,NULL,'estado=APROBADO, nota=8.50'),(134,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',133,NULL,NULL,'estado=APROBADO, nota=9.50'),(135,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',134,NULL,NULL,'estado=APROBADO, nota=8.00'),(136,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',135,NULL,NULL,'estado=DESAPROBADO, nota=1.00'),(137,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',136,NULL,NULL,'estado=APROBADO, nota=6.00'),(138,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',137,NULL,NULL,'estado=APROBADO, nota=8.00'),(139,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',138,NULL,NULL,'estado=APROBADO, nota=6.00'),(140,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',139,NULL,NULL,'estado=APROBADO, nota=5.00'),(141,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',140,NULL,NULL,'estado=APROBADO, nota=6.50'),(142,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',141,NULL,NULL,'estado=DESAPROBADO, nota=1.00'),(143,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',142,NULL,NULL,'estado=APROBADO, nota=8.50'),(144,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',143,NULL,NULL,'estado=DESAPROBADO, nota=3.00'),(145,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',144,NULL,NULL,'estado=DESAPROBADO, nota=2.00'),(146,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',145,NULL,NULL,'estado=APROBADO, nota=9.50'),(147,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',146,NULL,NULL,'estado=DESAPROBADO, nota=2.00'),(148,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',147,NULL,NULL,'estado=AUSENTE, nota=NULL'),(149,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',148,NULL,NULL,'estado=APROBADO, nota=5.00'),(150,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',149,NULL,NULL,'estado=APROBADO, nota=10.00'),(151,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',150,NULL,NULL,'estado=APROBADO, nota=6.00'),(152,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',151,NULL,NULL,'estado=APROBADO, nota=4.50'),(153,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',152,NULL,NULL,'estado=APROBADO, nota=5.00'),(154,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',153,NULL,NULL,'estado=APROBADO, nota=4.00'),(155,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',154,NULL,NULL,'estado=DESAPROBADO, nota=2.00'),(156,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',155,NULL,NULL,'estado=APROBADO, nota=9.00'),(157,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',156,NULL,NULL,'estado=APROBADO, nota=5.00'),(158,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',157,NULL,NULL,'estado=APROBADO, nota=7.50'),(159,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',158,NULL,NULL,'estado=APROBADO, nota=6.00'),(160,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',159,NULL,NULL,'estado=APROBADO, nota=5.00'),(161,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',160,NULL,NULL,'estado=APROBADO, nota=10.00'),(162,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',161,NULL,NULL,'estado=APROBADO, nota=8.50'),(163,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',162,NULL,NULL,'estado=APROBADO, nota=9.00'),(164,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',163,NULL,NULL,'estado=APROBADO, nota=8.00'),(165,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',164,NULL,NULL,'estado=DESAPROBADO, nota=2.00'),(166,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',165,NULL,NULL,'estado=APROBADO, nota=8.50'),(167,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',166,NULL,NULL,'estado=DESAPROBADO, nota=3.00'),(168,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',167,NULL,NULL,'estado=APROBADO, nota=8.00'),(169,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',168,NULL,NULL,'estado=APROBADO, nota=10.00'),(170,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',169,NULL,NULL,'estado=APROBADO, nota=9.00'),(171,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',170,NULL,NULL,'estado=APROBADO, nota=6.50'),(172,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',171,NULL,NULL,'estado=APROBADO, nota=8.50'),(173,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',172,NULL,NULL,'estado=DESAPROBADO, nota=1.00'),(174,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',173,NULL,NULL,'estado=APROBADO, nota=10.00'),(175,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',174,NULL,NULL,'estado=APROBADO, nota=7.00'),(176,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',175,NULL,NULL,'estado=APROBADO, nota=4.50'),(177,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',176,NULL,NULL,'estado=APROBADO, nota=7.50'),(178,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',177,NULL,NULL,'estado=APROBADO, nota=4.50'),(179,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',178,NULL,NULL,'estado=APROBADO, nota=6.00'),(180,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',179,NULL,NULL,'estado=APROBADO, nota=10.00'),(181,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',180,NULL,NULL,'estado=DESAPROBADO, nota=2.00'),(182,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',181,NULL,NULL,'estado=APROBADO, nota=4.00'),(183,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',182,NULL,NULL,'estado=APROBADO, nota=5.00'),(184,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',183,NULL,NULL,'estado=APROBADO, nota=9.00'),(185,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',184,NULL,NULL,'estado=APROBADO, nota=5.00'),(186,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',185,NULL,NULL,'estado=APROBADO, nota=4.00'),(187,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',186,NULL,NULL,'estado=APROBADO, nota=7.50'),(188,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',187,NULL,NULL,'estado=AUSENTE, nota=NULL'),(189,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',188,NULL,NULL,'estado=DESAPROBADO, nota=3.00'),(190,NULL,'2026-11-24 12:17:54','actas_examen','INSERT',189,NULL,NULL,'estado=APROBADO, nota=6.00');
/*!40000 ALTER TABLE `auditoria` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `carreras`
--

DROP TABLE IF EXISTS `carreras`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `carreras` (
  `id_carrera` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `activa` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id_carrera`),
  UNIQUE KEY `uq_carreras_nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `carreras`
--

LOCK TABLES `carreras` WRITE;
/*!40000 ALTER TABLE `carreras` DISABLE KEYS */;
INSERT INTO `carreras` VALUES (1,'Tecnicatura Superior En Desarrollo De Software',1),(2,'Tecnicatura Superior En Administración De Empresas',1);
/*!40000 ALTER TABLE `carreras` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ciclos_lectivos`
--

DROP TABLE IF EXISTS `ciclos_lectivos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ciclos_lectivos` (
  `id_ciclo` int(11) NOT NULL AUTO_INCREMENT,
  `anio` smallint(6) NOT NULL,
  `fecha_inicio` date NOT NULL,
  `fecha_fin` date NOT NULL,
  PRIMARY KEY (`id_ciclo`),
  UNIQUE KEY `uq_ciclos_anio` (`anio`),
  CONSTRAINT `chk_ciclos_fechas` CHECK (`fecha_fin` > `fecha_inicio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ciclos_lectivos`
--

LOCK TABLES `ciclos_lectivos` WRITE;
/*!40000 ALTER TABLE `ciclos_lectivos` DISABLE KEYS */;
/*!40000 ALTER TABLE `ciclos_lectivos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `correlatividades`
--

DROP TABLE IF EXISTS `correlatividades`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `correlatividades` (
  `id_materia` int(11) NOT NULL,
  `id_materia_requerida` int(11) NOT NULL,
  PRIMARY KEY (`id_materia`,`id_materia_requerida`),
  KEY `fk_correl_requerida` (`id_materia_requerida`),
  CONSTRAINT `fk_correl_materia` FOREIGN KEY (`id_materia`) REFERENCES `materias` (`id_materia`),
  CONSTRAINT `fk_correl_requerida` FOREIGN KEY (`id_materia_requerida`) REFERENCES `materias` (`id_materia`),
  CONSTRAINT `chk_correl_distintas` CHECK (`id_materia` <> `id_materia_requerida`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `correlatividades`
--

LOCK TABLES `correlatividades` WRITE;
/*!40000 ALTER TABLE `correlatividades` DISABLE KEYS */;
/*!40000 ALTER TABLE `correlatividades` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `docentes`
--

DROP TABLE IF EXISTS `docentes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `docentes` (
  `id_docente` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) NOT NULL,
  `apellido` varchar(50) NOT NULL,
  `dni` varchar(15) NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id_docente`),
  UNIQUE KEY `uq_docentes_dni` (`dni`),
  CONSTRAINT `chk_docentes_dni` CHECK (`dni` regexp '^[0-9]+$')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `docentes`
--

LOCK TABLES `docentes` WRITE;
/*!40000 ALTER TABLE `docentes` DISABLE KEYS */;
/*!40000 ALTER TABLE `docentes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inscripciones`
--

DROP TABLE IF EXISTS `inscripciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `inscripciones` (
  `id_inscripcion` int(11) NOT NULL AUTO_INCREMENT,
  `id_alumno` int(11) NOT NULL,
  `id_materia` int(11) NOT NULL,
  `id_ciclo` int(11) NOT NULL,
  `condicion_cursada` enum('CURSANDO','REGULAR','PROMOCIONADO','LIBRE') NOT NULL DEFAULT 'CURSANDO',
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id_inscripcion`),
  UNIQUE KEY `uq_inscripciones` (`id_alumno`,`id_materia`,`id_ciclo`),
  KEY `fk_inscripciones_materia` (`id_materia`),
  KEY `fk_inscripciones_ciclo` (`id_ciclo`),
  CONSTRAINT `fk_inscripciones_alumno` FOREIGN KEY (`id_alumno`) REFERENCES `alumnos` (`id_alumno`),
  CONSTRAINT `fk_inscripciones_ciclo` FOREIGN KEY (`id_ciclo`) REFERENCES `ciclos_lectivos` (`id_ciclo`),
  CONSTRAINT `fk_inscripciones_materia` FOREIGN KEY (`id_materia`) REFERENCES `materias` (`id_materia`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inscripciones`
--

LOCK TABLES `inscripciones` WRITE;
/*!40000 ALTER TABLE `inscripciones` DISABLE KEYS */;
/*!40000 ALTER TABLE `inscripciones` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inscripciones_examen`
--

DROP TABLE IF EXISTS `inscripciones_examen`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `inscripciones_examen` (
  `id_alumno` int(11) NOT NULL,
  `id_mesa` int(11) NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id_alumno`,`id_mesa`),
  KEY `fk_insc_examen_mesa` (`id_mesa`),
  CONSTRAINT `fk_insc_examen_alumno` FOREIGN KEY (`id_alumno`) REFERENCES `alumnos` (`id_alumno`),
  CONSTRAINT `fk_insc_examen_mesa` FOREIGN KEY (`id_mesa`) REFERENCES `mesas_examen` (`id_mesa`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inscripciones_examen`
--

LOCK TABLES `inscripciones_examen` WRITE;
/*!40000 ALTER TABLE `inscripciones_examen` DISABLE KEYS */;
/*!40000 ALTER TABLE `inscripciones_examen` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `lotes_carga`
--

DROP TABLE IF EXISTS `lotes_carga`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `lotes_carga` (
  `id_lote` int(11) NOT NULL AUTO_INCREMENT,
  `tipo` enum('MIGRACION','MASIVA') NOT NULL,
  `entidad` varchar(30) NOT NULL,
  `id_usuario` int(11) DEFAULT NULL,
  `archivo` varchar(200) NOT NULL,
  `fecha_hora` datetime NOT NULL DEFAULT current_timestamp(),
  `filas_total` int(11) NOT NULL DEFAULT 0,
  `filas_ok` int(11) NOT NULL DEFAULT 0,
  `filas_error` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id_lote`),
  KEY `fk_lotes_usuario` (`id_usuario`),
  CONSTRAINT `fk_lotes_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`),
  CONSTRAINT `chk_lotes_filas` CHECK (`filas_ok` + `filas_error` <= `filas_total`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lotes_carga`
--

LOCK TABLES `lotes_carga` WRITE;
/*!40000 ALTER TABLE `lotes_carga` DISABLE KEYS */;
INSERT INTO `lotes_carga` VALUES (1,'MIGRACION','actas_examen',NULL,'Actas_Historicas.csv','2026-11-24 12:17:54',204,189,15);
/*!40000 ALTER TABLE `lotes_carga` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `materias`
--

DROP TABLE IF EXISTS `materias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `materias` (
  `id_materia` int(11) NOT NULL AUTO_INCREMENT,
  `id_carrera` int(11) NOT NULL,
  `codigo` varchar(10) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `anio_nivel` tinyint(4) NOT NULL,
  `activa` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id_materia`),
  UNIQUE KEY `uq_materias_codigo` (`codigo`),
  KEY `fk_materias_carrera` (`id_carrera`),
  CONSTRAINT `fk_materias_carrera` FOREIGN KEY (`id_carrera`) REFERENCES `carreras` (`id_carrera`),
  CONSTRAINT `chk_materias_anio` CHECK (`anio_nivel` between 1 and 5)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `materias`
--

LOCK TABLES `materias` WRITE;
/*!40000 ALTER TABLE `materias` DISABLE KEYS */;
INSERT INTO `materias` VALUES (1,1,'DS101','Programación I',1,1),(2,1,'DS102','Matemática Discreta',1,1),(3,1,'DS103','Arquitectura De Computadoras',1,1),(4,1,'DS104','Inglés Técnico I',1,1),(5,1,'DS201','Programación Ii',2,1),(6,1,'DS202','Bases De Datos',2,1),(7,1,'DS203','Análisis De Sistemas',2,1),(8,1,'DS204','Redes De Datos',2,1),(9,1,'DS301','Ingeniería De Software',3,1),(10,1,'DS302','Seguridad Informática',3,1),(11,1,'DS303','Gestión De Proyectos Informáticos',3,1),(12,1,'DS304','Práctica Profesionalizante',3,1),(13,2,'AD101','Introducción A La Administración',1,1),(14,2,'AD102','Contabilidad I',1,1),(15,2,'AD103','Matemática Aplicada',1,1),(16,2,'AD104','Derecho Comercial',1,1),(17,2,'AD201','Costos',2,1),(18,2,'AD202','Marketing',2,1),(19,2,'AD203','Gestión De Recursos Humanos',2,1),(20,2,'AD204','Estadística',2,1),(21,2,'AD301','Finanzas',3,1),(22,2,'AD302','Comercio Exterior',3,1),(23,2,'AD303','Evaluación De Proyectos',3,1),(24,2,'AD304','Práctica Profesional',3,1);
/*!40000 ALTER TABLE `materias` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `matriculas`
--

DROP TABLE IF EXISTS `matriculas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `matriculas` (
  `id_matricula` int(11) NOT NULL AUTO_INCREMENT,
  `id_alumno` int(11) NOT NULL,
  `id_carrera` int(11) NOT NULL,
  `anio_ingreso` smallint(6) NOT NULL,
  `estado` enum('ACTIVA','EGRESADA','BAJA') NOT NULL DEFAULT 'ACTIVA',
  PRIMARY KEY (`id_matricula`),
  UNIQUE KEY `uq_matriculas_alumno_carrera` (`id_alumno`,`id_carrera`),
  KEY `fk_matriculas_carrera` (`id_carrera`),
  CONSTRAINT `fk_matriculas_alumno` FOREIGN KEY (`id_alumno`) REFERENCES `alumnos` (`id_alumno`),
  CONSTRAINT `fk_matriculas_carrera` FOREIGN KEY (`id_carrera`) REFERENCES `carreras` (`id_carrera`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `matriculas`
--

LOCK TABLES `matriculas` WRITE;
/*!40000 ALTER TABLE `matriculas` DISABLE KEYS */;
/*!40000 ALTER TABLE `matriculas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `mesas_examen`
--

DROP TABLE IF EXISTS `mesas_examen`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mesas_examen` (
  `id_mesa` int(11) NOT NULL AUTO_INCREMENT,
  `id_materia` int(11) NOT NULL,
  `id_ciclo` int(11) NOT NULL,
  `fecha` date NOT NULL,
  `llamado` tinyint(4) NOT NULL DEFAULT 1,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id_mesa`),
  UNIQUE KEY `uq_mesas` (`id_materia`,`fecha`,`llamado`),
  UNIQUE KEY `uq_mesas_id_materia` (`id_mesa`,`id_materia`),
  KEY `fk_mesas_ciclo` (`id_ciclo`),
  CONSTRAINT `fk_mesas_ciclo` FOREIGN KEY (`id_ciclo`) REFERENCES `ciclos_lectivos` (`id_ciclo`),
  CONSTRAINT `fk_mesas_materia` FOREIGN KEY (`id_materia`) REFERENCES `materias` (`id_materia`),
  CONSTRAINT `chk_mesas_llamado` CHECK (`llamado` >= 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mesas_examen`
--

LOCK TABLES `mesas_examen` WRITE;
/*!40000 ALTER TABLE `mesas_examen` DISABLE KEYS */;
/*!40000 ALTER TABLE `mesas_examen` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notas_cursada`
--

DROP TABLE IF EXISTS `notas_cursada`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notas_cursada` (
  `id_nota` int(11) NOT NULL AUTO_INCREMENT,
  `id_inscripcion` int(11) NOT NULL,
  `instancia` varchar(30) NOT NULL,
  `nota` decimal(4,2) NOT NULL,
  `fecha` date NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id_nota`),
  UNIQUE KEY `uq_notas_instancia` (`id_inscripcion`,`instancia`),
  CONSTRAINT `fk_notas_inscripcion` FOREIGN KEY (`id_inscripcion`) REFERENCES `inscripciones` (`id_inscripcion`),
  CONSTRAINT `chk_notas_rango` CHECK (`nota` between 1.00 and 10.00)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notas_cursada`
--

LOCK TABLES `notas_cursada` WRITE;
/*!40000 ALTER TABLE `notas_cursada` DISABLE KEYS */;
/*!40000 ALTER TABLE `notas_cursada` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_notas_ai AFTER INSERT ON notas_cursada FOR EACH ROW
BEGIN
  CALL sp_auditar('notas_cursada', 'INSERT', NEW.id_nota, 'nota', NULL, CAST(NEW.nota AS CHAR));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_notas_au AFTER UPDATE ON notas_cursada FOR EACH ROW
BEGIN
  IF OLD.nota <> NEW.nota THEN
    CALL sp_auditar('notas_cursada', 'UPDATE', NEW.id_nota, 'nota',
                    CAST(OLD.nota AS CHAR), CAST(NEW.nota AS CHAR));
  END IF;
  IF OLD.activo <> NEW.activo THEN
    CALL sp_auditar('notas_cursada', 'UPDATE', NEW.id_nota, 'activo',
                    CAST(OLD.activo AS CHAR), CAST(NEW.activo AS CHAR));
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_notas_ad AFTER DELETE ON notas_cursada FOR EACH ROW
BEGIN
  CALL sp_auditar('notas_cursada', 'DELETE', OLD.id_nota, 'nota', CAST(OLD.nota AS CHAR), NULL);
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `parametros`
--

DROP TABLE IF EXISTS `parametros`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `parametros` (
  `clave` varchar(50) NOT NULL,
  `valor` varchar(100) NOT NULL,
  `descripcion` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`clave`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `parametros`
--

LOCK TABLES `parametros` WRITE;
/*!40000 ALTER TABLE `parametros` DISABLE KEYS */;
INSERT INTO `parametros` VALUES ('asistencia_minima','75','Porcentaje mínimo de asistencia (RF-ASI-03). VALOR PROVISORIO: confirmar con la institución.'),('ultimo_legajo','1087','Último legajo asignado. Lo actualizan sp_proximo_legajo y sp_sincronizar_legajo.');
/*!40000 ALTER TABLE `parametros` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `roles` (
  `id_rol` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `nombre` varchar(30) NOT NULL,
  PRIMARY KEY (`id_rol`),
  UNIQUE KEY `uq_roles_nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES (1,'ADMIN'),(4,'DIRECTIVO'),(3,'DOCENTE'),(2,'PRECEPTOR');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `usuarios` (
  `id_usuario` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `id_rol` tinyint(3) unsigned NOT NULL,
  `id_docente` int(11) DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  `ultimo_acceso` datetime DEFAULT NULL,
  `creado_en` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `uq_usuarios_username` (`username`),
  UNIQUE KEY `uq_usuarios_docente` (`id_docente`),
  KEY `fk_usuarios_rol` (`id_rol`),
  CONSTRAINT `fk_usuarios_docente` FOREIGN KEY (`id_docente`) REFERENCES `docentes` (`id_docente`),
  CONSTRAINT `fk_usuarios_rol` FOREIGN KEY (`id_rol`) REFERENCES `roles` (`id_rol`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (1,'valentinopepa','scrypt:32768:8:1$vBrI1Pzsy9ixMOnJ$faedaf4f26e2fb8755087f65c6a6bb0c94878a5845c7198767573d0740d817948bd1467353f53f4d33bc6c5c02ff802a3260bd363f5769c33fb11c593023b532',1,NULL,1,NULL,'2026-11-23 15:57:21');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_usuarios_bi BEFORE INSERT ON usuarios FOR EACH ROW
BEGIN
  IF NEW.id_docente IS NULL AND NEW.id_rol = (SELECT id_rol FROM roles WHERE nombre = 'DOCENTE') THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Un usuario con rol DOCENTE debe estar vinculado a un docente (RF-USR-02)';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_usuarios_ai AFTER INSERT ON usuarios FOR EACH ROW
BEGIN
  CALL sp_auditar('usuarios', 'INSERT', NEW.id_usuario, 'id_rol', NULL, CAST(NEW.id_rol AS CHAR));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_usuarios_bu BEFORE UPDATE ON usuarios FOR EACH ROW
BEGIN
  IF NEW.id_docente IS NULL AND NEW.id_rol = (SELECT id_rol FROM roles WHERE nombre = 'DOCENTE') THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Un usuario con rol DOCENTE debe estar vinculado a un docente (RF-USR-02)';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_usuarios_au AFTER UPDATE ON usuarios FOR EACH ROW
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
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Dumping events for database 'gestion_academica_v2'
--

--
-- Dumping routines for database 'gestion_academica_v2'
--
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_auditar` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_auditar`(
  IN p_tabla VARCHAR(50), IN p_operacion VARCHAR(10), IN p_id INT,
  IN p_campo VARCHAR(50), IN p_anterior VARCHAR(255), IN p_nuevo VARCHAR(255))
BEGIN
  INSERT INTO auditoria (id_usuario, tabla, operacion, id_registro, campo, valor_anterior, valor_nuevo)
  VALUES (@app_user_id, p_tabla, p_operacion, p_id, p_campo, p_anterior, p_nuevo);
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_proximo_legajo` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_proximo_legajo`(OUT p_legajo INT)
BEGIN
  UPDATE parametros
     SET valor = LAST_INSERT_ID(CAST(valor AS UNSIGNED) + 1)
   WHERE clave = 'ultimo_legajo';
  SET p_legajo = LAST_INSERT_ID();
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_sincronizar_legajo` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_sincronizar_legajo`()
BEGIN
  UPDATE parametros
     SET valor = CAST((SELECT COALESCE(MAX(legajo), 0) FROM alumnos) AS CHAR)
   WHERE clave = 'ultimo_legajo';
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-11-24 15:14:07
