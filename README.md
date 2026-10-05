# AgentFlow

Plataforma de automação com agentes de IA, construída com **LangGraph** e **Gemini**.

O projeto está em desenvolvimento e evolui por etapas: de um grafo simples até agentes que usam ferramentas, leem dados e tomam decisões.

## O que já funciona

| Arquivo | O que faz |
|---|---|
| `grafo_basico.py` | Primeiro grafo do LangGraph, conectado ao Gemini |
| `agente_ferramentas.py` | Agente que decide sozinho entre responder direto ou usar ferramentas (soma e data/hora) |
| `agente_planilha.py` | Agente que lê planilhas CSV e responde perguntas sobre os dados |

## Como o agente funciona

```
START -> agente -> (precisa de ferramenta?) -> ferramentas -> agente -> resposta
```

O modelo analisa a pergunta e **decide** se responde direto ou chama uma ferramenta. Depois de executar, ele volta ao agente, que usa o resultado para escrever a resposta final.

## Exemplo de execução

```
Pergunta: Qual o total da coluna quantidade em vendas.csv?
  -> Ferramenta usada: somar_coluna {'nome_arquivo': 'vendas.csv', 'coluna': 'quantidade'}
Resposta: O total da coluna "quantidade" no arquivo vendas.csv é 52.

Pergunta: Qual é o produto mais caro de vendas.csv?
  -> Ferramenta usada: ler_planilha {'nome_arquivo': 'vendas.csv'}
Resposta: O produto mais caro na planilha vendas.csv é o Monitor, com um preço de 899.00.
```

## Tecnologias

- Python 3.10
- LangGraph e LangChain
- Gemini (Google AI Studio)

## Como rodar

1. Clone o repositório:
```bash
git clone https://github.com/kallymeire/agentflow.git
cd agentflow
```

2. Crie e ative o ambiente virtual (Windows):
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Crie uma chave em [aistudio.google.com](https://aistudio.google.com), copie o arquivo `.env.example` para `.env` e cole a chave nele.

5. Rode um dos agentes:
```bash
python src\agentflow\agente_planilha.py
```

> O plano gratuito do Gemini tem limite de chamadas por minuto e por dia. Se aparecer o erro 429, aguarde ou troque a variável `MODELO` no código.

## Estrutura

```
agentflow/
├── src/agentflow/   # grafos e agentes
├── dados/           # planilhas de exemplo
├── tests/
├── docs/
├── requirements.txt
└── .env.example
```

## Próximos passos

- [ ] Memória de conversa
- [ ] Sistema multiagente com supervisor
- [ ] RAG sobre documentos
- [ ] Controle de custo e uso de tokens
- [ ] Avaliação e observabilidade
- [ ] Interface web

## Autora

Kallymeire Coelho, [GitHub](https://github.com/kallymeire) · [LinkedIn](https://www.linkedin.com/in/kallymeire-coelho-212746263)