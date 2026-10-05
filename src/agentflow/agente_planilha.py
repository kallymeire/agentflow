import csv
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv()

# Para trocar de modelo, mude só esta linha
MODELO = "gemini-3.1-flash-lite"

# Pasta "dados" na raiz do projeto
PASTA_DADOS = Path(__file__).resolve().parents[2] / "dados"


def _caminho(nome_arquivo: str) -> Path:
    # .name garante que o agente só acesse arquivos dentro da pasta dados
    return PASTA_DADOS / Path(nome_arquivo).name


@tool
def ler_planilha(nome_arquivo: str) -> str:
    """Lê uma planilha CSV da pasta dados e devolve o conteúdo em texto."""
    caminho = _caminho(nome_arquivo)
    if not caminho.exists():
        return f"Arquivo '{nome_arquivo}' não encontrado."
    return caminho.read_text(encoding="utf-8")


@tool
def somar_coluna(nome_arquivo: str, coluna: str) -> str:
    """Soma os valores numéricos de uma coluna de uma planilha CSV da pasta dados."""
    caminho = _caminho(nome_arquivo)
    if not caminho.exists():
        return f"Arquivo '{nome_arquivo}' não encontrado."
    total = 0.0
    with open(caminho, newline="", encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            if coluna not in linha:
                return f"Coluna '{coluna}' não existe."
            total += float(linha[coluna])
    return str(total)


ferramentas = [ler_planilha, somar_coluna]

llm = ChatGoogleGenerativeAI(model=MODELO).bind_tools(ferramentas)


def agente(state: MessagesState):
    return {"messages": [llm.invoke(state["messages"])]}


workflow = StateGraph(MessagesState)
workflow.add_node("agente", agente)
workflow.add_node("tools", ToolNode(ferramentas))
workflow.add_edge(START, "agente")
workflow.add_conditional_edges("agente", tools_condition)
workflow.add_edge("tools", "agente")

grafo = workflow.compile()

if __name__ == "__main__":
    perguntas = [
        "Quais produtos existem na planilha vendas.csv?",
        "Qual o total da coluna quantidade em vendas.csv?",
        "Qual é o produto mais caro de vendas.csv?",
    ]

    for i, pergunta in enumerate(perguntas):
        if i > 0:
            print("\n(aguardando 30s para respeitar o limite do plano gratuito...)")
            time.sleep(30)

        print(f"\nPergunta: {pergunta}")
        resultado = grafo.invoke({"messages": [("user", pergunta)]})

        for msg in resultado["messages"]:
            for chamada in getattr(msg, "tool_calls", None) or []:
                print(f"  -> Ferramenta usada: {chamada['name']} {chamada['args']}")

        print(f"Resposta: {resultado['messages'][-1].text}")