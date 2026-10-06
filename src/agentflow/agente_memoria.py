import time

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition

# Reaproveita as ferramentas do agente de planilha
from agente_planilha import ferramentas

load_dotenv()

MODELO = "gemini-3.1-flash-lite"

llm = ChatGoogleGenerativeAI(model=MODELO).bind_tools(ferramentas)


def agente(state: MessagesState):
    return {"messages": [llm.invoke(state["messages"])]}


workflow = StateGraph(MessagesState)
workflow.add_node("agente", agente)
workflow.add_node("tools", ToolNode(ferramentas))
workflow.add_edge(START, "agente")
workflow.add_conditional_edges("agente", tools_condition)
workflow.add_edge("tools", "agente")

# A memória: guarda a conversa de cada "thread_id"
memoria = MemorySaver()
grafo = workflow.compile(checkpointer=memoria)

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "conversa-1"}}

    perguntas = [
        "Qual é o produto mais caro de vendas.csv?",
        "E qual é o mais barato?",
    ]

    for i, pergunta in enumerate(perguntas):
        if i > 0:
            print("\n(aguardando 30s para respeitar o limite do plano gratuito...)")
            time.sleep(30)

        print(f"\nPergunta: {pergunta}")
        resultado = grafo.invoke({"messages": [("user", pergunta)]}, config)

        mensagens = resultado["messages"]
        ultima = max(i for i, m in enumerate(mensagens) if m.type == "human")
        for msg in mensagens[ultima + 1:]:
            for chamada in getattr(msg, "tool_calls", None) or []:
                print(f"  -> Ferramenta usada: {chamada['name']} {chamada['args']}")

        print(f"Resposta: {mensagens[-1].text}")