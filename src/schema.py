from pydantic import BaseModel, Field
from datetime import date, datetime
import hashlib

class Vaga(BaseModel):
    id: str
    fonte: str
    titulo: str
    empresa: str
    localizacao: str | None = None
    remoto: str | None = None
    salario: str | None = None
    descricao: str
    url: str
    data_publicacao: date | None = None
    data_coleta: date = Field(default_factory=date.today)
    score_fit : int = 0
    tags_match: list[str] = Field(default_factory=list)

    @staticmethod
    def gerar_id(fonte: str, url: str, titulo: str) -> str:

        conteudo = fonte + url + titulo
        id = hashlib.sha1(conteudo.encode()).hexdigest()[:16]

        return id
    
    def para_linha_planilha(self) -> list :

        
            resultado = [
                self.score_fit, 
                self.titulo,
                self.empresa,
                self.fonte,
                self.localizacao,
                self.remoto,
                self.salario,
                ", ".join(self.tags_match),
                self.url,
                self.data_publicacao,
                self.data_coleta,
                self.descricao[:500]
            ]
        
            return resultado
    
    @staticmethod
    def header_planilha() -> list[str]:
        return ["score", "titulo", "empresa", "fonte", "localizacao", "remoto", "salario", "tags", "url", "data_publicacao", "data_coleta", "descricao"]