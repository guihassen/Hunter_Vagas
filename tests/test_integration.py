import csv
from datetime import date

import main as main_module
from src.schema import Vaga


def _vaga(fonte, titulo, empresa, url, descricao, remoto=None, localizacao="São Paulo, SP"):
    return Vaga(
        id=Vaga.gerar_id(fonte, url, titulo),
        fonte=fonte,
        titulo=titulo,
        empresa=empresa,
        localizacao=localizacao,
        remoto=remoto,
        salario=None,
        descricao=descricao,
        url=url,
        data_publicacao=date(2026, 1, 1),
        data_coleta=date.today(),
    )


class _StubCollector:
    def __init__(self, vagas):
        self._vagas = vagas

    def coletar(self, termos):
        return iter(self._vagas)


class _FailingCollector:
    """Simula uma fonte que produz algumas vagas e então quebra a conexão
    (ex.: httpx.ReadError por reset de conexão no meio da paginação)."""

    def __init__(self, vagas_antes_do_erro):
        self._vagas = vagas_antes_do_erro

    def coletar(self, termos):
        yield from self._vagas
        raise ConnectionError("connection reset by peer")


def test_pipeline_completo_agrega_dedupe_filtra_e_escreve_csv(monkeypatch, tmp_path):
    gupy_vagas = [
        _vaga(
            "gupy",
            "Estágio em Data Science",
            "Acme",
            "https://gupy.io/vaga/1",
            "Trabalhe com python, sql e machine learning nesta vaga de estágio.",
        )
    ]
    linkedin_vagas = [
        # duplicata (mesmo título+empresa, normalizado) da vaga do gupy -> deve ser removida no dedup
        _vaga(
            "linkedin",
            "estágio em data science",
            "ACME",
            "https://linkedin.com/jobs/view/2",
            "vaga duplicada",
        ),
        _vaga(
            "linkedin",
            "Estágio Analytics Agro",
            "Beta Agro",
            "https://linkedin.com/jobs/view/3",
            "Estágio em analytics e agronegócio, com python e power bi.",
        ),
    ]
    google_jobs_vagas = [
        # não deve passar no filtro de score (sem keyword técnica nem tipo de vaga)
        _vaga(
            "google_jobs",
            "Estágio Comercial",
            "Gamma",
            "https://gamma.com/vagas/4",
            "vaga de vendas e atendimento ao cliente",
        )
    ]

    monkeypatch.setattr(main_module, "GupyCollector", lambda config: _StubCollector(gupy_vagas))
    monkeypatch.setattr(main_module, "LinkedInCollector", lambda config: _StubCollector(linkedin_vagas))
    monkeypatch.setattr(main_module, "GoogleJobsCollector", lambda config: _StubCollector(google_jobs_vagas))
    monkeypatch.setattr(main_module, "RemotiveCollector", lambda config: _StubCollector([]))
    monkeypatch.setattr(main_module, "RemoteokCollector", lambda config: _StubCollector([]))

    with open(main_module.__file__.replace("main.py", "config.yaml"), encoding="utf-8") as f:
        import yaml

        config = yaml.safe_load(f)
    config["fontes"]["gupy"]["ativo"] = True
    config["fontes"]["linkedin"]["ativo"] = True
    config["fontes"]["google_jobs"]["ativo"] = True
    config["fontes"]["remotive"]["ativo"] = False
    config["fontes"]["remoteok"]["ativo"] = False

    (tmp_path / "data").mkdir()
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f)

    monkeypatch.chdir(tmp_path)

    main_module.main()

    csv_path = tmp_path / "data" / "vagas.csv"
    assert csv_path.exists()

    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.reader(f))

    header, *linhas = rows
    assert header == Vaga.header_planilha()

    titulos = [linha[1] for linha in linhas]
    empresas = {linha[2] for linha in linhas}

    # a duplicata do linkedin não aparece; a vaga sem relevância técnica (Gamma) é filtrada
    assert set(titulos) == {"Estágio em Data Science", "Estágio Analytics Agro"}
    assert empresas == {"Acme", "Beta Agro"}
    assert len(linhas) == 2

    scores = [int(linha[0]) for linha in linhas]
    assert scores == sorted(scores, reverse=True)


def test_fonte_com_erro_de_rede_nao_derruba_pipeline(monkeypatch, tmp_path, capsys):
    gupy_vagas = [
        _vaga(
            "gupy",
            "Estágio em Data Science",
            "Acme",
            "https://gupy.io/vaga/1",
            "Trabalhe com python, sql e machine learning nesta vaga de estágio.",
        )
    ]
    linkedin_vagas_antes_do_erro = [
        _vaga(
            "linkedin",
            "Estágio Analytics Agro",
            "Beta Agro",
            "https://linkedin.com/jobs/view/3",
            "Estágio em analytics e agronegócio, com python e power bi.",
        )
    ]

    monkeypatch.setattr(main_module, "GupyCollector", lambda config: _StubCollector(gupy_vagas))
    monkeypatch.setattr(
        main_module, "LinkedInCollector", lambda config: _FailingCollector(linkedin_vagas_antes_do_erro)
    )
    monkeypatch.setattr(main_module, "GoogleJobsCollector", lambda config: _StubCollector([]))
    monkeypatch.setattr(main_module, "RemotiveCollector", lambda config: _StubCollector([]))
    monkeypatch.setattr(main_module, "RemoteokCollector", lambda config: _StubCollector([]))

    with open(main_module.__file__.replace("main.py", "config.yaml"), encoding="utf-8") as f:
        import yaml

        config = yaml.safe_load(f)
    for fonte in ("gupy", "linkedin", "google_jobs"):
        config["fontes"][fonte]["ativo"] = True
    for fonte in ("remotive", "remoteok"):
        config["fontes"][fonte]["ativo"] = False

    (tmp_path / "data").mkdir()
    with open(tmp_path / "config.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f)

    monkeypatch.chdir(tmp_path)

    main_module.main()  # não deve levantar exceção

    csv_path = tmp_path / "data" / "vagas.csv"
    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.reader(f))

    titulos = {linha[1] for linha in rows[1:]}
    # gupy e as vagas do linkedin coletadas ANTES do erro de rede devem sobreviver
    assert titulos == {"Estágio em Data Science", "Estágio Analytics Agro"}
    assert "fonte 'linkedin' falhou e foi ignorada" in capsys.readouterr().out
