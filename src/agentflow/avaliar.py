import time
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from agente_multiagente import grafo, MODELO


# ---------- Juiz: confere a resposta por significado ----------
class Veredito(BaseModel):
    correta: bool
    motivo: str


_juiz = ChatGoogleGenerativeAI(model=MODELO, temperature=0).with_structured_output(
    Veredito
)


def julgar(pergunta, esperado, resposta):
    """Pergunta ao modelo se a resposta diz o mesmo que a esperada."""
    try:
        return _juiz.invoke(
            "Você é um avaliador rigoroso.\n"
            f"Pergunta: {pergunta}\n"
            f"Resposta esperada: {esperado}\n"
            f"Resposta dada: {resposta}\n"
            "A resposta dada tem o mesmo significado da esperada e não inventa "
            "nada? Preencha 'correta' e explique em uma frase em 'motivo'."
        )
    except Exception:
        return None


# Cada caso: pergunta, agente esperado, termos que a resposta deve conter
# e a resposta esperada (usada pelo juiz)
CASOS = [
    {
        "pergunta": "Qual o prazo para devolver um produto?",
        "agente": "loja",
        "termos": ["7 dias"],
        "esperado": "O prazo para devolver um produto é de 7 dias.",
    },
    {
        "pergunta": "Quanto tempo de garantia tem o monitor?",
        "agente": "loja",
        "termos": ["24 meses"],
        "esperado": "A garantia do monitor é de 24 meses.",
    },
    {
        "pergunta": "A partir de quanto o frete é grátis?",
        "agente": "loja",
        "termos": ["300"],
        "esperado": "O frete é grátis em compras acima de R$ 300,00.",
    },
    {
        "pergunta": "Qual o total da coluna quantidade em vendas.csv?",
        "agente": "planilha",
        "termos": ["52"],
        "esperado": "O total da coluna quantidade é 52.",
    },
    {
        "pergunta": "Quanto é 12,5 + 30?",
        "agente": "calculo",
        "termos": ["42,5", "42.5"],
        "esperado": "12,5 + 30 = 42,5.",
    },
    {
        # Teste anti-invenção: a informação NÃO está nos documentos
        "pergunta": "Vocês vendem geladeira?",
        "agente": "loja",
        "termos": ["não encontr"],
        "esperado": "Não há informação sobre a venda de geladeira nos documentos.",
    },
    # ----- Casos novos -----
    {
        # Mesma informação, perguntada com outras palavras
        "pergunta": "Em quantos dias posso devolver uma compra?",
        "agente": "loja",
        "termos": ["7 dias"],
        "esperado": "O prazo para devolver é de 7 dias.",
    },
    {
        # Erros de digitação
        "pergunta": "Qanto tmpo de garantia tem o monitor?",
        "agente": "loja",
        "termos": ["24 meses"],
        "esperado": "A garantia do monitor é de 24 meses.",
    },
    {
        "pergunta": "Qual é o produto mais caro de vendas.csv?",
        "agente": "planilha",
        "termos": ["Monitor"],
        "esperado": "O produto mais caro é o Monitor, com preço de 899,00.",
    },
    {
        "pergunta": "Quanto é 100 + 250,5?",
        "agente": "calculo",
        "termos": ["350,5", "350.5"],
        "esperado": "100 + 250,5 = 350,5.",
    },
    {
        # Teste anti-invenção (confira que micro-ondas NÃO aparece nos documentos)
        "pergunta": "Vocês vendem micro-ondas?",
        "agente": "loja",
        "termos": ["não encontr"],
        "esperado": "Não há informação sobre a venda de micro-ondas nos documentos.",
    },
    {
        # Pergunta geral, sem relação com a loja
        "pergunta": "Quem descobriu o Brasil?",
        "agente": "geral",
        "termos": ["Cabral"],
        "esperado": "Pedro Álvares Cabral, em 1500.",
    },
    {
        # A checagem por palavras-chave aceita só uma das duas informações;
        # o juiz percebe quando falta uma delas
        "pergunta": "Qual a garantia do monitor e o prazo de devolução?",
        "agente": "loja",
        "termos": ["24 meses", "7 dias"],
        "esperado": "A garantia do monitor é de 24 meses e a devolução é em até 7 dias.",
    },
]

PAUSA = 30  # segundos entre perguntas (limite do plano gratuito)
PAUSA_JUIZ = 5  # respiro antes da chamada do juiz
RELATORIO = Path(__file__).resolve().parents[2] / "docs" / "avaliacao.md"


def _limpar(texto):
    """Deixa o texto em uma linha só e sem o caractere que quebra a tabela."""
    return " ".join(str(texto).replace("|", "/").split())


