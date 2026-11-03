"""Avisos preparados en bandeja local. El envío queda desactivado hasta una activación explícita."""
import json
import os
import html
import io
import re
from datetime import datetime,timezone
from cero.db import now


def enqueue(conn,deal_id,deal):
    if deal.get('status')!='verified' or deal.get('is_sample') or deal.get('image_status')!='verified':return
    if deal.get('price')==0 and deal.get('free_review')!='accepted':return
    if deal.get('price')!=0 and (deal.get('discount_pct') or 0)<80:return
    if deal.get('price')!=0 and (deal.get('score') or 0)<85:return
    previous=conn.execute('SELECT status FROM observations WHERE deal_id=? ORDER BY id DESC LIMIT 1 OFFSET 1',(deal_id,)).fetchone()
    restocked=bool(previous and previous['status']=='expired')
    conn.execute('''INSERT INTO notifications(deal_id,payload,created_at) VALUES(?,?,?)
      ON CONFLICT(deal_id,channel) DO UPDATE SET payload=excluded.payload,created_at=excluded.created_at,
      sent_at=CASE WHEN ? OR json_extract(excluded.payload,'$.price')<COALESCE(json_extract(notifications.payload,'$.price'),1e12)
      THEN NULL ELSE notifications.sent_at END''',
      (deal_id,json.dumps({'title':deal.get('title'),'url':deal.get('url'),'price':deal.get('price'),
                          'variant':deal.get('variant'),'score':deal.get('score')},ensure_ascii=False),now(),int(restocked)))


def armed():
    from cero.config import TELEGRAM_BOT_TOKEN,TELEGRAM_CHAT_ID
    return os.environ.get('TELEGRAM_ENABLED','false').lower()=='true' and bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)

def chat_targets():
    """TELEGRAM_CHAT_ID: ids separados por comas; sufijo opcional ':hombre' o ':mujer' para su perfil de tallas."""
    from cero.config import TELEGRAM_CHAT_ID
    out=[]
    for part in str(TELEGRAM_CHAT_ID).split(','):
        chat,_,profile=part.strip().partition(':')
        if chat.strip():out.append((chat.strip(),profile.strip().lower() or 'hombre'))
    return out


def targets_for(deal):
    from cero.sizes import wearable
    return [chat for chat,profile in chat_targets() if wearable(deal,profile)]


def send_deal(deal,silent=False):
    if not armed() or deal.get('status')!='verified' or deal.get('is_sample') or deal.get('image_status')!='verified':return False
    if deal.get('price')==0 and deal.get('free_review')!='accepted':return False
    if not deal.get('checked_at') or (datetime.now(timezone.utc)-datetime.fromisoformat(deal['checked_at'])).total_seconds()>7200:return False
    if deal.get('price')!=0 and (deal.get('discount_pct') or 0)<80:return False
    image=deal.get('image','')
    if not re.fullmatch(r'/static/cache/[a-f0-9]{64}\.webp',image):return False
    from pathlib import Path
    from cero.config import TELEGRAM_BOT_TOKEN,TELEGRAM_CHAT_ID
    from cero.policy import affiliate_url
    from PIL import Image
    from curl_cffi import requests
    path=Path(__file__).parent/'static'/'cache'/Path(image).name
    if not path.exists():return False
    with Image.open(path) as im:
        buffer=io.BytesIO();im.convert('RGB').save(buffer,format='JPEG',quality=88)
    title=html.escape(deal.get('title','')[:180]);url=html.escape(affiliate_url(deal['url']),quote=True)
    price=deal.get('price');currency=html.escape(deal.get('currency') or 'EUR');store=html.escape(deal.get('store',''))
    shipping='Envío por confirmar' if deal.get('shipping') is None else f"Gastos mostrados: {deal['shipping']:.2f} {currency}"
    caption=f'<b>{title}</b>\n{price:.2f} {currency} · {store}\n{shipping}\n<a href="{url}">Ver en tienda</a>'
    api=os.environ.get('TELEGRAM_API','https://api.telegram.org')
    # TELEGRAM_CHAT_ID admite varios destinatarios separados por comas (por ejemplo "123456,789012").
    chats=targets_for(deal)
    delivered=False
    for chat in chats:
        if _send_one(requests,api,TELEGRAM_BOT_TOKEN,chat,caption,buffer.getvalue(),silent):delivered=True
    return delivered


def _send_one(requests,api,token,chat,caption,photo,silent):
    flag='true' if silent else 'false'
    try:
        from curl_cffi import CurlMime
        mp=CurlMime()
        try:
            for name,value in (('chat_id',chat),('caption',caption),('parse_mode','HTML'),('disable_notification',flag)):
                mp.addpart(name=name,data=str(value).encode('utf-8'))
            mp.addpart(name='photo',content_type='image/jpeg',filename='producto.jpg',data=photo)
            response=requests.post(f'{api}/bot{token}/sendPhoto',multipart=mp,timeout=30)
        finally:mp.close()
        if response.status_code==200 and response.json().get('ok') is True:return True
    except Exception:pass
    # Si falla la foto, el aviso sale igualmente como texto con enlace.
    try:
        response=requests.post(f'{api}/bot{token}/sendMessage',data={'chat_id':chat,'text':caption,'parse_mode':'HTML','disable_web_page_preview':'false','disable_notification':flag},timeout=20)
        return response.status_code==200 and response.json().get('ok') is True
    except Exception:return False


def send_note(text):return False

def send_hello(text):return False
