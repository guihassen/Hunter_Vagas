import httpx
import respx

from src.collectors import google_jobs as gj
from src.collectors.google_jobs import GoogleJobsCollector, _is_relevant_url, _empresa_from_domain


def test_is_relevant_url_bloqueia_dominios_conhecidos():
    assert _is_relevant_url("https://www.linkedin.com/jobs/view/123") is False
    assert _is_relevant_url("https://www.glassdoor.com.br/vaga/1") is False
    assert _is_relevant_url("https://careers.empresa-x.com/vaga/1") is True


def test_empresa_from_domain_limpa_prefixos_e_sufixos():
    assert _empresa_from_domain("https://careers.minha-empresa.com.br/vaga") == "Minha Empresa"


class _FakeDDGS:
    def __init__(self, resultados):
        self._resultados = resultados

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def text(self, query, max_results=15):
        return self._resultados


def _config(max_results=15, queries=None):
    cfg = {"fontes": {"google_jobs": {"max_results_por_query": max_results}}}
    if queries is not None:
        cfg["fontes"]["google_jobs"]["queries"] = queries
    return cfg


@respx.mock
def test_coletar_ignora_dominios_bloqueados_e_usa_fetch_generico(monkeypatch):
    resultados = [
        {"href": "https://www.linkedin.com/jobs/view/1", "title": "ignorado", "body": "x"},
        {
            "href": "https://careers.acme.com/vaga/1",
            "title": "Estágio Dados",
            "body": "trecho do snippet",
        },
    ]
    monkeypatch.setattr(gj, "DDGS", lambda: _FakeDDGS(resultados))
    respx.get("https://careers.acme.com/vaga/1").mock(
        return_value=httpx.Response(200, text="<html><body><h1>Estágio em Dados</h1><main>corpo da vaga</main></body></html>")
    )

    collector = GoogleJobsCollector(_config(queries=["estagio dados"]))
    vagas = list(collector.coletar(["dados"]))

    assert len(vagas) == 1
    assert vagas[0].titulo == "Estágio em Dados"
    assert vagas[0].fonte == "google_jobs"
    assert vagas[0].empresa == "Acme"


@respx.mock
def test_coletar_deduplica_urls_entre_queries(monkeypatch):
    resultado = [{"href": "https://careers.acme.com/vaga/1", "title": "Vaga", "body": "x"}]
    monkeypatch.setattr(gj, "DDGS", lambda: _FakeDDGS(resultado))
    respx.get("https://careers.acme.com/vaga/1").mock(
        return_value=httpx.Response(200, text="<html><body><main>corpo</main></body></html>")
    )

    collector = GoogleJobsCollector(_config(queries=["query 1", "query 2"]))
    vagas = list(collector.coletar(["dados"]))

    assert len(vagas) == 1


@respx.mock
def test_fetch_greenhouse_usa_api_oficial(monkeypatch):
    monkeypatch.setattr(gj, "DDGS", lambda: _FakeDDGS([]))
    respx.get("https://boards-api.greenhouse.io/v1/boards/acme/jobs/999").mock(
        return_value=httpx.Response(
            200,
            json={
                "title": "Estágio Data Science",
                "location": {"name": "São Paulo"},
                "content": "<p>Descrição <b>completa</b></p>",
            },
        )
    )

    collector = GoogleJobsCollector(_config())
    vaga = collector._fetch_greenhouse(
        httpx.Client(),
        "https://boards.greenhouse.io/acme/jobs/999",
        {"title": "snippet", "body": "snippet body"},
    )

    assert vaga.titulo == "Estágio Data Science"
    assert vaga.empresa == "Acme"
    assert vaga.localizacao == "São Paulo"
    assert vaga.descricao == "Descrição  completa"


@respx.mock
def test_fetch_lever_usa_api_oficial(monkeypatch):
    monkeypatch.setattr(gj, "DDGS", lambda: _FakeDDGS([]))
    respx.get("https://api.lever.co/v0/postings/acme/abc123").mock(
        return_value=httpx.Response(
            200,
            json={
                "text": "Estágio Analytics",
                "categories": {"location": "Remoto"},
                "descriptionBody": {"content": [{"content": "Descrição via lever"}]},
            },
        )
    )

    collector = GoogleJobsCollector(_config())
    vaga = collector._fetch_lever(
        httpx.Client(),
        "https://jobs.lever.co/acme/abc123",
        {"title": "snippet", "body": "snippet body"},
    )

    assert vaga.titulo == "Estágio Analytics"
    assert vaga.empresa == "Acme"
    assert vaga.localizacao == "Remoto"
    assert vaga.descricao == "Descrição via lever"
