import unicodedata
from src.schema import Vaga


def _normalizar(texto: str) -> str:
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
        chave = (titulo_normalizado, empresa_normalizada)
        if chave not in visto:
            visto[chave] = vaga
    
        return list(visto.values())
      

        
