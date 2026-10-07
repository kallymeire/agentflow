import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv()

MODELO = "gemini-3.1-flash-lite"
PASTA = Path(__file__).resolve().parents[2] / "base_conhecimento"


# ---------- 1. Indexação: documentos -> pedaços -> embeddings ----------
def construir_indice():
    divisor = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    textos, metadados = [], []

    for arquivo in PASTA.glob("*.txt"):
        conteudo = arquivo.read_text(encoding="utf-8")
        for trecho in divisor.split_text(conteudo):
            textos.append(trecho)
            metadados.append({"fonte": arquivo.name})

    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
    return InMemoryVectorStore.from_texts(textos, embeddings, metadatas=metadados)


indice = construir_indice()


# ---------- 2. Ferramenta de busca ----------
@tool
def buscar_documentos(pergunta: str) -> str:
    """Busca trechos relevantes na base de conhecimento da loja
    (troca, devolução, garantia, frete, pagamento e atendimento)."""
    resultados = indice.similarity_search(pergunta, k=3)
    if not resultados:
        return "Nenhum trecho encontrado."
    return "\n\n".join(
        f"[fonte: {doc.metadata['fonte']}]\n{doc.page_content}" for doc in resultados
    )


ferramentas = [buscar_documentos]

INSTRUCAO = (
    "Você é o assistente da loja Techponto. Para responder, use SEMPRE a ferramenta "
    "buscar_documentos. Responda apenas com base nos trechos encontrados e cite a "
    "fonte (nome do arquivo). Se a informação não estiver nos documentos, diga que "
    "não encontrou, sem inventar."
)

llm = ChatGoogleGenerativeAI(model=MODELO).bind_tools(ferramentas)


# ---------- 3. Agente ----------
def agente(state: MessagesState):
    mensagens = [SystemMessage(content=INSTRUCAO), *state["messages"]]
    return {"messages": [llm.invoke(mensagens)]}


workflow = StateGraph(MessagesState)
workflow.add_node("agente", agente)
workflow.add_node("tools", ToolNode(ferramentas))
workflow.add_edge(START, "agente")
workflow.add_conditional_edges("agente", tools_condition)
workflow.add_edge("tools", "agente")

grafo = workflow.compile()


if __name__ == "__main__":
    perguntas = [
        "Qual o prazo para devolver um produto?",
        "Quanto tempo de garantia tem o monitor?",
        "Vocês vendem geladeira?",
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