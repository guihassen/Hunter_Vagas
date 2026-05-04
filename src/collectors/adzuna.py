import os
from dotenv import load_dotenv
from src.collectors.base import BaseCollector
from src.schema import Vaga
import httpx
from datetime import date, datetime


load_dotenv()

ENDPOINT = "https://api.adzuna.com/v1/api/jobs/br/search"

class AdzunaCollector(BaseCollector) :
    
    def __init__(self, config:dict) :
        super().__init__(config)
        self.app_id = os.getenv("ADZUNA_APP_ID")
        self.app_key = os.getenv("ADZUNA_APP_KEY")
        self.max_paginas=config["fontes"]["adzuna"]["max_paginas"]

    def coletar(self, termos: list[str]):
        with httpx.Client() as client :
            
            for termo in termos :
                params = {
                        "app_id": self.app_id,
                        "app_key": self.app_key,
                        "what": termo,
                        "results_per_page": 20,
                        }
                for pagina in range(1, self.max_paginas + 1):
                    url = f"{ENDPOINT}/{pagina}"
                    resp = client.get(url, params=params, timeout=30.0)
                    resp.raise_for_status()
                    vagas = resp.json().get("results", [])

                    if not vagas :
                        break

                    for vaga_raw in vagas:
                        yield self._normalizar(vaga_raw)


    def _normalizar(self, raw: dict) -> Vaga:
        titulo = raw.get("title", "")
        empresa = raw.get("company", {}).get("display_name", "")
        url = raw.get("redirect_url", "")
        localizacao = raw.get("location", {}).get("display_name") or None

        sal_min = raw.get("salary_min")
        sal_max = raw.get("salary_max")
        salario = f"R$ {sal_min}–{sal_max}" if sal_min else None

        data_pub = None
        if raw.get("created"):
            try:
                data_pub = datetime.fromisoformat(
                    raw["created"].replace("Z", "+00:00")
                ).date()
            except Exception:
                pass

        return Vaga(
            id=Vaga.gerar_id("adzuna", url, titulo),
            fonte="adzuna",
            titulo=titulo,
            empresa=empresa,
            localizacao=localizacao,
            remoto=None,
            salario=salario,
            descricao=raw.get("description") or "",
            url=url,
            data_publicacao=data_pub,
            data_coleta=date.today(),
    )