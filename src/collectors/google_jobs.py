import re
import time
import warnings
import httpx
from datetime import date
from urllib.parse import urlparse
from bs4 import BeautifulSoup
warnings.filterwarnings("ignore", category=RuntimeWarning, module="duckduckgo_search")
from duckduckgo_search import DDGS
from src.collectors.base import BaseCollector
from src.schema import Vaga

# Queries simples sem operadores avançados — DDG não suporta site:, OR, aspas combinadas
QUERIES = [
    "estagio data science Sao Paulo vaga",
    "estagio machine learning Sao Paulo",
    "estagio analytics dados Sao Paulo",
    "internship data analyst Sao Paulo",
    "estagio BI Sao Paulo",
    "estagio agro dados Sao Paulo",
    "intern data science Brazil Sao Paulo",
]

# Domínios já cobertos por outros coletores, bloqueados, ou que retornam listas/notícias
_SKIP_DOMAINS = {
    # já cobertos
    "linkedin.com", "br.linkedin.com",
    "gupy.io", "portal.gupy.io",
    "adzuna.com", "adzuna.com.br",
    "indeed.com", "br.indeed.com",
    # job boards que bloqueiam scraping ou retornam listas
    "glassdoor.com", "glassdoor.com.br", "glassdoor.co.uk", "glassdoor.de",
    "jooble.org", "br.jooble.org",
    "whatjobs.com", "br.whatjobs.com",
    "efinancialcareers.com",
    "catho.com.br",
    "infojobs.com.br",
    "vagas.com.br",
    # portais de estágio genéricos (não individuais)
    "ciee.org.br", "portal.ciee.org.br", "cieers.org.br",
    "nube.com.br",
    "futuraestagios.com.br", "superestagios.com.br", "portaldoestagio.com.br",
    "ciadeestagios.com.br",
    # portais institucionais / notícias
    "agencia.petrobras.com.br",
    "gazetadopovo.com.br", "concursonews.com.br", "concursosnobrasil.com.br",
    "seudinheiro.com", "dcmais.com.br",
    "wizard.com.br", "dmv.org",
}

_GENERIC_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def _domain_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lstrip("www.")
    except Exception:
        return ""


def _is_relevant_url(url: str) -> bool:
    domain = _domain_of(url)
    return not any(domain == s or domain.endswith("." + s) for s in _SKIP_DOMAINS)


def _empresa_from_domain(url: str) -> str:
    """Extrai nome da empresa limpando prefixos comuns do domínio."""
    netloc = urlparse(url).netloc.lstrip("www.")
    # Remove prefixos de páginas de carreira
    for prefix in ("careers.", "carreiras.", "jobs.", "vagas.", "trabalhe.", "recrutamento."):
        if netloc.startswith(prefix):
            netloc = netloc[len(prefix):]
    # Remove sufixo de domínio
    netloc = re.sub(r"\.(com\.br|com|org\.br|org|io|co\.uk)$", "", netloc)
    return netloc.replace("-", " ").replace(".", " ").title()


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

                relevantes = [r for r in results if _is_relevant_url(r.get("href", ""))]
                print(f"[google_jobs] '{query[:55]}' → {len(results)} resultados, {len(relevantes)} novos domínios")

                for r in relevantes:
                    url = r.get("href", "")
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    try:
                        vaga = self._processar_url(client, url, r)
                        if vaga:
                            yield vaga
                    except Exception as e:
                        print(f"[google_jobs erro] {url[:60]}: {e}")
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
        tag_re = re.compile(r"<[^>]+>")
        descricao = tag_re.sub(" ", data.get("content") or "").strip() or snippet.get("body", "")
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
        titulo = snippet.get("title", "")
        if not titulo:
            return None
        descricao = snippet.get("body", "")
        empresa = _empresa_from_domain(url)
        localizacao = ""

        try:
            r = client.get(url, headers=_GENERIC_HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup(["script", "style", "nav", "header", "footer"]):
                tag.decompose()

            h1 = soup.find("h1")
            if h1:
                titulo = h1.get_text(strip=True) or titulo

            main = soup.find("main") or soup.find("article") or soup.find("body")
            if main:
                texto = main.get_text(separator=" ", strip=True)
                descricao = re.sub(r"\s+", " ", texto)[:3000]

            # Detectar localização no texto
            loc_match = re.search(
                r"(são paulo[^,\n]*|sp[^a-z]|híbrido|remoto|presencial)",
                descricao.lower()
            )
            if loc_match:
                localizacao = loc_match.group(0).strip().title()
        except Exception:
            pass

        return Vaga(
            id=Vaga.gerar_id("google_jobs", url, titulo),
            fonte="google_jobs",
            titulo=titulo,
            empresa=empresa,
            localizacao=localizacao,
            remoto=None,
            salario=None,
            descricao=descricao,
            url=url,
            data_publicacao=None,
            data_coleta=date.today(),
        )
