# AgentFlow

Plataforma de automação com agentes de IA, construída com **LangGraph** e **Gemini**.

O projeto evolui por etapas: de um grafo simples até um sistema multiagente que usa ferramentas, lê planilhas, consulta documentos com RAG, lembra da conversa, controla o uso de tokens, guarda respostas em cache, é validado por testes automáticos e tem interface web.

![Interface do AgentFlow](docs/demo.png)

## O que já funciona

| Arquivo | O que faz |
|---|---|
| `grafo_basico.py` | Primeiro grafo do LangGraph, conectado ao Gemini |
| `agente_ferramentas.py` | Agente que decide sozinho entre responder direto ou usar ferramentas (soma e data/hora) |
| `agente_planilha.py` | Agente que lê planilhas CSV e responde perguntas sobre os dados |
| `agente_memoria.py` | Agente que lembra da conversa (memória por `thread_id`) |
| `agente_rag.py` | Agente RAG: busca em documentos e responde citando a fonte |
| `agente_multiagente.py` | Supervisor que delega a pergunta para 4 agentes especialistas e contabiliza tokens |
| `cache_respostas.py` | Cache de respostas: pergunta repetida no mesmo contexto custa 0 tokens |
| `app_web.py` | Interface web de chat (Streamlit) com painel de uso de tokens e de cache |
| `avaliar.py` | Avaliação automática: roda perguntas de teste e gera um relatório |

## Como o agente funciona

```
START -> agente -> (precisa de ferramenta?) -> ferramentas -> agente -> resposta
```

O modelo analisa a pergunta e **decide** se responde direto ou chama uma ferramenta. Depois de executar, ele volta ao agente, que usa o resultado para escrever a resposta final.

## Arquitetura multiagente

```
                 +--> planilha (ler_planilha, somar_coluna)
                 +--> calculo  (somar, data_e_hora_atual)
START -> supervisor
                 +--> loja     (buscar_documentos, RAG)
                 +--> geral    (sem ferramentas)
```

O **supervisor** lê a pergunta e escolhe qual agente especialista vai respondê-la. Cada especialista tem as suas próprias ferramentas e instruções. A interface web mostra, abaixo de cada resposta, qual agente respondeu.

## RAG sobre documentos

```
documentos (.txt) -> pedaços (chunks) -> embeddings -> índice vetorial
pergunta -> busca por similaridade -> trechos relevantes -> agente responde com a fonte
```

- Os documentos ficam na pasta `base_conhecimento/`.
- Os embeddings são gerados com `gemini-embedding-001`.
- O agente é instruído a responder **somente** com base nos trechos encontrados, a citar o arquivo de origem e a admitir quando não encontra a informação.

## Controle de tokens

- **Medição:** cada pergunta soma os tokens de entrada e de saída de todas as chamadas ao modelo (supervisor e agente especialista). A interface mostra o valor da última pergunta e o total da sessão.
- **Janela deslizante:** o modelo recebe apenas as últimas 5 mensagens da conversa, em vez do histórico inteiro, para que o custo não cresça a cada pergunta.

Exemplo de medição:

```
Pergunta: Qual o prazo de garantia do monitor?
  [supervisor] escolheu o agente: loja
Tokens: 695 de entrada + 60 de saída

Pergunta: Qual o total da coluna quantidade em vendas.csv?
  [supervisor] escolheu o agente: planilha
Tokens: 464 de entrada + 63 de saída
```

A pergunta que usa RAG gasta mais tokens de entrada, porque os trechos recuperados dos documentos entram no prompt.

## Cache de respostas

Antes de chamar o modelo, a interface procura a pergunta no cache. Se já existir uma resposta para **a mesma pergunta no mesmo contexto**, ela é devolvida na hora, **sem gastar nenhum token**.

- A chave do cache considera a pergunta **e as mensagens anteriores** da janela de contexto. Assim, uma pergunta como "E qual é o mais barato?" nunca recebe uma resposta guardada de outra conversa.
- O texto é normalizado (maiúsculas e espaços não importam), mas a correspondência é **exata**: perguntas escritas de outro jeito não reaproveitam o cache.
- As respostas ficam em `cache/respostas.json`, que não é enviado ao GitHub.
- Se os documentos da pasta `base_conhecimento/` mudarem, apague a pasta `cache/` para não devolver respostas desatualizadas.
- A avaliação automática chama o sistema direto, sem cache, para testar o modelo de verdade.

A interface mostra "resposta do cache: 0 tokens" na resposta e um contador no painel lateral.

## Avaliação automática

O script `avaliar.py` roda 6 perguntas de teste e confere duas coisas em cada uma:

1. O supervisor escolheu o **agente esperado**?
2. A resposta contém a **informação esperada**?

O resultado é salvo em [`docs/avaliacao.md`](docs/avaliacao.md).

**Resultado atual: 6 de 6 perguntas corretas** (3829 tokens de entrada + 454 de saída no total).

### O que a avaliação encontrou

Na primeira execução o resultado foi **5 de 6**. A pergunta *"Vocês vendem geladeira?"* foi enviada pelo supervisor ao agente **geral**, que não consulta os documentos, em vez do agente **loja**. A causa era a instrução do supervisor, que descrevia a loja apenas como "políticas" e não incluía perguntas sobre os produtos vendidos. Depois de ajustar a instrução, a avaliação passou de 5 para 6 acertos.

### Limitações

- São apenas 6 casos de teste, um conjunto pequeno. Serve para detectar regressões, mas não prova qualidade em todos os cenários.
- A verificação da resposta é por palavras-chave (por exemplo, "24 meses"), e não por significado.

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

### RAG

```
Pergunta: Vocês vendem geladeira?
  [supervisor] escolheu o agente: loja
  -> Ferramenta usada: buscar_documentos {'pergunta': 'Vocês vendem geladeira?'}
Resposta: Não encontrei informações sobre a venda de geladeiras nos documentos da Techponto.
```

O agente admite que não encontrou a informação, em vez de inventar uma resposta.

## Tecnologias

- Python 3.10
- LangGraph e LangChain
- Gemini (Google AI Studio): modelo de chat e embeddings
- Streamlit

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

5. Rode a interface web:
```bash
streamlit run src\agentflow\app_web.py
```

Ou rode a avaliação automática (leva alguns minutos, por causa das pausas entre as perguntas):
```bash
python src\agentflow\avaliar.py
```

> O plano gratuito do Gemini tem limite de chamadas por minuto e por dia. Se aparecer o erro 429, aguarde ou troque a variável `MODELO` no código.

## Estrutura

```
agentflow/
├── src/agentflow/       # grafos, agentes, cache, interface web e avaliação
├── base_conhecimento/   # documentos usados pelo RAG
├── dados/               # planilhas de exemplo
├── docs/                # imagens e relatório de avaliação
├── tests/
├── requirements.txt
└── .env.example
```

## Próximos passos

- [x] Memória de conversa
- [x] Sistema multiagente com supervisor
- [x] Interface web
- [x] RAG sobre documentos
- [x] RAG integrado ao supervisor e à interface web
- [x] Controle de uso de tokens e janela de contexto
- [x] Avaliação automática com perguntas de teste
- [x] Cache de respostas repetidas
- [ ] Observabilidade (rastreamento das chamadas)

## Autora

Kallymeire Coelho, [GitHub](https://github.com/kallymeire) · [LinkedIn](https://www.linkedin.com/in/kallymeire-coelho-212746263)