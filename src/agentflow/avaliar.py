import time
from pathlib import Path

from agente_multiagente import grafo

# Cada caso: pergunta, agente esperado e termos que a resposta deve conter
CASOS = [
    {
        "pergunta": "Qual o prazo para devolver um produto?",
        "agente": "loja",
        "termos": ["7 dias"],
    },
    {
        "pergunta": "Quanto tempo de garantia tem o monitor?",
        "agente": "loja",
        "termos": ["24 meses"],
    },
    {
        "pergunta": "A partir de quanto o frete é grátis?",
        "agente": "loja",
        "termos": ["300"],
    },
    {
        "pergunta": "Qual o total da coluna quantidade em vendas.csv?",
        "agente": "planilha",
        "termos": ["52"],
    },
    {
        "pergunta": "Quanto é 12,5 + 30?",
        "agente": "calculo",
        "termos": ["42,5", "42.5"],
    },
    {
        # Teste anti-invenção: a informação NÃO está nos documentos
        "pergunta": "Vocês vendem geladeira?",
        "agente": "loja",
        "termos": ["não encontr"],
    },
]

PAUSA = 30  # segundos entre perguntas (limite do plano gratuito)
RELATORIO = Path(__file__).resolve().parents[2] / "docs" / "avaliacao.md"


def avaliar():
    linhas = []
    acertos = 0
    erros = 0
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
                f"| {i} | {caso['pergunta']} | {caso['agente']} | - | - | ERRO | - |"
            )
            continue

        resposta = resultado["messages"][-1].text
        agente = resultado.get("proximo", "")
        entrada = resultado.get("tokens_entrada", 0)
        saida = resultado.get("tokens_saida", 0)

        agente_ok = agente == caso["agente"]
        resposta_ok = any(t.lower() in resposta.lower() for t in caso["termos"])
        passou = agente_ok and resposta_ok

        acertos += passou
        total_entrada += entrada
        total_saida += saida

        print(f"  agente: {agente} (esperado: {caso['agente']}) -> {'ok' if agente_ok else 'errado'}")
        print(f"  resposta contém o esperado -> {'ok' if resposta_ok else 'errado'}")
        print(f"  RESULTADO: {'PASSOU' if passou else 'FALHOU'}  ({entrada + saida} tokens)")

        linhas.append(
            f"| {i} | {caso['pergunta']} | {caso['agente']} | {agente} | "
            f"{'sim' if resposta_ok else 'não'} | "
            f"{'✅ passou' if passou else '❌ falhou'} | {entrada + saida} |"
        )

    print("\n" + "=" * 50)
    print(f"ACERTOS: {acertos} de {len(CASOS)}  (erros de chamada: {erros})")
    print(f"TOKENS TOTAIS: {total_entrada} entrada + {total_saida} saída")

    # Relatório em Markdown, para mostrar no GitHub
    texto = (
        "# Avaliação automática\n\n"
        f"**Resultado: {acertos} de {len(CASOS)} perguntas corretas** "
        f"(erros de chamada: {erros}).\n\n"
        "| # | Pergunta | Agente esperado | Agente escolhido | Resposta correta | Resultado | Tokens |\n"
        "|---|---|---|---|---|---|---|\n"
        + "\n".join(linhas)
        + f"\n\nTokens totais: {total_entrada} de entrada + {total_saida} de saída.\n"
    )
    RELATORIO.write_text(texto, encoding="utf-8")
    print(f"Relatório salvo em: {RELATORIO}")


if __name__ == "__main__":
    avaliar()