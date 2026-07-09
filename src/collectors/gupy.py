import re
import time
import httpx
from datetime import date, datetime
from src.collectors.base import BaseCollector
from src.schema import Vaga

ENDPOINT = "https://portal.api.gupy.io/api/job"

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _TAG_RE.sub(" ", text or "").strip()


class GupyCollector(BaseCollector):
    nome = "gupy"

    def __init__(self, config: dict):
        super().__init__(config)
        gupy_cfg = config["fontes"]["gupy"]
        self.max_paginas = gupy_cfg["max_paginas"]
        # Termos específicos pro Gupy: a API busca só no título da vaga,
        # então frases longas ("estágio data science") quase nunca batem.
        # Termos curtos como "dados" ou "analytics" capturam muito mais.
        self.termos_override = gupy_cfg.get("termos_busca")

    def coletar(self, termos: list[str]):
        termos_efetivos = self.termos_override if self.termos_override else termos
        with httpx.Client() as client:
            for termo in termos_efetivos:
                offset = 0
                limit = 20
                for _ in range(self.max_paginas):
                    params = {"name": termo, "limit": limit, "offset": offset}
                    resp = client.get(ENDPOINT, params=params, timeout=30.0)
                    resp.raise_for_status()
                    payload = resp.json()
                    vagas = payload.get("data", [])
                    total = payload.get("pagination", {}).get("total", 0)
                    print(f"[gupy] termo='{termo}' offset={offset} vagas={len(vagas)} total={total}")
                    if not vagas:
                        break
                    for vaga_raw in vagas:
                        try:
                            yield self._normalizar(vaga_raw)
                        except Exception as e:
                            print(f"[gupy erro] {e}")
                    offset += limit
                    if offset >= total:
                        break
                    time.sleep(0.5)

    def _normalizar(self, raw: dict) -> Vaga:
        titulo = raw.get("name", "")
        empresa = raw.get("careerPageName", "")
        url = raw.get("jobUrl", "")
        cidade = raw.get("city") or ""
        estado = raw.get("state") or ""
        localizacao = f"{cidade}, {estado}".strip(", ") or None

        remoto = None
        
        if raw.get("isRemoteWork"):
            remoto = "remoto"
        elif raw.get("workplaceType") == "hybrid":
            remoto = "hibrido"

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
            remoto=remoto,
            salario=None,
            descricao=_strip_html(raw.get("description") or ""),
            url=url,
            data_publicacao=data_pub,
            data_coleta=date.today(),
        )
