import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict
from langgraph.graph import StateGraph, END

# 1. Carregar variáveis de ambiente (lê o arquivo .env)
load_dotenv()

# 2. Definir o Estado do grafo
class Estado(TypedDict):
    pergunta: str
    resposta: str

# 3. Inicializar o modelo
llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

# 4. Nó que processa a pergunta
def no_gerar_resposta(state: Estado):
    print("--- EXECUTANDO O NÓ DO AGENTE ---")
    pergunta = state["pergunta"]
    resultado = llm.invoke(pergunta)
    return {"resposta": resultado.text}

# 5. Construir o grafo
workflow = StateGraph(Estado)
workflow.add_node("gerador", no_gerar_resposta)
workflow.set_entry_point("gerador")
workflow.add_edge("gerador", END)

grafo = workflow.compile()

# 6. Executar
if __name__ == "__main__":
    estado_inicial = {
        "pergunta": "Explique o conceito de Agentes de IA de forma simples e em português."
    }
    resultado_final = grafo.invoke(estado_inicial)

    print("\n--- RESPOSTA FINAL DO GRAFO ---")
    print(resultado_final["resposta"])