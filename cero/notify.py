"""Bandeja de avisos: por defecto sólo informa; --send requiere activación explícita.

Antirrepetición: un mismo producto (tienda + título + variante) no se vuelve a avisar
mientras no baje de precio o pasen COOLDOWN_DAYS días desde el último aviso.
"""
import argparse
import json
import re
from datetime import datetime,timedelta,timezone
from urllib.parse import urlsplit
from cero.db import connect,unpack,now
from cero.telegram import armed,send_deal
from cero.filters import unwanted
from cero.telegram import targets_for

COOLDOWN_DAYS=7
MAX_PER_RUN=15  # se envían primero los de mayor puntuación


def _norm(text):
    return re.sub(r'[^a-z0-9]+',' ',(text or '').lower()).strip()


def dedup_key(deal):
    host=urlsplit(deal.get('url') or '').netloc.lower()
    if host.startswith('www.'):host=host[4:]
    return f"{host}|{_norm(deal.get('title'))}|{_norm(deal.get('variant'))}"


def _ensure_log(c):
    c.execute('CREATE TABLE IF NOT EXISTS notify_log (key TEXT PRIMARY KEY,price REAL,sent_at TEXT)');c.commit()


def is_repeat(c,deal,at=None):
    """True si ya se avisó de este producto a un precio igual o menor dentro del periodo de enfriamiento."""
    row=c.execute('SELECT price,sent_at FROM notify_log WHERE key=?',(dedup_key(deal),)).fetchone()
    if not row:return False
    price=deal.get('price')
    if price is not None and row['price'] is not None and price<row['price']:return False
    try:sent=datetime.fromisoformat(row['sent_at'])
    except (TypeError,ValueError):return False
    return (at or datetime.now(timezone.utc))-sent<timedelta(days=COOLDOWN_DAYS)


def remember(c,deal):
    c.execute('INSERT INTO notify_log(key,price,sent_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET price=excluded.price,sent_at=excluded.sent_at',
              (dedup_key(deal),deal.get('price'),now()))


def is_stale(deal):
    """Ficha comprobada hace más de 2 h o foto ausente en disco: send_deal la rechazaría sin avisar."""
    from pathlib import Path
    try:age=(datetime.now(timezone.utc)-datetime.fromisoformat(deal.get('checked_at'))).total_seconds()
    except (TypeError,ValueError):return True
    if age>7200:return True
    image=deal.get('image') or ''
    return not (Path(__file__).parent/'static'/'cache'/Path(image).name).exists()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--send',action='store_true');args=parser.parse_args()
    if args.send and not armed():raise SystemExit('Telegram está desactivado o faltan credenciales. No se ha enviado nada.')
    c=connect()
    try:
        _ensure_log(c)
        rows=c.execute('SELECT n.id notification_id,d.* FROM notifications n JOIN deals d ON d.id=n.deal_id WHERE n.sent_at IS NULL ORDER BY COALESCE(d.score,0) DESC,n.id LIMIT 200').fetchall()
        print(str(len(rows))+' avisos en bandeja. '+('Envío activado.' if args.send else 'Sólo lectura: no se envían mensajes.'))
        if args.send:
            sent=repeated=skipped_unwanted=skipped_size=stale=failed=0;seen=set();waiting=0
            for row in rows:
                deal=unpack(row);key=dedup_key(deal)
                bad=unwanted(deal)
                if bad or not targets_for(deal):
                    # Libros, consumibles, o ropa/calzado que no es de la talla de nadie: se descarta sin avisar.
                    if bad:skipped_unwanted+=1
                    else:skipped_size+=1
                    c.execute('UPDATE notifications SET sent_at=? WHERE id=?',(now(),row['notification_id']));c.commit();continue
                if key in seen or is_repeat(c,deal):
                    # Repetido: se da por tratado sin enviar.
                    c.execute('UPDATE notifications SET sent_at=? WHERE id=?',(now(),row['notification_id']));c.commit();repeated+=1;continue
                if sent>=MAX_PER_RUN:waiting+=1;continue  # el resto queda en bandeja para el siguiente ciclo
                if is_stale(deal):stale+=1;print('  Caducado: '+str(deal.get('title'))[:70]+' | comprobado: '+str(deal.get('checked_at'))+' | foto: '+str(deal.get('image'))[-20:]);continue  # ficha vieja o sin foto: se reintenta cuando se vuelva a comprobar
                if send_deal(deal,silent=sent>0):  # solo el primer aviso de cada tanda suena; el resto, en silencio
                    seen.add(key);remember(c,deal)
                    c.execute('UPDATE notifications SET sent_at=? WHERE id=?',(now(),row['notification_id']));c.commit();sent+=1
                else:failed+=1
            print(f'Enviados: {sent}. Repetidos omitidos: {repeated}. Libros/consumibles descartados: {skipped_unwanted}. Talla no válida: {skipped_size}. En espera por el límite: {waiting}. Caducados/sin foto (se reintentan): {stale}. Fallo de envío: {failed}.')
    finally:c.close()


if __name__=='__main__':main()
