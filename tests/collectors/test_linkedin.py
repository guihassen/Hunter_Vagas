import httpx
import respx

from src.collectors.linkedin import LinkedInCollector, BASE_URL, JOB_URL

SEARCH_HTML = """
<ul>
  <li>
    <div class="base-search-card" data-entity-urn="urn:li:jobPosting:1234">
      <h3 class="base-search-card__title">Estágio em Data Science</h3>
      <h4 class="base-search-card__subtitle">Acme Corp</h4>
      <span class="job-search-card__location">São Paulo, Brazil</span>
      <time datetime="2026-02-15">2 dias atrás</time>
      <a class="base-card__full-link" href="https://www.linkedin.com/jobs/view/1234/?refId=abc">ver vaga</a>
    </div>
  </li>
</ul>
"""

JOB_HTML = """
<div class="show-more-less-html__markup">
  Trabalhe com <b>Python</b> e SQL nesta vaga incrível.
</div>
"""


def _config(max_paginas=1):
    return {"fontes": {"linkedin": {"max_paginas": max_paginas, "termos_busca": ["data science"]}}}


@respx.mock
def test_coletar_extrai_card_e_descricao():
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, text=SEARCH_HTML))
    respx.get(JOB_URL.format("1234")).mock(return_value=httpx.Response(200, text=JOB_HTML))

    collector = LinkedInCollector(_config())
    vagas = list(collector.coletar(["data science"]))

    assert len(vagas) == 1
    vaga = vagas[0]
    assert vaga.titulo == "Estágio em Data Science"
    assert vaga.empresa == "Acme Corp"
    assert vaga.localizacao == "São Paulo, Brazil"
    assert vaga.url == "https://www.linkedin.com/jobs/view/1234/"
    assert "Python" in vaga.descricao and "SQL" in vaga.descricao
    assert vaga.data_publicacao.isoformat() == "2026-02-15"


@respx.mock
def test_para_de_paginar_quando_http_erro(capsys):
    respx.get(BASE_URL).mock(return_value=httpx.Response(500))

    collector = LinkedInCollector(_config(max_paginas=3))
    vagas = list(collector.coletar(["data science"]))

    assert vagas == []
    assert "HTTP 500" in capsys.readouterr().out


@respx.mock
def test_para_de_paginar_quando_sem_cards():
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, text="<ul></ul>"))

    collector = LinkedInCollector(_config(max_paginas=3))
    vagas = list(collector.coletar(["data science"]))

    assert vagas == []
    assert respx.calls.call_count == 1
