# Registro documental C8

- Stack documentado: MySQL 8.0.16 o superior con InnoDB como motor objetivo; Flask 3.x y `mysql-connector-python` para la aplicación.
- La documentación distingue el motor objetivo MySQL de las verificaciones locales hechas en MariaDB 10.4.32.
- Regla de asistencia precisada en el manual y en el SRS v1.3 editable. El 75 % semilla sigue expresamente provisorio, pendiente de aprobación institucional.
- Se unificaron el PDF RBAC original y el Word C8 en un único documento consolidado: Diseño de Seguridad RBAC y Auditoría SGMA v1.1 C8 definitivo.docx. Incluye las matrices y el SQL de permisos del original, la ampliación RNF-05 y la evidencia C5; las decisiones abiertas permanecen señaladas. El PDF y el Word C8 previos quedan como antecedentes.
- Se generó una versión Word editable y actualizada de Arquitectura ETL; se retiraron afirmaciones obsoletas sobre que el código no estaba implementado y se describieron las salidas y controles que realmente existen.
- Tras recibir el SRS v1.2 original, se rehízo como SRS v1.3 editable: conserva sus requisitos y matrices, fija MySQL/Flask, precisa la regla de asistencia y amplía RNF-05. Los umbrales numéricos originales se conservaron.
- Usar como versión vigente el archivo SRS v1.3 SGMA editable C8. El borrador preliminar creado antes de recibir el PDF original queda obsoleto.
- Se actualizó C4 para comparar las pruebas realizadas con los umbrales del SRS. Los ensayos existentes son parciales y no demuestran todavía el cumplimiento de RNF-01, RNF-02, RNF-10 ni RNF-11.
- Comparación de copias locales de Fase 2: el `gestion_academica.sql` del workspace y los `gestion_academica.sql` y `gestion_academica_v2.sql` de la carpeta descargada tienen el mismo contenido de texto SQL; los hashes binarios difieren por formato de archivo. Los demás artefactos de Fase 2 coinciden byte por byte. La copia extra `gestion_academica_v2.sql` no se duplicó en el repositorio para evitar dos nombres para el mismo script.
- El SRS v1.3 permanece en revisión, pendiente de aprobación del equipo y la institución.
- Estado Drive: el conector de Google Drive está deshabilitado por la administración y no se pudo operar la carpeta. Las versiones editables quedan preparadas localmente; no se afirma que Drive ya esté actualizado.
- La inspección visual DOCX→PNG no pudo ejecutarse porque falta el módulo `pdf2image` requerido por el renderizador disponible. Se comprobó la estructura OOXML y el contenido extraído; conviene abrir los tres DOCX en Word antes de reemplazar los originales en Drive.

- La arquitectura ETL quedó consolidada en Fase 2 Diseño y Base de Datos/Arquitectura ETL SGMA v1.3 C8 definitivo.docx, integrando el PDF v1.1 y el Word C8 con el estado del código y las evidencias C3/C4. Los originales se conservan como antecedentes; no se afirma que las salidas CSV/informe antiguas ni todos los umbrales RNF estén implementados/verificados.

