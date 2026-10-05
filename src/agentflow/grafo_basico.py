import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# 1. Carregar variáveis do ficheiro .env
load_dotenv()

# 2. Inicializar o modelo ChatGoogleGenerativeAI com o Gemini atualizado
llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash")

# 3. Definir a mensagem a enviar
mensagem = "Explica o conceito de Agentes de IA de forma simples e em português."

# 4. Invocar o modelo e obter a resposta
resultado = llm.invoke(mensagem)

# 5. Imprimir a resposta
print("--- RESPOSTA DO GEMINI ---")
print(resultado.content)