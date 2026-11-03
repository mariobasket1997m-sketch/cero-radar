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


class ProfileTests(unittest.TestCase):
    def test_profiles_are_separate(self):
        jeans=d('Pantalón vaquero','27W / 30L')
        self.assertTrue(wearable(jeans,'mujer'));self.assertFalse(wearable(jeans,'hombre'))
        big=d('Pantalón vaquero','33W / 34L')
        self.assertTrue(wearable(big,'hombre'));self.assertFalse(wearable(big,'mujer'))
        self.assertTrue(wearable(d('Zapatillas','44'),'hombre'));self.assertFalse(wearable(d('Zapatillas','44'),'mujer'))
        self.assertTrue(wearable(d('Zapatillas','38'),'mujer'));self.assertFalse(wearable(d('Zapatillas','38'),'hombre'))
        self.assertTrue(wearable(d('Camiseta','S'),'mujer'));self.assertFalse(wearable(d('Camiseta','S'),'hombre'))
        self.assertTrue(wearable(d('Camiseta','XL'),'hombre'));self.assertFalse(wearable(d('Camiseta','XL'),'mujer'))

    def test_chat_targets_and_routing(self):
        import os
        from importlib import reload
        os.environ['TELEGRAM_CHAT_ID']='1, 2:mujer ,3'
        import cero.config as cfg;reload(cfg)
        from cero import telegram
        self.assertEqual(telegram.chat_targets(),[('1','hombre'),('2','mujer'),('3','hombre')])
        self.assertEqual(telegram.targets_for(d('Pantalón vaquero','27W / 30L')),['2'])
        self.assertEqual(telegram.targets_for(d('Zapatillas','44')),['1','3'])
        self.assertEqual(telegram.targets_for(d('Auriculares','')),['1','2','3'])
        self.assertEqual(telegram.targets_for(d('Camiseta','XS')),[])
        os.environ.pop('TELEGRAM_CHAT_ID');reload(cfg)


class BooksTests(unittest.TestCase):
    def test_books_unwanted(self):
        from cero.filters import unwanted
        self.assertTrue(unwanted(d('El nombre del viento','Tapa blanda')))
        self.assertTrue(unwanted(d('Novela histórica','')))
        self.assertTrue(unwanted(d('Libro de cocina','')))
        self.assertTrue(unwanted(d('Dune','Edición Kindle')))
        self.assertFalse(unwanted(d('Zapatillas running','44')))
        self.assertFalse(unwanted(d('Auriculares bluetooth','Negro')))


class ConsumablesTests(unittest.TestCase):
    def test_printer_consumables_unwanted(self):
        from cero.filters import unwanted
        self.assertTrue(unwanted(d('Epson Cartucho Light Cian ULTRACHROME SC-P900','')))
        self.assertTrue(unwanted(d('Tóner compatible HP 59A','')))
        self.assertFalse(unwanted(d('Impresora Epson EcoTank','')))
