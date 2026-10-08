import hashlib
import json
from pathlib import Path

ARQUIVO = Path(__file__).resolve().parents[2] / "cache" / "respostas.json"


def _normalizar(texto: str) -> str:
    return " ".join(texto.lower().split())


def _chave(mensagens) -> str:
    """A chave considera a pergunta e o contexto que veio antes dela."""
    base = "|".join(f"{papel}:{_normalizar(texto)}" for papel, texto in mensagens)
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _carregar() -> dict:
    if ARQUIVO.exists():
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    return {}


def buscar(mensagens):
    """Devolve {'resposta': ..., 'agente': ...} se já existir, senão None."""
    return _carregar().get(_chave(mensagens))


def salvar(mensagens, resposta: str, agente: str) -> None:
    dados = _carregar()
    dados[_chave(mensagens)] = {"resposta": resposta, "agente": agente}
    ARQUIVO.parent.mkdir(exist_ok=True)
    ARQUIVO.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
    )