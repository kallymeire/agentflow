import streamlit as st

from agente_multiagente import grafo

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

    entrada = saida = 0
    legenda = ""

    with st.chat_message("assistant"):
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
            except Exception:
                resposta = (
                    "Não consegui falar com o modelo agora. "
                    "Pode ser o limite do plano gratuito: aguarde um minuto e tente de novo."
                )

        st.markdown(resposta)
        if legenda:
            st.caption(legenda)

    st.session_state.total_entrada += entrada
    st.session_state.total_saida += saida
    st.session_state.ultima = entrada + saida
    st.session_state.historico.append({"papel": "user", "texto": pergunta, "legenda": ""})
    st.session_state.historico.append(
        {"papel": "assistant", "texto": resposta, "legenda": legenda}
    )

# Painel lateral com o uso de tokens
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
    st.caption(f"Janela de contexto: últimas {JANELA} mensagens")