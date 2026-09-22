import httpx
import respx

from src.collectors.remotive import RemotiveCollector, ENDPOINT


def _config(categorias=("data",)):
    return {"fontes": {"remotive": {"categorias": list(categorias)}}}


@respx.mock
def test_filtra_por_keyword_no_titulo_ou_descricao():
    vagas_api = {
        "jobs": [
            {
                "title": "Data Science Intern",
                "company_name": "Acme",
                "url": "https://remotive.com/vaga/1",
                "candidate_required_location": "Brazil",
                "publication_date": "2026-02-01T00:00:00Z",
                "description": "irrelevante",
            },
            {
                # keyword só aparece na descrição, não no título
                "title": "Backend Engineer",
                "company_name": "Beta",
                "url": "https://remotive.com/vaga/2",
                "candidate_required_location": "Brazil",
                "description": "atuação com machine learning e dados",
            },
            {
                "title": "Sales Manager",
                "company_name": "Gamma",
                "url": "https://remotive.com/vaga/3",
                "candidate_required_location": "Brazil",
                "description": "vendas b2b",
            },
        ]
    }
    respx.get(ENDPOINT).mock(return_value=httpx.Response(200, json=vagas_api))

    collector = RemotiveCollector(_config())
    vagas = list(collector.coletar(["data science", "machine learning"]))

    titulos = {v.titulo for v in vagas}
    assert titulos == {"Data Science Intern", "Backend Engineer"}
    assert all(v.remoto == "remoto" for v in vagas)


@respx.mock
def test_uma_requisicao_por_categoria():
    respx.get(ENDPOINT).mock(return_value=httpx.Response(200, json={"jobs": []}))

    collector = RemotiveCollector(_config(categorias=["data", "software-dev"]))
    list(collector.coletar(["dados"]))

    assert respx.calls.call_count == 2
