from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class Estado(TypedDict):
    nome: str
    mensagem: str


def saudar(state: Estado):
    return {"mensagem": f"Olá, {state['nome']}!"}


def animar(state: Estado):
    return {"mensagem": state["mensagem"] + " Bem-vinda ao AgentFlow!"}


builder = StateGraph(Estado)
builder.add_node("saudar", saudar)
builder.add_node("animar", animar)

builder.add_edge(START, "saudar")
builder.add_edge("saudar", "animar")
builder.add_edge("animar", END)

graph = builder.compile()

resultado = graph.invoke({"nome": "Kallymeire"})
print(resultado["mensagem"])