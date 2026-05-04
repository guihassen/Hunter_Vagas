from src.collectors.base import BaseCollector
from src.schema import Vaga
import httpx
from datetime import date, datetime

ENDPOINT = "https://remoteok.com/api"


class RemoteokCollector(BaseCollector):
    nome = "remoteok"

    def __init__(self, config):
        super().__init__(config)


    def coletar(self, termos: list[str]) :
        keywords = [t.lower() for t in termos]
        with httpx.Client() as client :
            resp = client.get(ENDPOINT, timeout=30.0)
            resp.raise_for_status()
            vagas = resp.json()[1:]

            for vaga_raw in vagas:
                texto = (vaga_raw.get("position", "") + " " + vaga_raw.get("description", "")).lower()
                if any(kw in texto for kw in keywords):
                    yield self._normalizar(vaga_raw)

    def _normalizar(self, raw: dict) -> Vaga:
        titulo = raw.get("position", "")
        empresa = raw.get("company", "")
        url = raw.get("url", "")
        localizacao = raw.get("location") or ""
        descricao = raw.get("description", "")

        data_pub = None
        if raw.get("date"):
            try:
                data_pub = datetime.fromisoformat(
                    raw["date"].replace("Z", "+00:00")
                ).date()
            except Exception:
                pass

        return Vaga(
            id=Vaga.gerar_id("remoteok", url, titulo),
            fonte="remoteok",
            titulo=titulo,
            empresa=empresa,
            localizacao=localizacao,
            remoto="remoto",
            salario=None,
            descricao=descricao,
            url=url,
            data_publicacao=data_pub,
            data_coleta=date.today(),
        )
    
