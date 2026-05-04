from src.collectors.base import BaseCollector
from src.schema import Vaga
import httpx
from datetime import date, datetime

ENDPOINT = "https://remotive.com/api/remote-jobs"


class RemotiveCollector(BaseCollector):
    nome = "remotive"

    def __init__(self, config):
        super().__init__(config)
        self.categorias = config["fontes"]["remotive"]["categorias"]

    def coletar(self, termos: list[str]) :
        keywords = [t.lower() for t in termos]
        with httpx.Client() as client :
            for categoria in self.categorias :
                params = {"category": categoria}
                resp = client.get(ENDPOINT, params=params, timeout=30.0)
                resp.raise_for_status()
                vagas = resp.json().get("jobs", [])

                for vaga_raw in vagas:
                    
                    texto = (vaga_raw.get("title") or "" + vaga_raw.get("description") or "").lower()
                    if any(kw in texto for kw in keywords):
                        yield self._normalizar(vaga_raw)

    def _normalizar(self, raw: dict) -> Vaga:
        titulo = raw.get("title", "")
        empresa = raw.get("company_name", "")
        url = raw.get("url", "")
        localizacao = raw.get("candidate_required_location") or ""

        data_pub = None
        if raw.get("publication_date"):
            try:
                data_pub = datetime.fromisoformat(
                    raw["publication_date"].replace("Z", "+00:00")
                ).date()
            except Exception:
                pass

        return Vaga(
            id=Vaga.gerar_id("remotive", url, titulo),
            fonte="remotive",
            titulo=titulo,
            empresa=empresa,
            localizacao=localizacao,
            remoto="remoto",
            salario=None,
            descricao=raw.get("description") or "",
            url=url,
            data_publicacao=data_pub,
            data_coleta=date.today(),
        )
    