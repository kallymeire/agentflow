import numpy as np

from cache_respostas import _embeddings

# (pergunta A, pergunta B, devem ser tratadas como a mesma pergunta?)
PARES = [
    ("Quanto tempo de garantia tem o monitor?", "Qual o prazo de garantia do monitor?", True),
    ("Qual o prazo para devolver um produto?", "Em quantos dias posso devolver uma compra?", True),
    ("A partir de quanto o frete é grátis?", "Qual o valor mínimo para ter frete grátis?", True),
    ("Qual o total da coluna quantidade em vendas.csv?", "Quanto soma a coluna quantidade de vendas.csv?", True),
    ("Quanto tempo de garantia tem o monitor?", "Quanto tempo de garantia tem o mouse?", False),
    ("Vocês vendem geladeira?", "Vocês vendem micro-ondas?", False),
    ("A partir de quanto o frete é grátis?", "Qual o prazo para devolver um produto?", False),
    ("Qual o produto mais caro de vendas.csv?", "Qual o produto mais barato de vendas.csv?", False),
]

iguais, diferentes = [], []

for a, b, igual in PARES:
    va = np.array(_embeddings.embed_query(a))
    vb = np.array(_embeddings.embed_query(b))
    s = float(va @ vb / (np.linalg.norm(va) * np.linalg.norm(vb)))
    (iguais if igual else diferentes).append(s)
    print(f"{s:.3f}  {'IGUAL    ' if igual else 'DIFERENTE'}  {a}  |  {b}")

menor_igual = min(iguais)
maior_diferente = max(diferentes)
print(f"\nMenor nota entre os IGUAIS:      {menor_igual:.3f}")
print(f"Maior nota entre os DIFERENTES:  {maior_diferente:.3f}")

if menor_igual > maior_diferente:
    sugestao = (menor_igual + maior_diferente) / 2
    print(f"As faixas estão separadas. Sugestão de LIMITE: {sugestao:.2f}")
else:
    print(
        "As faixas se misturam: perguntas diferentes tiveram nota parecida com as iguais.\n"
        "Use um LIMITE alto (ex.: 0.95) e aceite reaproveitar menos respostas."
    )