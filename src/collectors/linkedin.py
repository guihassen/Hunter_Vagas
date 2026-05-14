import re
import time
import httpx
from datetime import date, datetime
from bs4 import BeautifulSoup
from src.collectors.base import BaseCollector
from src.schema import Vaga

BASE_URL = "https://www.linkedin.com/jobs/search/"
JOB_URL = "https://www.linkedin.com/jobs/view/{}/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
}

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _TAG_RE.sub(" ", text or "").strip()


class LinkedInCollector(BaseCollector):
    nome = "linkedin"

    def __init__(self, config: dict):
        super().__init__(config)
        li_cfg = config["fontes"]["linkedin"]
        self.max_paginas = li_cfg["max_paginas"]

    def coletar(self, termos: list[str]):
        with httpx.Client(follow_redirects=True) as client:
            for termo in termos:
                for pagina in range(self.max_paginas):
                    start = pagina * 25
                    params = {
                        "keywords": termo,
                        "location": "São Paulo",
                        "f_JT": "I",
                        "start": start,
                    }
                    resp = client.get(BASE_URL, params=params, headers=HEADERS, timeout=30.0)
                    if resp.status_code != 200:
                        print(f"[linkedin] HTTP {resp.status_code} para termo='{termo}'")
                        break

                    cards = self._extrair_cards(resp.text)
                    print(f"[linkedin] termo='{termo}' start={start} vagas={len(cards)}")
                    if not cards:
                        break

                    for card in cards:
                        try:
                            descricao = self._buscar_descricao(client, card["job_id"])
                            yield self._normalizar(card, descricao)
                        except Exception as e:
                            print(f"[linkedin erro] {e}")
                        time.sleep(1)

                    time.sleep(2)

    def _extrair_cards(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.find_all("div", class_=re.compile(r"base-search-card"))
        result = []
        for card in cards:
            titulo_el = card.find(class_=re.compile(r"base-search-card__title"))
            empresa_el = card.find(class_=re.compile(r"base-search-card__subtitle"))
            loc_el = card.find(class_=re.compile(r"job-search-card__location"))
            time_el = card.find("time")
            link_el = card.find("a", class_=re.compile(r"base-card__full-link"))

            if not titulo_el:
                continue

            urn = card.get("data-entity-urn", "")
            job_id = urn.split(":")[-1] if urn else ""

            result.append({
                "titulo": titulo_el.get_text(strip=True),
                "empresa": empresa_el.get_text(strip=True) if empresa_el else "",
                "localizacao": loc_el.get_text(strip=True) if loc_el else "",
                "data": time_el.get("datetime") if time_el else None,
                "url": link_el.get("href", "").split("?")[0] if link_el else "",
                "job_id": job_id,
            })
        return result

    def _buscar_descricao(self, client: httpx.Client, job_id: str) -> str:
        if not job_id:
            return ""
        resp = client.get(JOB_URL.format(job_id), headers=HEADERS, timeout=30.0)
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        el = soup.find(class_=re.compile(r"show-more-less-html__markup"))
        return _strip_html(str(el)) if el else ""

    def _normalizar(self, raw: dict, descricao: str) -> Vaga:
        data_pub = None
        if raw.get("data"):
            try:
                data_pub = datetime.fromisoformat(raw["data"]).date()
            except Exception:
                pass

        return Vaga(
            id=Vaga.gerar_id("linkedin", raw["url"], raw["titulo"]),
            fonte="linkedin",
            titulo=raw["titulo"],
            empresa=raw["empresa"],
            localizacao=raw["localizacao"],
            remoto=None,
            salario=None,
            descricao=descricao,
            url=raw["url"],
            data_publicacao=data_pub,
            data_coleta=date.today(),
        )
