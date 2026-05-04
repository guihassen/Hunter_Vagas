from src.collectors.base import BaseCollector
from src.schema import Vaga
import httpx
from datetime import date, datetime

ENDPOINT = "https://portal.api.gupy.io/api/job/list"

class GupyCollector(BaseCollector):
    nome = "gupy"


    def __init__(self, config: dict):
        super().__init__(config)
        self.max_paginas=config["fontes"]["gupy"]["max_paginas"]

    def coletar(self, termos: list[str]):
        with httpx.Client() as client :
            for termo in termos :
                for pagina in range(self.max_paginas):
                    offset = pagina * 20
                    params = {"name": termo, "offset": offset, "limit": 20}
                    resp = client.get(ENDPOINT, params=params, timeout=30.0)
                    resp.raise_for_status()
                    vagas = resp.json().get("data", [])

                    if not vagas :
                        break

                    for vaga_raw in vagas:
                        yield self._normalizar(vaga_raw)

    def _normalizar(self, raw: dict) -> Vaga:
        titulo = raw.get("name", "")
        empresa = raw.get("careerPageName", "")
        url = raw.get("jobUrl", "")
        cidade = raw.get("city") or ""
        estado = raw.get("state") or ""
        localizacao = f"{cidade}, {estado}".strip(", ") or None
        is_remoto = raw.get("isRemoteWork", False)

        data_pub = None
        if raw.get("publishedDate"):
            try:
                data_pub = datetime.fromisoformat(
                    raw["publishedDate"].replace("Z", "+00:00")
                ).date()
            except Exception:
                pass

        return Vaga(
            id=Vaga.gerar_id("gupy", url, titulo),
            fonte="gupy",
            titulo=titulo,
            empresa=empresa,
            localizacao=localizacao,
            remoto="remoto" if is_remoto else "presencial",
            salario=None,
            descricao=raw.get("description") or "",
            url=url,
            data_publicacao=data_pub,
            data_coleta=date.today(),
        )