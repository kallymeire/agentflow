# AgentFlow

Plataforma de automação com agentes de IA, construída com **LangGraph** e **Gemini**.

O projeto está em desenvolvimento e evolui por etapas: de um grafo simples até agentes que usam ferramentas, leem dados, lembram da conversa e trabalham em equipe com um supervisor.

## O que já funciona

| Arquivo | O que faz |
|---|---|
| `grafo_basico.py` | Primeiro grafo do LangGraph, conectado ao Gemini |
| `agente_ferramentas.py` | Agente que decide sozinho entre responder direto ou usar ferramentas (soma e data/hora) |
| `agente_planilha.py` | Agente que lê planilhas CSV e responde perguntas sobre os dados |
| `agente_memoria.py` | Agente que lembra da conversa (memória por `thread_id`) |
| `agente_multiagente.py` | Supervisor que delega a pergunta para agentes especialistas |

## Como o agente funciona

```
START -> agente -> (precisa de ferramenta?) -> ferramentas -> agente -> resposta
```

O modelo analisa a pergunta e **decide** se responde direto ou chama uma ferramenta. Depois de executar, ele volta ao agente, que usa o resultado para escrever a resposta final.

## Arquitetura multiagente

```
                 +--> planilha (ler_planilha, somar_coluna)
START -> supervisor --> calculo (somar, data_e_hora_atual)
                 +--> geral (sem ferramentas)
```

O **supervisor** lê a pergunta e escolhe qual agente especialista vai respondê-la. Cada especialista tem as suas próprias ferramentas e instruções.

## Exemplos de execução

### Agente com ferramentas

```
Pergunta: Qual o total da coluna quantidade em vendas.csv?
  -> Ferramenta usada: somar_coluna {'nome_arquivo': 'vendas.csv', 'coluna': 'quantidade'}
Resposta: O total da coluna "quantidade" no arquivo vendas.csv é 52.
```

### Agente com memória

```
Pergunta: Qual é o produto mais caro de vendas.csv?
Resposta: O produto mais caro é o Monitor, com um preço de 899,00.

Pergunta: E qual é o mais barato?
Resposta: O produto mais barato é o Mouse, com um preço de 45,50.
```

Na segunda pergunta o agente não recebeu o nome da planilha: ele entendeu pelo contexto da conversa.

### Sistema multiagente

```
Pergunta: Qual o total da coluna quantidade em vendas.csv?
  [supervisor] escolheu o agente: planilha
  -> Ferramenta usada: somar_coluna {...}
Resposta: O total da coluna "quantidade" no arquivo vendas.csv é 52.

Pergunta: Que dia e hora são agora?
  [supervisor] escolheu o agente: calculo
  -> Ferramenta usada: data_e_hora_atual {}
Resposta: Agora são 21:15 do dia 05/10/2026.
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

4. Crie uma chave em [aistudio.google.com](https://aistudio.google.com), copie o arquivo `.env.example` para `.env` e cole a chave nele. O arquivo `.env` nunca deve ser enviado ao GitHub.

5. Rode um dos agentes:
```bash
python src\agentflow\agente_multiagente.py
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

- [x] Memória de conversa
- [x] Sistema multiagente com supervisor
- [ ] Interface web
- [ ] RAG sobre documentos
- [ ] Controle de custo e uso de tokens
- [ ] Avaliação e observabilidade

## Autora

Kallymeire Coelho, [GitHub](https://github.com/kallymeire) · [LinkedIn](https://www.linkedin.com/in/kallymeire-coelho-212746263)