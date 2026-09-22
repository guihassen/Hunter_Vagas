import httpx
import respx

from src.collectors.gupy import GupyCollector, ENDPOINT
from src.schema import Vaga


def _config(max_paginas=5):
    return {"fontes": {"gupy": {"max_paginas": max_paginas, "termos_busca": ["dados"]}}}


@respx.mock
def test_coletar_normaliza_e_para_na_pagina_vazia():
    pagina1 = {
        "data": [
            {
                "id": 1,
                "name": "Estágio em Dados",
                "careerPageName": "Empresa X",
                "jobUrl": "https://gupy.io/vaga/1",
                "city": "São Paulo",
                "state": "SP",
                "isRemoteWork": False,
                "workplaceType": "hybrid",
                "description": "<p>Trabalhe com <b>Python</b> e SQL</p>",
                "publishedDate": "2026-01-10T12:00:00Z",
            }
        ],
        "pagination": {"total": 1},
    }
    route = respx.get(ENDPOINT).mock(
        return_value=httpx.Response(200, json=pagina1)
    )

    collector = GupyCollector(_config())
    vagas = list(collector.coletar(["dados"]))

    assert route.called
    assert len(vagas) == 1
    vaga = vagas[0]
    assert isinstance(vaga, Vaga)
    assert vaga.fonte == "gupy"
    assert vaga.titulo == "Estágio em Dados"
    assert vaga.empresa == "Empresa X"
    assert vaga.localizacao == "São Paulo, SP"
    assert vaga.remoto == "hibrido"
    assert vaga.descricao == "Trabalhe com  Python  e SQL"
    assert vaga.data_publicacao.isoformat() == "2026-01-10"


@respx.mock
def test_coletar_para_quando_pagina_sem_vagas():
    route = respx.get(ENDPOINT).mock(
        return_value=httpx.Response(200, json={"data": [], "pagination": {"total": 0}})
    )

    collector = GupyCollector(_config())
    vagas = list(collector.coletar(["dados"]))

    assert vagas == []
    assert route.call_count == 1


@respx.mock
def test_coletar_pagina_ate_max_paginas_quando_total_nao_bate():
    # total sempre maior que o offset acumulado -> deve parar em max_paginas
    respx.get(ENDPOINT).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": 1,
                        "name": "Estágio Analytics",
                        "careerPageName": "Empresa Y",
                        "jobUrl": "https://gupy.io/vaga/2",
                        "isRemoteWork": True,
                    }
                ],
                "pagination": {"total": 999},
            },
        )
    )

    collector = GupyCollector(_config(max_paginas=3))
    vagas = list(collector.coletar(["dados"]))

    assert len(vagas) == 3
    assert all(v.remoto == "remoto" for v in vagas)


@respx.mock
def test_erro_de_normalizacao_nao_interrompe_coleta(capsys):
    respx.get(ENDPOINT).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {"id": 1, "name": None, "jobUrl": "https://gupy.io/vaga/3"},
                    {
                        "id": 2,
                        "name": "Estágio válido",
                        "careerPageName": "Empresa Z",
                        "jobUrl": "https://gupy.io/vaga/4",
                    },
                ],
                "pagination": {"total": 2},
            },
        )
    )

    collector = GupyCollector(_config())
    vagas = list(collector.coletar(["dados"]))

    assert len(vagas) == 1
    assert vagas[0].titulo == "Estágio válido"
    assert "[gupy erro]" in capsys.readouterr().out
