import hashlib
import json
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

RAIZ = Path(__file__).resolve().parents[2]
ARQUIVO = RAIZ / "cache" / "respostas.json"
ARQUIVO_SEMANTICO = RAIZ / "cache" / "semantico.json"
PASTA_DOCS = RAIZ / "base_conhecimento"

# Similaridade mínima para reaproveitar uma resposta.
# Calibre rodando calibrar_cache.py e ajuste este valor.
LIMITE = 0.95

_embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")


def _normalizar(texto: str) -> str:
    return " ".join(texto.lower().split())


def _hash(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _versao_docs() -> str:
    """Muda quando um documento da base muda: o cache se invalida sozinho."""
    base = "".join(
        f"{a.name}{a.stat().st_mtime}" for a in sorted(PASTA_DOCS.glob("*.txt"))
    )
    return _hash(base)


def _contexto(mensagens) -> str:
    """Mensagens que vieram antes da pergunta atual (a última da lista)."""
    return "|".join(f"{papel}:{_normalizar(texto)}" for papel, texto in mensagens[:-1])


def _chave(mensagens) -> str:
    """A chave considera a versão dos documentos, a pergunta e o contexto."""
    base = "|".join(f"{papel}:{_normalizar(texto)}" for papel, texto in mensagens)
    return _hash(_versao_docs() + "|" + base)


def _ler(arquivo, padrao):
    if arquivo.exists():
        return json.loads(arquivo.read_text(encoding="utf-8"))
    return padrao


def _gravar(arquivo, dados, indent=None) -> None:
    arquivo.parent.mkdir(exist_ok=True)
    arquivo.write_text(
        json.dumps(dados, ensure_ascii=False, indent=indent), encoding="utf-8"
    )


def _buscar_semantico(mensagens):
    ctx, versao = _hash(_contexto(mensagens)), _versao_docs()
    candidatos = [
        e for e in _ler(ARQUIVO_SEMANTICO, [])
        if e["ctx"] == ctx and e["versao"] == versao
    ]
    if not candidatos:
        return None  # nada para comparar: nem gasta a chamada de embedding

    try:
        q = np.array(_embeddings.embed_query(mensagens[-1][1]))
    except Exception:
        return None  # sem embedding, segue para o modelo normalmente

    melhor, nota = None, 0.0
    for e in candidatos:
        v = np.array(e["vetor"])
        s = float(q @ v / (np.linalg.norm(q) * np.linalg.norm(v)))
        if s > nota:
            melhor, nota = e, s

    if melhor and nota >= LIMITE:
        return {
            "resposta": melhor["resposta"],
            "agente": melhor["agente"],
            "tipo": "semântico",
            "similaridade": round(nota, 3),
        }
    return None


def buscar(mensagens):
    """Devolve {'resposta', 'agente', 'tipo', ...} se houver cache, senão None."""
    exato = _ler(ARQUIVO, {}).get(_chave(mensagens))
    if exato:
        return {**exato, "tipo": "exato"}
    return _buscar_semantico(mensagens)


def salvar(mensagens, resposta: str, agente: str) -> None:
    dados = _ler(ARQUIVO, {})
    dados[_chave(mensagens)] = {"resposta": resposta, "agente": agente}
    _gravar(ARQUIVO, dados, indent=2)

    # Cache semântico: se o embedding falhar, a resposta já está no cache exato
    try:
        vetor = _embeddings.embed_query(mensagens[-1][1])
    except Exception:
        return
    semantico = _ler(ARQUIVO_SEMANTICO, [])
    semantico.append({
        "ctx": _hash(_contexto(mensagens)),
        "versao": _versao_docs(),
        "vetor": vetor,
        "resposta": resposta,
        "agente": agente,
    })
    _gravar(ARQUIVO_SEMANTICO, semantico)