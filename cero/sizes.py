"""Filtro de tallas para avisos: solo ropa y calzado que le valga a alguno de los perfiles.

Perfiles (se avisa si le sirve a cualquiera de los dos):
  Hombre 1,85 m / 85 kg: arriba L-XXL, pantalón W32-36 / L32-36, calzado 44 y 45.
  Mujer 1,70 m / 60 kg:  arriba S-L,   pantalón W26-30 / L30-34, calzado 38 y 39.
Si el producto no es ropa/calzado, o no indica talla, se deja pasar.
"""
import re
from cero.taxonomy import normalize

LETTERS={'s','m','l','xl','xxl','2xl'}
WAIST=set(range(32,37))|set(range(26,31))
LENGTH=set(range(32,37))|set(range(30,35))
SHOES={38,39,44,45}
SHOE_RE=re.compile(r'\b(?:zapatill\w*|zapato\w*|bota\w*|botin\w*|sandalia\w*|calzado|mocasin\w*|deportivas|sneakers?|chancla\w*)\b')
CLOTHING_RE=re.compile(r'\b(?:camiseta|polo|camisa|sudadera|jersey|chaqueta|abrigo|cazadora|pantalon\w*|vaquero\w*|jeans|falda|vestido|mallas?|leggings?|chandal|bermuda\w*|short\w*|maillot|culotte|ropa)\b')
KIDS_RE=re.compile(r'\b\d{1,2}\s*(?:anos?|meses)\b|\b(?:nino|nina|bebe|infantil|junior)\b')


def kind(deal):
    """'shoe', 'clothing' o None si no es de talla."""
    title=normalize(deal.get('title'))
    if SHOE_RE.search(title) or deal.get('product_type')=='zapatillas deportivas':return 'shoe'
    if deal.get('category')=='Moda' or deal.get('product_type') in ('ropa','ropa deportiva','ropa de ciclismo') or CLOTHING_RE.search(title):return 'clothing'
    return None


def wearable(deal):
    k=kind(deal)
    if not k:return True
    variant=normalize(deal.get('variant'));title=normalize(deal.get('title'))
    if KIDS_RE.search(variant) or KIDS_RE.search(title):return False
    if not variant:return True
    if k=='shoe':
        nums=[int(float(n.replace(',','.'))) for n in re.findall(r'\b(3\d|4\d)(?:[.,]\d)?\b',variant)]
        return True if not nums else any(n in SHOES for n in nums)
    m=re.search(r'\b(\d{2})\s*w\b.*?\b(\d{2})\s*l\b',variant) or re.search(r'\bw\s*(\d{2})\b.*?\bl\s*(\d{2})\b',variant)
    if m:return int(m.group(1)) in WAIST and int(m.group(2)) in LENGTH
    m=re.search(r'\b(\d{2})\s*w\b|\bw\s*(\d{2})\b',variant)
    if m:return int(m.group(1) or m.group(2)) in WAIST
    tokens=[t for t in re.split(r'[^a-z0-9]+',variant) if t]
    letters=[t for t in tokens if t in {'xxs','xs','s','m','l','xl','xxl','2xl','3xl','4xl'}]
    if letters:return any(t in LETTERS for t in letters)
    return True
