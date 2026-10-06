import streamlit as st

from agente_multiagente import grafo

st.set_page_config(page_title="AgentFlow", page_icon="🤖")
st.title("🤖 AgentFlow")
st.caption("Supervisor + agentes especialistas com LangGraph e Gemini")

if "historico" not in st.session_state:
    st.session_state.historico = []

# Mostra a conversa até agora
for papel, texto in st.session_state.historico:
    with st.chat_message(papel):
        st.markdown(texto)

pergunta = st.chat_input("Pergunte algo (ex.: qual o produto mais caro de vendas.csv?)")

if pergunta:
    with st.chat_message("user"):
        st.markdown(pergunta)

    mensagens = st.session_state.historico + [("user", pergunta)]

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                resultado = grafo.invoke({"messages": mensagens})
                resposta = resultado["messages"][-1].text
                agente = resultado.get("proximo", "")
            except Exception:
                resposta = (
                    "Não consegui falar com o modelo agora. "
                    "Pode ser o limite do plano gratuito: aguarde um minuto e tente de novo."
                )
                agente = ""

        st.markdown(resposta)
        if agente:
            st.caption(f"Agente que respondeu: {agente}")

    st.session_state.historico.append(("user", pergunta))
    st.session_state.historico.append(("assistant", resposta))