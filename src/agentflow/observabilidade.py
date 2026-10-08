import json
from datetime import datetime
from pathlib import Path

ARQUIVO = Path(__file__).resolve().parents[2] / "logs" / "chamadas.jsonl"


def registrar(pergunta, agente, entrada, saida, tempo, cache, erro=False):
    """Guarda uma linha no log para cada pergunta respondida."""
    ARQUIVO.parent.mkdir(exist_ok=True)
    evento = {
        "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pergunta": pergunta,
        "agente": agente,
        "tokens_entrada": entrada,
        "tokens_saida": saida,
        "tempo_s": round(tempo, 2),
        "cache": cache,
        "erro": erro,
    }
    with open(ARQUIVO, "a", encoding="utf-8") as f:
        f.write(json.dumps(evento, ensure_ascii=False) + "\n")


def ler():
    """Lê todas as chamadas registradas."""
    if not ARQUIVO.exists():
        return []
    eventos = []
    for linha in ARQUIVO.read_text(encoding="utf-8").splitlines():
        if linha.strip():
            eventos.append(json.loads(linha))
    return eventos


def resumo(eventos):
    """Números gerais: total, cache, erros, tempo médio e tokens."""
    if not eventos:
        return {"total": 0, "cache": 0, "erros": 0, "tempo_medio": 0.0, "tokens": 0}

    ao_modelo = [e for e in eventos if not e["cache"] and not e["erro"]]
    tempo_medio = (
        round(sum(e["tempo_s"] for e in ao_modelo) / len(ao_modelo), 2)
        if ao_modelo
        else 0.0
    )
    return {
        "total": len(eventos),
        "cache": sum(1 for e in eventos if e["cache"]),
        "erros": sum(1 for e in eventos if e["erro"]),
        "tempo_medio": tempo_medio,
        "tokens": sum(e["tokens_entrada"] + e["tokens_saida"] for e in eventos),
    }