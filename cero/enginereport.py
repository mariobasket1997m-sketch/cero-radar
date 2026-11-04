"""Resumen por buscador de las consultas de esta base de datos: cuántas hicieron, cuántos enlaces dieron y qué errores."""
from cero.db import connect


def main():
    c=connect()
    try:
        rows=c.execute("SELECT engine,COUNT(*) n,SUM(urls) urls,SUM(CASE WHEN urls=0 THEN 1 ELSE 0 END) vacias,"
                       "SUM(CASE WHEN COALESCE(error,'')!='' THEN 1 ELSE 0 END) errores,MAX(error) ultimo_error "
                       "FROM query_history WHERE created_at>=datetime('now','-1 day') GROUP BY engine ORDER BY urls DESC").fetchall()
        print('Buscadores (últimas 24 h): consultas / enlaces / vacías / errores')
        for r in rows:print(f"  {r['engine']}: {r['n']} / {r['urls'] or 0} / {r['vacias']} / {r['errores']} {r['ultimo_error'] or ''}")
        if not rows:print('  sin consultas registradas')
    finally:c.close()


if __name__=='__main__':main()
