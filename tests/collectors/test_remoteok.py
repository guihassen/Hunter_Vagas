import httpx
import respx

from src.collectors.remoteok import RemoteokCollector, ENDPOINT


@respx.mock
def test_ignora_primeiro_item_de_legal_notice_e_filtra_por_keyword():
    payload = [
        {"legal": "https://remoteok.com/legal"},
        {
            "position": "Data Analyst",
            "company": "Acme",
            "url": "https://remoteok.com/vaga/1",
            "location": "Worldwide",
            "description": "analytics e dashboards",
            "date": "2026-03-01T00:00:00Z",
        },
        {
            "position": "DevOps Engineer",
            "company": "Beta",
            "url": "https://remoteok.com/vaga/2",
            "location": "Worldwide",
            "description": "kubernetes e terraform",
            "date": "2026-03-01T00:00:00Z",
        },
    ]
    respx.get(ENDPOINT).mock(return_value=httpx.Response(200, json=payload))

    collector = RemoteokCollector({})
    vagas = list(collector.coletar(["data", "analytics"]))

    assert len(vagas) == 1
    vaga = vagas[0]
    assert vaga.titulo == "Data Analyst"
    assert vaga.fonte == "remoteok"
    assert vaga.remoto == "remoto"
    assert vaga.data_publicacao.isoformat() == "2026-03-01"
