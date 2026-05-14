import re
from src.schema import Vaga


def _contem_termo(termo: str, texto: str) -> bool:
    # Usa word boundary para evitar falsos positivos em português:
    # "intern" não deve bater em "interno", "interna", "internamente", etc.
    return bool(re.search(r"\b" + re.escape(termo) + r"\b", texto))



def calcular_score(vaga: Vaga, config: dict) -> tuple[int, list[str]]:
    texto = (vaga.titulo + " " + vaga.descricao + " " + (vaga.localizacao or "")).lower()
    tags = []

    peso_kw = config["scoring"]["keywords_tecnicas"]["peso_total"]
    categorias = config["scoring"]["keywords_tecnicas"]["termos"]

    matches = 0
    for nome_cat, termos in categorias.items():
        if any(termo.lower() in texto for termo in termos):
            matches += 1
            tags.append(nome_cat)

    score_kw = (matches / len(categorias)) * peso_kw

    # 2) setores_bonus
    peso_sb = config["scoring"]["setores_bonus"]["peso_total"]
    setores = config["scoring"]["setores_bonus"]["termos"]

    matches = 0

    for nome_set, termos in setores.items():
        if any(termo.lower() in texto for termo in termos):
            matches += 1
            tags.append(nome_set)
    
    score_setor = (matches / len(setores)) * peso_sb


    # 3) tipo_vaga

    peso_tipo = config["scoring"]["tipo_vaga"]["peso_total"]
    termos_tipo = config["scoring"]["tipo_vaga"]["obrigatorio"]

    if any(_contem_termo(termo.lower(), texto) for termo in termos_tipo):
        score_tipo = peso_tipo
        tags.append("estagio")
    else:
        score_tipo = 0

    # 4) salario
    peso_salario = config["scoring"]["salario"]["peso_total"]
    salarios = config["scoring"]["salario"]["bom_se_contem"]
    if any(salario.lower() in texto for salario in salarios):
            score_salario = peso_salario
            tags.append("beneficios")
    else:
         score_salario = 0
    
    # 5) negativos (subtrai)
    peso_negativo = config["scoring"]["negativos"]["peso_total"]
    termos_neg = config["scoring"]["negativos"]["termos"]

    if any(termo.lower() in texto for termo in termos_neg):
            penalidade = peso_negativo
            tags.append("seniority_alta")
    else :
         penalidade = 0
    
    total = max(0, min(100, int(round(
        score_kw + score_setor + score_tipo + score_salario - penalidade
    ))))
    return total, tags

def _localizacao_ok(vaga: Vaga) -> bool:
    if vaga.remoto == "remoto":
        return True
    if not vaga.localizacao:
        return True
    loc = vaga.localizacao.lower()
    return "são paulo" in loc or ", sp" in loc


def _é_estagio(vaga: Vaga, config: dict) -> bool:
    termos = config["scoring"]["tipo_vaga"]["obrigatorio"]
    texto = (vaga.titulo + " " + vaga.descricao).lower()
    return any(_contem_termo(termo.lower(), texto) for termo in termos)





def aplicar_score_e_filtrar(vagas: list[Vaga], config: dict) -> list[Vaga]:
     
    resultado = []
    filtro_loc = ["SP", "São Paulo", "são paulo"]

    for vaga in vagas :
        score, tags = calcular_score(vaga, config)

        vaga.score_fit = score
        vaga.tags_match = tags

        if score >= config["score_minimo"] and _localizacao_ok(vaga) and _é_estagio(vaga, config):
            resultado.append(vaga)
        
        


    resultado.sort(key=lambda v: v.score_fit, reverse=True)        
    return resultado
          
