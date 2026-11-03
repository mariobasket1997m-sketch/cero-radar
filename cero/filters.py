"""Exclusiones generales de avisos (para todos los destinatarios)."""
import re
from cero.taxonomy import normalize

BOOK_RE=re.compile(r'\b(?:libros?|novelas?|ebooks?|e-books?|audiolibros?|tapa blanda|tapa dura|pasta blanda|pasta dura|edicion kindle|kindle edition|paperback|hardcover|comics?|mangas?|cuentos? infantil\w*)\b')


def unwanted(deal):
    """True si el producto no debe avisarse nunca (libros)."""
    text=normalize(' '.join(str(deal.get(k) or '') for k in ('title','variant','category','subcategory','product_type')))
    return bool(BOOK_RE.search(text))
