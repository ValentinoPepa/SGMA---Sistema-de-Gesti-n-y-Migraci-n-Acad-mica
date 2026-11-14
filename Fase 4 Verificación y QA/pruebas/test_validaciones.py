import unittest
from datetime import date, timedelta

from sgma.validaciones import (
    normalizar_dni,
    normalizar_email,
    normalizar_fecha,
    normalizar_nombre,
    normalizar_nota,
    separar_nombre_completo,
    validar_columnas_plantilla,
    validar_correlativas,
    validar_referencia,
)


class ValidacionesTests(unittest.TestCase):
    def test_dni_quita_separadores_y_detecta_duplicado_en_lote(self):
        usados = set()
        primero = normalizar_dni("42.123.456", dnis_del_lote=usados)
        segundo = normalizar_dni("42-123-456", dnis_del_lote=usados)
        self.assertTrue(primero.valido)
        self.assertEqual(primero.valor, "42123456")
        self.assertFalse(segundo.valido)
        self.assertEqual(segundo.errores[0].codigo, "ERR_01_DNI_DUP")

    def test_dni_rechaza_caracteres_que_no_son_digitos(self):
        resultado = normalizar_dni("12A34")
        self.assertFalse(resultado.valido)
        self.assertIn("solo dígitos", resultado.errores[0].mensaje)

    def test_nombre_completo_y_normalizacion(self):
        resultado = separar_nombre_completo("PÉREZ, Juan Carlos")
        self.assertTrue(resultado.valido)
        self.assertEqual(resultado.valor, {"apellido": "Pérez", "nombre": "Juan Carlos"})
        self.assertFalse(normalizar_nombre("  ", "nombre").valido)

    def test_fecha_acepta_formatos_legacy_y_rechaza_fecha_futura(self):
        self.assertEqual(normalizar_fecha("15/05/2002", campo="fecha").valor, date(2002, 5, 15))
        resultado = normalizar_fecha(date.today() + timedelta(days=1), campo="fecha_examen", no_futura=True)
        self.assertFalse(resultado.valido)
        self.assertEqual(resultado.errores[0].codigo, "ERR_03_DATE_INVALID")

    def test_email_se_normaliza_y_valida(self):
        self.assertEqual(normalizar_email("  Alumno@Ejemplo.COM ").valor, "alumno@ejemplo.com")
        invalido = normalizar_email("correo-sin-dominio")
        self.assertFalse(invalido.valido)
        self.assertEqual(invalido.errores[0].codigo, "ERR_05_EMAIL_INVALID")

    def test_nota_acepta_coma_y_limita_rango_y_precision(self):
        self.assertEqual(str(normalizar_nota("7,50").valor), "7.50")
        for valor in ("0", "10.01", "7.555", "no es nota"):
            with self.subTest(valor=valor):
                resultado = normalizar_nota(valor)
                self.assertFalse(resultado.valido)
                self.assertEqual(resultado.errores[0].codigo, "ERR_04_NOTA_OUT_RANGE")

    def test_referencias_correlativas_y_plantilla(self):
        self.assertEqual(validar_referencia(False, campo="materia", descripcion="MAT1").errores[0].codigo, "ERR_02_FK_NOTFOUND")
        self.assertEqual(validar_correlativas(["MAT1"]).errores[0].codigo, "ERR_06_CORRELATIVA")
        self.assertTrue(validar_columnas_plantilla(["dni", "nombre"], ["dni", "nombre"]).valido)
        error = validar_columnas_plantilla(["nombre", "dni"], ["dni", "nombre"])
        self.assertFalse(error.valido)
        self.assertEqual(error.errores[0].codigo, "ERR_08_PLANTILLA")


if __name__ == "__main__":
    unittest.main()
