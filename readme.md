# 🎯 Vagas Hunter

Scraper automatizado de vagas de estágio em Data Science, Machine Learning e Análise de Dados. Coleta vagas de múltiplas fontes, pontua cada uma por fit com seu perfil e exporta tudo pra uma planilha CSV ordenada por relevância.

---

## Como funciona

O projeto varre múltiplas fontes de vagas, normaliza tudo num schema único e aplica um sistema de scoring (0–100) baseado no seu perfil. Em vez de ler 500 vagas manualmente, você recebe as top vagas ordenadas por relevância.

**Sistema de scoring:**

- Keywords técnicas (ML, Python, SQL, BI) — peso 40
- Setores de interesse (consultoria, agronegócio) — peso 20
- Tipo de vaga (estágio/intern) — peso 20
- Benefícios mencionados — peso 10
- Penalidade pra vagas sênior/pleno — peso -10

---

## Fontes suportadas

| Fonte    | Tipo                   | Status                                |
| -------- | ---------------------- | ------------------------------------- |
| Adzuna   | API pública (gratuita) | ✅ Ativo                              |
| Remotive | API pública (gratuita) | ✅ Ativo                              |
| RemoteOK | Feed JSON público      | ✅ Ativo                              |
| Gupy     | API pública            | ⏸ Desativado (endpoint descontinuado) |

---

## Estrutura do projeto

```
vagas-hunter/
├── src/
│   ├── collectors/
│   │   ├── base.py          # Interface abstrata dos coletores
│   │   ├── adzuna.py        # Coletor Adzuna (API oficial)
│   │   ├── remotive.py      # Coletor Remotive
│   │   ├── remoteok.py      # Coletor RemoteOK
│   │   └── gupy.py          # Coletor Gupy (desativado)
│   ├── schema.py            # Schema unificado (Pydantic)
│   ├── filters.py           # Sistema de scoring
│   └── dedup.py             # Deduplicação entre fontes
├── .github/workflows/
│   └── scrape.yml           # GitHub Actions (a implementar)
├── data/
│   └── vagas.csv            # Output gerado
├── config.yaml              # Perfil de busca e pesos do scoring
├── main.py                  # Orquestrador
├── requirements.txt
└── .env                     # Credenciais (não versionar)
```

---

## Instalação

**Pré-requisitos:** Python 3.11+

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/vagas-hunter.git
cd vagas-hunter

# Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instale as dependências
pip install -r requirements.txt
```

---

## Configuração

**1. Credenciais**

Crie um arquivo `.env` na raiz:

```
ADZUNA_APP_ID=seu_app_id
ADZUNA_APP_KEY=sua_app_key
```

Obtenha suas credenciais gratuitamente em [developers.adzuna.com](https://developers.adzuna.com).

**2. Perfil de busca**

Edite o `config.yaml` para ajustar:

- `termos_busca` — keywords enviadas pra cada API
- `score_minimo` — nota mínima pra aparecer no output
- `scoring` — pesos e termos de cada dimensão
- `fontes` — ativa/desativa cada fonte

---

## Uso

```bash
python main.py
```

O resultado é salvo em `data/vagas.csv` ordenado por score decrescente.

**Colunas do CSV:**

| Coluna       | Descrição                  |
| ------------ | -------------------------- |
| score        | Fit com seu perfil (0–100) |
| título       | Nome da vaga               |
| empresa      | Nome da empresa            |
| fonte        | Origem da vaga             |
| localização  | Cidade/estado              |
| modalidade   | remoto / presencial        |
| salário      | Valor se disponível        |
| tags         | Keywords que bateram       |
| url          | Link direto pra vaga       |
| publicada_em | Data de publicação         |
| coletada_em  | Data da coleta             |
| descrição    | Trecho da descrição        |

---

## Dependências

```
httpx
tenacity
pydantic
pyyaml
gspread
google-auth
python-dotenv
```

---

## Roadmap

- [ ] Integração com Google Sheets
- [ ] Automação via GitHub Actions (2x por dia)
- [ ] Reativar coletor Gupy quando API voltar
- [ ] Notificação por email/Telegram pra vagas com score alto

---

## Aviso

Este projeto é para uso pessoal e educacional. Respeite os Termos de Serviço de cada plataforma. As APIs utilizadas são públicas e gratuitas dentro dos limites de uso documentados.
