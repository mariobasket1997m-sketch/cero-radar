import unittest
from cero.sizes import wearable


def d(title,variant='',**k):return {'title':title,'variant':variant,**k}


class SizesTests(unittest.TestCase):
    def test_non_clothing_always_passes(self):
        self.assertTrue(wearable(d('Auriculares bluetooth','Negro')))
        self.assertTrue(wearable(d('Robot aspirador','')))

    def test_jeans_waist_length(self):
        self.assertTrue(wearable(d('Pantalón vaquero','27W / 30L')))   # perfil mujer
        self.assertTrue(wearable(d('Pantalón vaquero','Tamaño: 33W / 34L')))  # perfil hombre
        self.assertFalse(wearable(d('Pantalón vaquero','31W / 32L')))
        self.assertFalse(wearable(d('Pantalón vaquero','24W / 28L')))
        self.assertFalse(wearable(d('Pantalón vaquero','40W / 34L')))

    def test_letter_sizes(self):
        self.assertTrue(wearable(d('Camiseta algodón','L / Negro')))
        self.assertTrue(wearable(d('Sudadera','XL')))
        self.assertTrue(wearable(d('Camiseta','M')))
        self.assertFalse(wearable(d('Camiseta','XS')))
        self.assertFalse(wearable(d('Camiseta','3XL')))

    def test_shoes(self):
        self.assertTrue(wearable(d('Zapatillas running','44')))
        self.assertTrue(wearable(d('Zapatillas running','EU 39 / Blanco')))
        self.assertFalse(wearable(d('Zapatillas running','42')))
        self.assertFalse(wearable(d('Botas de montaña','47')))

    def test_unknown_or_missing_size_passes(self):
        self.assertTrue(wearable(d('Camiseta','')))
        self.assertTrue(wearable(d('Camiseta','Rojo')))

    def test_kids_excluded(self):
        self.assertFalse(wearable(d('Camiseta niño','8 años')))
        self.assertFalse(wearable(d('Pantalón infantil','L')))


if __name__=='__main__':unittest.main()
