import time

import streamlit as st

from agente_multiagente import grafo
from cache_respostas import buscar, salvar
from observabilidade import ler, registrar, resumo

# Janela deslizante: o modelo recebe só as últimas mensagens da conversa
JANELA = 5

st.set_page_config(page_title="AgentFlow", page_icon="🤖")
st.title("🤖 AgentFlow")
st.caption("Supervisor + agentes especialistas com LangGraph e Gemini")

if "historico" not in st.session_state:
    st.session_state.historico = []
    st.session_state.total_entrada = 0
    st.session_state.total_saida = 0
    st.session_state.ultima = 0
    st.session_state.respostas_do_cache = 0

# Mostra a conversa até agora (com a legenda de cada resposta)
for msg in st.session_state.historico:
    with st.chat_message(msg["papel"]):
        st.markdown(msg["texto"])
        if msg["legenda"]:
            st.caption(msg["legenda"])

pergunta = st.chat_input("Pergunte algo (ex.: qual o produto mais caro de vendas.csv?)")

if pergunta:
    with st.chat_message("user"):
        st.markdown(pergunta)

    # Só as últimas mensagens vão para o modelo (economiza tokens)
    anteriores = [(m["papel"], m["texto"]) for m in st.session_state.historico]
    mensagens = (anteriores + [("user", pergunta)])[-JANELA:]

    inicio = time.perf_counter()
    entrada = saida = 0
    legenda = ""
    agente = ""
    do_cache = False
    erro = False

    with st.chat_message("assistant"):
        guardada = buscar(mensagens)

        if guardada:
            # Cache: mesma pergunta, mesmo contexto -> zero tokens
            resposta = guardada["resposta"]
            agente = guardada["agente"]
            do_cache = True
            legenda = (
                f"Agente que respondeu: {agente} · "
                "resposta do cache: 0 tokens"
            )
            st.session_state.respostas_do_cache += 1
        else:
            with st.spinner("Pensando..."):
                try:
                    resultado = grafo.invoke({"messages": mensagens})
                    resposta = resultado["messages"][-1].text
                    agente = resultado.get("proximo", "")
                    entrada = resultado.get("tokens_entrada", 0)
                    saida = resultado.get("tokens_saida", 0)
                    legenda = (
                        f"Agente que respondeu: {agente} · "
                        f"tokens: {entrada} entrada + {saida} saída"
                    )
                    salvar(mensagens, resposta, agente)
                except Exception:
                    resposta = (
                        "Não consegui falar com o modelo agora. "
                        "Pode ser o limite do plano gratuito: aguarde um minuto e tente de novo."
                    )
                    erro = True

        st.markdown(resposta)
        if legenda:
            st.caption(legenda)

    # Observabilidade: registra a chamada no log
    registrar(
        pergunta, agente, entrada, saida,
        time.perf_counter() - inicio, do_cache, erro,
    )

    st.session_state.total_entrada += entrada
    st.session_state.total_saida += saida
    st.session_state.ultima = entrada + saida
    st.session_state.historico.append({"papel": "user", "texto": pergunta, "legenda": ""})
    st.session_state.historico.append(
        {"papel": "assistant", "texto": resposta, "legenda": legenda}
    )

# Dados de observabilidade (lidos do arquivo de log)
eventos = ler()
numeros = resumo(eventos)

# Painel lateral
with st.sidebar:
    st.header("📊 Uso de tokens")
    st.metric("Última pergunta", st.session_state.ultima)
    st.metric(
        "Total da sessão",
        st.session_state.total_entrada + st.session_state.total_saida,
    )
    st.caption(
        f"Entrada: {st.session_state.total_entrada} · "
        f"Saída: {st.session_state.total_saida}"
    )
    st.metric("Respostas vindas do cache", st.session_state.respostas_do_cache)
    st.caption(f"Janela de contexto: últimas {JANELA} mensagens")

    st.divider()
    st.header("🔎 Observabilidade")
    st.caption(
        f"Chamadas registradas: {numeros['total']} · "
        f"cache: {numeros['cache']} · erros: {numeros['erros']}"
    )
    st.caption(f"Tempo médio das chamadas ao modelo: {numeros['tempo_medio']} s")
    st.caption(f"Tokens somados no log: {numeros['tokens']}")

# Tabela com as últimas chamadas
with st.expander("🔎 Registro das últimas chamadas"):
    if eventos:
        st.dataframe(list(reversed(eventos[-10:])))
    else:
        st.caption("Nenhuma chamada registrada ainda.")