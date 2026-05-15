import re
import time
import httpx
from datetime import date
from duckduckgo_search import DDGS
from src.collectors.base import BaseCollector
from src.collectors.linkedin import _strip_html
from src.schema import Vaga

QUERIES = [
    'site:boards.greenhouse.io (estágio OR intern) (dados OR "data science" OR analytics OR "machine learning") São Paulo',
    'site:jobs.lever.co (estágio OR intern) (dados OR "data science" OR analytics) São Paulo',
    '"estágio" ("data science" OR "machine learning" OR analytics OR dados) "São Paulo" -site:linkedin.com -site:gupy.io',
    '"intern" ("data analyst" OR "data scientist" OR analytics) "São Paulo"',
    '"estágio" (agro OR agtech OR agronegócio) dados "São Paulo"',
]

_GENERIC_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


class GoogleJobsCollector(BaseCollector):
    nome = "google_jobs"

    def __init__(self, config: dict):
        super().__init__(config)
        cfg = config["fontes"]["google_jobs"]
        self.max_results = cfg.get("max_results_por_query", 15)
        self.queries_override = cfg.get("queries")

    def coletar(self, termos: list[str]):
        queries = self.queries_override or QUERIES
        seen_urls: set[str] = set()

        with DDGS() as ddgs, httpx.Client(follow_redirects=True, timeout=20) as client:
            for query in queries:
                try:
                    results = list(ddgs.text(query, max_results=self.max_results))
                except Exception as e:
                    print(f"[google_jobs] DDG erro: {e}")
                    continue

                print(f"[google_jobs] query='{query[:65]}' resultados={len(results)}")
                for r in results:
                    url = r.get("href", "")
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    try:
                        vaga = self._processar_url(client, url, r)
                        if vaga:
                            yield vaga
                    except Exception as e:
                        print(f"[google_jobs erro] {url}: {e}")
                    time.sleep(0.5)
                time.sleep(2)

    def _processar_url(self, client: httpx.Client, url: str, snippet: dict) -> "Vaga | None":
        if "greenhouse.io" in url:
            return self._fetch_greenhouse(client, url, snippet)
        if "lever.co" in url:
            return self._fetch_lever(client, url, snippet)
        return self._fetch_generico(client, url, snippet)

    def _fetch_greenhouse(self, client: httpx.Client, url: str, snippet: dict) -> "Vaga | None":
        m = re.search(r"greenhouse\.io/([^/]+)/jobs/(\d+)", url)
        if not m:
            return None
        slug, job_id = m.group(1), m.group(2)
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{job_id}"
        r = client.get(api_url)
        if r.status_code != 200:
            return self._fetch_generico(client, url, snippet)
        data = r.json()
        descricao = _strip_html(data.get("content") or snippet.get("body", ""))
        loc = (data.get("location") or {}).get("name", "") or ""
        return Vaga(
            id=Vaga.gerar_id("google_jobs", url, data.get("title", "")),
            fonte="google_jobs",
            titulo=data.get("title") or snippet.get("title", ""),
            empresa=slug.replace("-", " ").title(),
            localizacao=loc,
            remoto=None,
            salario=None,
            descricao=descricao,
            url=url,
            data_publicacao=None,
            data_coleta=date.today(),
        )

    def _fetch_lever(self, client: httpx.Client, url: str, snippet: dict) -> "Vaga | None":
        m = re.search(r"lever\.co/([^/]+)/([^/?]+)", url)
        if not m:
            return None
        company, posting_id = m.group(1), m.group(2)
        api_url = f"https://api.lever.co/v0/postings/{company}/{posting_id}?mode=json"
        r = client.get(api_url)
        if r.status_code != 200:
            return self._fetch_generico(client, url, snippet)
        data = r.json()
        body_items = (data.get("descriptionBody") or {}).get("content") or []
        descricao = " ".join(
            item.get("content", "") for item in body_items if isinstance(item, dict)
        ) or snippet.get("body", "")
        loc = (data.get("categories") or {}).get("location", "") or ""
        return Vaga(
            id=Vaga.gerar_id("google_jobs", url, data.get("text", "")),
            fonte="google_jobs",
            titulo=data.get("text") or snippet.get("title", ""),
            empresa=company.replace("-", " ").title(),
            localizacao=loc,
            remoto=None,
            salario=None,
            descricao=descricao,
            url=url,
            data_publicacao=None,
            data_coleta=date.today(),
        )

    def _fetch_generico(self, client: httpx.Client, url: str, snippet: dict) -> "Vaga | None":
        try:
            r = client.get(url, headers=_GENERIC_HEADERS)
            texto = _strip_html(r.text)[:3000]
        except Exception:
            texto = snippet.get("body", "")
        titulo = snippet.get("title", "")
        if not titulo:
            return None
        return Vaga(
            id=Vaga.gerar_id("google_jobs", url, titulo),
            fonte="google_jobs",
            titulo=titulo,
            empresa="",
            localizacao="",
            remoto=None,
            salario=None,
            descricao=texto,
            url=url,
            data_publicacao=None,
            data_coleta=date.today(),
        )
