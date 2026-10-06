import time
from typing import Literal

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel

# Reaproveita as ferramentas que você já criou
from agente_planilha import ler_planilha, somar_coluna
from agente_ferramentas import somar, data_e_hora_atual

load_dotenv()

MODELO = "gemini-3.1-flash-lite"


# ---------- Estado e decisão do supervisor ----------
class Estado(MessagesState):
    proximo: str


class Decisao(BaseModel):
    agente: Literal["planilha", "calculo", "geral"]


INSTRUCAO_SUPERVISOR = (
    "Você é um supervisor. Leia a pergunta do usuário e escolha o agente certo:\n"
    "- planilha: perguntas sobre arquivos CSV ou planilhas (vendas.csv)\n"
    "- calculo: somas de números, data ou hora atual\n"
    "- geral: qualquer outra pergunta"
)


# ---------- Fábrica de agentes especialistas ----------
def criar_agente(ferramentas, instrucao):
    llm = ChatGoogleGenerativeAI(model=MODELO)
    if ferramentas:
        llm = llm.bind_tools(ferramentas)

    def no_agente(state: MessagesState):
        mensagens = [SystemMessage(content=instrucao), *state["messages"]]
        return {"messages": [llm.invoke(mensagens)]}

    g = StateGraph(MessagesState)
    g.add_node("agente", no_agente)
    g.add_edge(START, "agente")

    if ferramentas:
        g.add_node("tools", ToolNode(ferramentas))
        g.add_conditional_edges("agente", tools_condition)
        g.add_edge("tools", "agente")
    else:
        g.add_edge("agente", END)

    return g.compile()


agente_planilha = criar_agente(
    [ler_planilha, somar_coluna],
    "Você é o especialista em planilhas. Use as ferramentas para ler e somar dados.",
)
agente_calculo = criar_agente(
    [somar, data_e_hora_atual],
    "Você é o especialista em cálculos e data/hora. Use as ferramentas.",
)
agente_geral = criar_agente(
    [],
    "Você é um assistente geral. Responda de forma curta e em português.",
)


# ---------- Nós do grafo principal ----------
llm_supervisor = ChatGoogleGenerativeAI(model=MODELO).with_structured_output(Decisao)


def supervisor(state: Estado):
    decisao = llm_supervisor.invoke(
        [SystemMessage(content=INSTRUCAO_SUPERVISOR), *state["messages"]]
    )
    escolha = decisao.agente if decisao else "geral"
    print(f"  [supervisor] escolheu o agente: {escolha}")
    return {"proximo": escolha}


def chamar(subgrafo):
    def no(state: Estado):
        resultado = subgrafo.invoke({"messages": state["messages"]})
        novas = resultado["messages"][len(state["messages"]):]
        for msg in novas:
            for chamada in getattr(msg, "tool_calls", None) or []:
                print(f"  -> Ferramenta usada: {chamada['name']} {chamada['args']}")
        return {"messages": [resultado["messages"][-1]]}

    return no


workflow = StateGraph(Estado)
workflow.add_node("supervisor", supervisor)
workflow.add_node("planilha", chamar(agente_planilha))
workflow.add_node("calculo", chamar(agente_calculo))
workflow.add_node("geral", chamar(agente_geral))

workflow.add_edge(START, "supervisor")
workflow.add_conditional_edges(
    "supervisor",
    lambda state: state["proximo"],
    {"planilha": "planilha", "calculo": "calculo", "geral": "geral"},
)
workflow.add_edge("planilha", END)
workflow.add_edge("calculo", END)
workflow.add_edge("geral", END)

grafo = workflow.compile()


if __name__ == "__main__":
    perguntas = [
        "Qual o total da coluna quantidade em vendas.csv?",
        "Que dia e hora são agora?",
    ]

    for i, pergunta in enumerate(perguntas):
        if i > 0:
            print("\n(aguardando 30s para respeitar o limite do plano gratuito...)")
            time.sleep(30)

        print(f"\nPergunta: {pergunta}")
        resultado = grafo.invoke({"messages": [("user", pergunta)]})
        print(f"Resposta: {resultado['messages'][-1].text}")