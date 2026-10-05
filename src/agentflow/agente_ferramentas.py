from datetime import datetime
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv()


# 1. Ferramentas que o agente pode usar
@tool
def somar(a: float, b: float) -> float:
    """Soma dois números."""
    return a + b


@tool
def data_e_hora_atual() -> str:
    """Retorna a data e a hora atuais."""
    return datetime.now().strftime("%d/%m/%Y %H:%M")


ferramentas = [somar, data_e_hora_atual]

# 2. Modelo que sabe que as ferramentas existem
llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash").bind_tools(ferramentas)


# 3. Nó do agente: o modelo decide se responde ou usa uma ferramenta
def agente(state: MessagesState):
    return {"messages": [llm.invoke(state["messages"])]}


# 4. Grafo: agente -> (ferramenta?) -> agente -> fim
workflow = StateGraph(MessagesState)
workflow.add_node("agente", agente)
workflow.add_node("tools", ToolNode(ferramentas))
workflow.add_edge(START, "agente")
workflow.add_conditional_edges("agente", tools_condition)
workflow.add_edge("tools", "agente")

grafo = workflow.compile()

# 5. Testes
if __name__ == "__main__":
    perguntas = [
        "Quanto é 12,5 + 30?",
        "Que dia e hora são agora?",
        "Explique em uma frase o que é um agente de IA.",
    ]

    for pergunta in perguntas:
        print(f"\nPergunta: {pergunta}")
        resultado = grafo.invoke({"messages": [("user", pergunta)]})

        for msg in resultado["messages"]:
            for chamada in getattr(msg, "tool_calls", None) or []:
                print(f"  -> Ferramenta usada: {chamada['name']} {chamada['args']}")

        print(f"Resposta: {resultado['messages'][-1].text}")