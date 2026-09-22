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

| Fonte       | Tipo                       | Status                                          |
| ----------- | -------------------------- | ------------------------------------------------ |
| Gupy        | API pública                | ✅ Ativo                                          |
| LinkedIn    | Scraping (HTML público)    | ✅ Ativo                                          |
| Google Jobs | Busca (DuckDuckGo + fetch) | ✅ Ativo                                          |
| Remotive    | API pública (gratuita)     | ⏸ Desativado por padrão (poucas vagas BR)         |
| RemoteOK    | Feed JSON público          | ⏸ Desativado por padrão (poucas vagas BR)         |
| Adzuna      | API pública                | ❌ Removido (API instável, retornava 400 recorrente) |
| Glassdoor   | —                          | ❌ Inviável — sem API pública; scraping é bloqueado por captcha/anti-bot após 1-2 requisições |

---

## Estrutura do projeto

```
vagas-hunter/
├── src/
│   ├── collectors/
│   │   ├── base.py          # Interface abstrata dos coletores
│   │   ├── gupy.py          # Coletor Gupy (API pública)
│   │   ├── linkedin.py      # Coletor LinkedIn (scraping HTML)
│   │   ├── google_jobs.py   # Coletor via busca DuckDuckGo + fetch de páginas
│   │   ├── remotive.py      # Coletor Remotive
│   │   └── remoteok.py      # Coletor RemoteOK
│   ├── schema.py            # Schema unificado (Pydantic)
│   ├── filters.py           # Sistema de scoring
│   └── dedup.py             # Deduplicação entre fontes
├── tests/
│   ├── collectors/          # Testes unitários de cada coletor (mocks de rede)
│   └── test_integration.py  # Teste integrado do pipeline completo
├── .github/workflows/
│   └── scrape.yml           # GitHub Actions (a implementar)
├── data/
│   └── vagas.csv            # Output gerado
├── config.yaml              # Perfil de busca e pesos do scoring
├── main.py                  # Orquestrador
└── requirements.txt
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

Nenhuma credencial é necessária — todas as fontes ativas hoje (Gupy, LinkedIn, Google Jobs) são públicas e não exigem chave de API.

**Perfil de busca**

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
beautifulsoup4
gspread
google-auth
duckduckgo-search
```

---

## Testes

```bash
pip install -r requirements-dev.txt
pytest
```

Cada coletor tem testes unitários que mockam a rede (`respx`/HTML fixo), e há um teste de integração (`tests/test_integration.py`) que roda o pipeline completo — coleta de múltiplas fontes (stubadas), dedup, scoring e geração do CSV — sem tocar em nenhuma API real.

---

## Roadmap

- [ ] Integração com Google Sheets
- [ ] Automação via GitHub Actions (2x por dia)
- [ ] Notificação por email/Telegram pra vagas com score alto

**Descartado:** Glassdoor — não tem API pública (a antiga API de parceiros foi descontinuada) e o scraping do site é bloqueado por captcha/anti-bot já na segunda requisição consecutiva.

---

## Aviso

Este projeto é para uso pessoal e educacional. Respeite os Termos de Serviço de cada plataforma. As APIs utilizadas são públicas e gratuitas dentro dos limites de uso documentados.