def avaliar():
    linhas = []
    motivos = []
    divergencias = []
    passaram = 0
    erros = 0
    acertos_palavras = 0
    acertos_juiz = 0
    avaliados_juiz = 0
    total_entrada = total_saida = 0

    for i, caso in enumerate(CASOS, start=1):
        if i > 1:
            time.sleep(PAUSA)

        print(f"\n[{i}/{len(CASOS)}] {caso['pergunta']}")

        try:
            resultado = grafo.invoke({"messages": [("user", caso["pergunta"])]})
        except Exception as e:
            erros += 1
            print(f"  ERRO ao chamar o modelo ({type(e).__name__})")
            linhas.append(
                f"| {i} | {caso['pergunta']} | {caso['agente']} | - | - | - | ERRO | - |"
            )
            continue

        resposta = resultado["messages"][-1].text
        agente = resultado.get("proximo", "")
        entrada = resultado.get("tokens_entrada", 0)
        saida = resultado.get("tokens_saida", 0)

        agente_ok = agente == caso["agente"]
        palavras_ok = any(t.lower() in resposta.lower() for t in caso["termos"])

        # Juiz: confere por significado
        time.sleep(PAUSA_JUIZ)
        veredito = julgar(caso["pergunta"], caso["esperado"], resposta)
        juiz_ok = veredito.correta if veredito else None
        motivo = veredito.motivo if veredito else "sem avaliação do juiz"

        passou = agente_ok and palavras_ok and (juiz_ok is not False)

        passaram += passou
        total_entrada += entrada
        total_saida += saida
        if agente_ok and palavras_ok:
            acertos_palavras += 1
        if juiz_ok is not None:
            avaliados_juiz += 1
            acertos_juiz += juiz_ok
            if juiz_ok != palavras_ok:
                divergencias.append(
                    f"- **Caso {i}** ({caso['pergunta']}): palavras-chave = "
                    f"{'ok' if palavras_ok else 'errado'}, juiz = "
                    f"{'ok' if juiz_ok else 'errado'}. Motivo do juiz: {_limpar(motivo)}"
                )
                print(
                    f"  DIVERGÊNCIA: palavras-chave={'ok' if palavras_ok else 'errado'}"
                    f", juiz={'ok' if juiz_ok else 'errado'}"
                )

        juiz_texto = "n/d" if juiz_ok is None else ("sim" if juiz_ok else "não")
        print(f"  agente: {agente} (esperado: {caso['agente']}) -> {'ok' if agente_ok else 'errado'}")
        print(f"  palavras-chave -> {'ok' if palavras_ok else 'errado'}")
        print(f"  juiz -> {juiz_texto} ({_limpar(motivo)})")
        print(f"  RESULTADO: {'PASSOU' if passou else 'FALHOU'}  ({entrada + saida} tokens)")

        linhas.append(
            f"| {i} | {caso['pergunta']} | {caso['agente']} | {agente} | "
            f"{'sim' if palavras_ok else 'não'} | {juiz_texto} | "
            f"{'✅ passou' if passou else '❌ falhou'} | {entrada + saida} |"
        )
        motivos.append(f"- **Caso {i}**: {_limpar(motivo)}")

    print("\n" + "=" * 50)
    print(f"ACERTOS: {passaram} de {len(CASOS)}  (erros de chamada: {erros})")
    print(f"Agente + palavras-chave: {acertos_palavras} de {len(CASOS)}")
    print(f"Juiz: {acertos_juiz} de {avaliados_juiz} avaliados")
    print(f"Divergências entre os dois métodos: {len(divergencias)}")
    print(f"TOKENS TOTAIS: {total_entrada} entrada + {total_saida} saída")

    # Relatório em Markdown, para mostrar no GitHub
    texto = (
        "# Avaliação automática\n\n"
        f"**Resultado: {passaram} de {len(CASOS)} perguntas corretas** "
        f"(erros de chamada: {erros}).\n\n"
        f"- Agente certo e palavras-chave: {acertos_palavras} de {len(CASOS)}\n"
        f"- Juiz (por significado): {acertos_juiz} de {avaliados_juiz} avaliados\n"
        f"- Divergências entre os dois métodos: {len(divergencias)}\n\n"
        "| # | Pergunta | Agente esperado | Agente escolhido | Palavras-chave | Juiz | Resultado | Tokens |\n"
        "|---|---|---|---|---|---|---|---|\n"
        + "\n".join(linhas)
        + f"\n\nTokens totais: {total_entrada} de entrada + {total_saida} de saída.\n"
    )
    if divergencias:
        texto += "\n## Divergências entre palavras-chave e juiz\n\n" + "\n".join(divergencias) + "\n"
    if motivos:
        texto += "\n## Motivos do juiz\n\n" + "\n".join(motivos) + "\n"

    RELATORIO.parent.mkdir(exist_ok=True)
    RELATORIO.write_text(texto, encoding="utf-8")
    print(f"Relatório salvo em: {RELATORIO}")


if __name__ == "__main__":
    avaliar()