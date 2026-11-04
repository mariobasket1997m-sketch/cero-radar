"""Filtro de tallas para avisos: solo ropa y calzado que le valga a alguno de los perfiles.

Perfiles por destinatario (hombre / mujer; sin perfil = cualquiera de los dos):
  Hombre 1,85 m / 85 kg: arriba L-XXL, pantalón W32-36 / L32-36, calzado 44 y 45.
  Mujer 1,70 m / 60 kg:  arriba S-L,   pantalón W26-30 / L30-34, calzado 38 y 39.
Si el producto no es ropa/calzado, o no indica talla, se deja pasar.
"""
import re
from cero.taxonomy import normalize

PROFILES={
 'hombre':{'letters':{'l','xl','xxl','2xl'},'waist':set(range(32,37)),'length':set(range(32,37)),'shoes':{44,45}},
 'mujer':{'letters':{'s','m','l'},'waist':set(range(26,31)),'length':set(range(30,35)),'shoes':{38,39}},
}


def _profile(name):
    """None o 'todos' = cualquiera de los perfiles."""
    if name in PROFILES:return PROFILES[name]
    return {k:set().union(*(p[k] for p in PROFILES.values())) for k in ('letters','waist','length','shoes')}
SHOE_RE=re.compile(r'\b(?:zapatill\w*|zapato\w*|bota\w*|botin\w*|sandalia\w*|calzado|mocasin\w*|deportivas|sneakers?|chancla\w*)\b')
CLOTHING_RE=re.compile(r'\b(?:camiseta|polo|camisa|sudadera|jersey|chaqueta|abrigo|cazadora|pantalon\w*|vaquero\w*|jeans|falda|vestido|mallas?|leggings?|chandal|bermuda\w*|short\w*|maillot|culotte|ropa)\b')
# Género declarado en el título: un perfil no recibe lo que es claramente del otro género.
FEMALE_RE=re.compile(r'mujer|\b(?:women\w*|woman|femenin\w*|senora\w*|chica\w*|dama\w*|lady|ladies)\b')
MALE_RE=re.compile(r'hombre|\b(?:men|mens|man|masculin\w*|caballero\w*|chico\w*)\b')
KIDS_RE=re.compile(r'\b\d{1,2}\s*(?:anos?|meses)\b|\b(?:nino|nina|bebe|infantil|junior)\b')


def kind(deal):
    """'shoe', 'clothing' o None si no es de talla."""
    title=normalize(deal.get('title'))
    if SHOE_RE.search(title) or deal.get('product_type')=='zapatillas deportivas':return 'shoe'
    if deal.get('category')=='Moda' or deal.get('product_type') in ('ropa','ropa deportiva','ropa de ciclismo') or CLOTHING_RE.search(title):return 'clothing'
    return None


def wearable(deal,profile=None):
    k=kind(deal)
    if not k:return True
    P=_profile(profile)
    variant=normalize(deal.get('variant'));title=normalize(deal.get('title'))
    if KIDS_RE.search(variant) or KIDS_RE.search(title):return False
    gender=' '.join((title,variant))
    female=bool(FEMALE_RE.search(gender));male=bool(MALE_RE.search(gender))
    if profile=='hombre' and female and not male:return False
    if profile=='mujer' and male and not female:return False
    if not variant:
        # Sin variante: se busca la talla escrita en el título ("talla 36", "EU 36", "nº 36").
        if k=='shoe':
            nums=[int(n) for n in re.findall(r'(?:talla|tallas|eu|nº|no|num|numero|size|t)\.?\s*:?\s*(3\d|4\d)\b',title)]
            if nums:return any(n in P['shoes'] for n in nums)
        variant=title if k!='shoe' else ''
        if not variant:return True
    if k=='shoe':
        nums=[int(float(n.replace(',','.'))) for n in re.findall(r'\b(3\d|4\d)(?:[.,]\d)?\b',variant)]
        return True if not nums else any(n in P['shoes'] for n in nums)
    m=re.search(r'\b(\d{2})\s*w\b.*?\b(\d{2})\s*l\b',variant) or re.search(r'\bw\s*(\d{2})\b.*?\bl\s*(\d{2})\b',variant)
    if m:return int(m.group(1)) in P['waist'] and int(m.group(2)) in P['length']
    m=re.search(r'\b(\d{2})\s*w\b|\bw\s*(\d{2})\b',variant)
    if m:return int(m.group(1) or m.group(2)) in P['waist']
    tokens=[t for t in re.split(r'[^a-z0-9]+',variant) if t]
    letters=[t for t in tokens if t in {'xxs','xs','s','m','l','xl','xxl','2xl','3xl','4xl'}]
    if letters:return any(t in P['letters'] for t in letters)
    return True
