import unicodedata
from src.schema import Vaga


def _normalizar(texto: str) -> str:
    
    if not texto:  # ← adiciona essa linha
        return ""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )
    return sem_acento.lower().strip()

def deduplicar(vagas: list[Vaga]) -> list[Vaga] :

    visto = {}
    for vaga in vagas:
        titulo_normalizado = _normalizar(vaga.titulo)
        empresa_normalizada = _normalizar(vaga.empresa)
        print(f"chave: ({titulo_normalizado!r}, {empresa_normalizada!r})")
        chave = (titulo_normalizado, empresa_normalizada)
        chave = (titulo_normalizado, empresa_normalizada)
        if not titulo_normalizado:  # ← adiciona isso
            continue
        if chave not in visto:
            visto[chave] = vaga

    return list(visto.values())
      

        
