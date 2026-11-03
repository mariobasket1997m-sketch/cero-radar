import sqlite3
import unittest
from datetime import datetime,timedelta,timezone
from cero import notify


class NotifyDedupTests(unittest.TestCase):
    def setUp(self):
        self.c=sqlite3.connect(':memory:');self.c.row_factory=sqlite3.Row;notify._ensure_log(self.c)
        self.deal={'title':'Auriculares  BT-200!','variant':'Negro','url':'https://www.tienda.es/p/1?utm=a','price':0}

    def test_key_ignores_www_query_case_and_punctuation(self):
        other=dict(self.deal,title='auriculares bt 200',url='https://tienda.es/p/2')
        self.assertEqual(notify.dedup_key(self.deal),notify.dedup_key(other))

    def test_variant_and_store_differentiate(self):
        self.assertNotEqual(notify.dedup_key(self.deal),notify.dedup_key(dict(self.deal,variant='Blanco')))
        self.assertNotEqual(notify.dedup_key(self.deal),notify.dedup_key(dict(self.deal,url='https://otra.es/p')))

    def test_repeat_blocked_until_price_drops_or_cooldown(self):
        d=dict(self.deal,price=10.0);self.assertFalse(notify.is_repeat(self.c,d))
        notify.remember(self.c,d)
        self.assertTrue(notify.is_repeat(self.c,d))
        self.assertTrue(notify.is_repeat(self.c,dict(d,price=12.0)))
        self.assertFalse(notify.is_repeat(self.c,dict(d,price=5.0)))
        later=datetime.now(timezone.utc)+timedelta(days=notify.COOLDOWN_DAYS+1)
        self.assertFalse(notify.is_repeat(self.c,d,at=later))

    def test_free_item_not_repeated_within_cooldown(self):
        notify.remember(self.c,self.deal)
        self.assertTrue(notify.is_repeat(self.c,self.deal))


if __name__=='__main__':unittest.main()
