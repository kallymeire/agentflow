import os
import time

import streamlit as st

from agente_multiagente import grafo
from cache_respostas import buscar, salvar
from observabilidade import ler, registrar, resumo

# Janela deslizante: o modelo recebe só as últimas mensagens da conversa
JANELA = 5

# Modo público (demonstração online): ative com AGENTFLOW_PUBLICO=1 nos secrets.
# Nele, o uso do modelo é limitado e o registro de perguntas de outros
# visitantes fica escondido.
MODO_PUBLICO = os.getenv("AGENTFLOW_PUBLICO") == "1"
LIMITE_SESSAO = int(os.getenv("AGENTFLOW_LIMITE_SESSAO", "10"))
LIMITE_GLOBAL = int(os.getenv("AGENTFLOW_LIMITE_GLOBAL", "300"))


@st.cache_resource
def _contador_global():
    """Conta as chamadas ao modelo de todos os visitantes (enquanto o app roda)."""
    return {"chamadas": 0}


st.set_page_config(page_title="AgentFlow", page_icon="🤖")
st.title("🤖 AgentFlow")
st.caption("Supervisor + agentes especialistas com LangGraph e Gemini")

if "historico" not in st.session_state:
    st.session_state.historico = []
    st.session_state.total_entrada = 0
    st.session_state.total_saida = 0
    st.session_state.ultima = 0
    st.session_state.respostas_do_cache = 0
    st.session_state.chamadas_modelo = 0

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
    tipo_cache = ""
    erro = False

    with st.chat_message("assistant"):
        guardada = buscar(mensagens)
        contador = _contador_global()

        if guardada:
            # Cache: mesma pergunta (ou parecida), mesmo contexto -> zero tokens de chat
            resposta = guardada["resposta"]
            agente = guardada["agente"]
            do_cache = True
            tipo_cache = guardada["tipo"]
            if tipo_cache == "exato":
                detalhe = "cache exato"
            else:
                detalhe = f"cache semântico (similaridade {guardada['similaridade']})"
            legenda = (
                f"Agente que respondeu: {agente} · "
                f"resposta do {detalhe}: 0 tokens de chat"
            )
            st.session_state.respostas_do_cache += 1
        elif MODO_PUBLICO and st.session_state.chamadas_modelo >= LIMITE_SESSAO:
            resposta = (
                f"Esta demonstração permite {LIMITE_SESSAO} perguntas ao modelo por "
                "sessão, por causa da cota gratuita. Perguntas já respondidas "
                "continuam saindo do cache."
            )
        elif MODO_PUBLICO and contador["chamadas"] >= LIMITE_GLOBAL:
            resposta = (
                "A demonstração atingiu o limite de uso por enquanto. "
                "Tente de novo mais tarde."
            )
        else:
            st.session_state.chamadas_modelo += 1
            contador["chamadas"] += 1
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
        time.perf_counter() - inicio, do_cache, erro, tipo_cache,
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
    if MODO_PUBLICO:
        restantes = max(LIMITE_SESSAO - st.session_state.chamadas_modelo, 0)
        st.caption(f"Demonstração: {restantes} perguntas ao modelo restantes nesta sessão")

    st.divider()
    st.header("🔎 Observabilidade")
    st.caption(
        f"Chamadas registradas: {numeros['total']} · "
        f"cache: {numeros['cache']} (semântico: {numeros['cache_semantico']}) · "
        f"erros: {numeros['erros']}"
    )
    st.caption(f"Tempo médio das chamadas ao modelo: {numeros['tempo_medio']} s")
    st.caption(f"Tokens somados no log: {numeros['tokens']}")

# Tabela com as últimas chamadas (escondida no modo público: tem perguntas de outros visitantes)
if not MODO_PUBLICO:
    with st.expander("🔎 Registro das últimas chamadas"):
        if eventos:
            st.dataframe(list(reversed(eventos[-10:])))
        else:
            st.caption("Nenhuma chamada registrada ainda.")