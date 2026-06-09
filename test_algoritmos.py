import unittest

from algoritmos import busqueda_binaria, ordenar_burbuja


class TestAlgoritmos(unittest.TestCase):

    def test_ordenar_burbuja(self):
        Numeros = [5, 2, 8, 1]
        resultado = ordenar_burbuja(Numeros)
        self.assertEqual(resultado, [1, 2, 5, 8])

    def test_ordenar_burbuja_ya_ordenado(self):
        Numeros = [1, 2, 3, 4]
        resultado = ordenar_burbuja(Numeros)
        self.assertEqual(resultado, [1, 2, 3, 4])

    def test_ordenar_burbuja_lista_vacia(self):
        self.assertEqual(ordenar_burbuja([]), [])

    def test_busqueda_binaria_encontrado(self):
        Numeros = [1, 2, 5, 8]
        resultado = busqueda_binaria(Numeros, 5)
        self.assertTrue(resultado)

    def test_busqueda_binaria_no_encontrado(self):
        Numeros = [1, 2, 5, 8]
        resultado = busqueda_binaria(Numeros, 7)
        self.assertFalse(resultado)

    def test_busqueda_binaria_lista_vacia(self):
        self.assertFalse(busqueda_binaria([], 1))


if __name__ == "__main__":
    unittest.main()
