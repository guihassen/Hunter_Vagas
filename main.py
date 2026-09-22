import yaml
import csv
from src.collectors.gupy import GupyCollector
from src.collectors.remotive import RemotiveCollector
from src.collectors.remoteok import RemoteokCollector
from src.collectors.linkedin import LinkedInCollector
from src.collectors.google_jobs import GoogleJobsCollector
from src.filters import aplicar_score_e_filtrar
from src.dedup import deduplicar
from src.schema import Vaga

def _coletar(nome: str, collector, termos: list[str], vagas_raw: list):
    # Uma fonte instável (erro de rede, bloqueio anti-bot, etc.) não pode
    # derrubar a coleta das demais nem descartar o que já foi obtido.
    try:
        vagas_raw.extend(collector.coletar(termos))
    except Exception as e:
        print(f"[main] fonte '{nome}' falhou e foi ignorada: {e}")


def main () :

    with open("config.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    vagas_raw = []

    termos = config["termos_busca"]

    if config["fontes"]["gupy"]["ativo"]:
        _coletar("gupy", GupyCollector(config), termos, vagas_raw)

    if config["fontes"]["remotive"]["ativo"]:
        _coletar("remotive", RemotiveCollector(config), termos, vagas_raw)

    if config["fontes"]["remoteok"]["ativo"]:
        _coletar("remoteok", RemoteokCollector(config), termos, vagas_raw)

    if config["fontes"]["linkedin"]["ativo"]:
        _coletar("linkedin", LinkedInCollector(config), termos, vagas_raw)

    if config["fontes"]["google_jobs"]["ativo"]:
        _coletar("google_jobs", GoogleJobsCollector(config), termos, vagas_raw)

    vagas_dedup = deduplicar(vagas_raw)
    print(f"Total coletado: {len(vagas_raw)}")
    print(f"Após dedup: {len(vagas_dedup)}")

    vagas_filtradas = aplicar_score_e_filtrar(vagas_dedup, config)
    print(f"Após filtro de score: {len(vagas_filtradas)}")

    with open("data/vagas.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(Vaga.header_planilha())
        for vaga in vagas_filtradas:
            writer.writerow(vaga.para_linha_planilha())


if __name__ == "__main__":
    main()