import yaml
import csv
from src.collectors.gupy import GupyCollector
from src.collectors.remotive import RemotiveCollector
from src.collectors.remoteok import RemoteokCollector
from src.collectors.adzuna import AdzunaCollector
from src.collectors.linkedin import LinkedInCollector
from src.collectors.google_jobs import GoogleJobsCollector
from src.filters import aplicar_score_e_filtrar
from src.dedup import deduplicar
from src.schema import Vaga

def main () :

    with open("config.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    vagas_raw = []

    termos = config["termos_busca"]

    if config["fontes"]["gupy"]["ativo"]:
        gupy = GupyCollector(config)
        vagas_raw.extend(gupy.coletar(termos))

    if config["fontes"]["remotive"]["ativo"]:
        remotive = RemotiveCollector(config)
        vagas_raw.extend(remotive.coletar(termos))

    if config["fontes"]["remoteok"]["ativo"]:
        remoteok = RemoteokCollector(config)
        vagas_raw.extend(remoteok.coletar(termos))

    if config["fontes"]["adzuna"]["ativo"]:
        adzuna = AdzunaCollector(config)
        vagas_raw.extend(adzuna.coletar(termos))

    if config["fontes"]["linkedin"]["ativo"]:
        linkedin = LinkedInCollector(config)
        vagas_raw.extend(linkedin.coletar(termos))

    if config["fontes"]["google_jobs"]["ativo"]:
        google_jobs = GoogleJobsCollector(config)
        vagas_raw.extend(google_jobs.coletar(termos))

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