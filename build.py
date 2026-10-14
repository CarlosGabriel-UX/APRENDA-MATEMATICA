#!/usr/bin/env python3
"""Gera as páginas do site a partir dos fragmentos em src/.

Uso:  python3 build.py

Cada caderno é escrito só com o conteúdo (HTML simples) em
src/cadernos/<slug>.html. Este script envolve o conteúdo com o
cabeçalho, o menu lateral e o rodapé, e grava o resultado em
cadernos/<slug>.html. Também gera a página inicial (index.html).
Não precisa de nenhuma biblioteca: só Python 3.
"""
from html import escape
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
SRC = RAIZ / "src" / "cadernos"
SAIDA = RAIZ / "cadernos"

SITE = "Aprenda Matemática"

# (slug, ícone, título, resumo, frequência em provas, termos extras de busca)
GUIAS = [
    ("estrategias", "⏱️", "Estratégias de prova",
     "Como ganhar tempo: ordem de resolução, eliminação de alternativas, estimativa e teste das respostas.",
     "Leia primeiro", "tempo chute eliminar alternativas estimativa"),
    ("formulario", "📋", "Formulário de bolso",
     "Todas as fórmulas e atalhos dos cadernos numa página só, para revisar na véspera.",
     "Revisão", "fórmulas resumo revisão véspera"),
]

CADERNOS = [
    ("aritmetica", "🔢", "Aritmética e divisibilidade",
     "Operações, potências, raízes, critérios de divisibilidade, MMC e MDC.",
     "alta", "mmc mdc primos potência raiz divisores expressão numérica"),
    ("fracoes", "🍕", "Frações e números decimais",
     "Simplificar, comparar e operar frações; dízimas periódicas e conversões.",
     "alta", "fração decimal dízima geratriz"),
    ("porcentagem", "💯", "Porcentagem",
     "Fator multiplicativo, aumentos e descontos sucessivos, variação percentual.",
     "alta", "por cento desconto acréscimo aumento lucro prejuízo"),
    ("razao-proporcao", "⚖️", "Razão e proporção",
     "Razões, propriedades das proporções, escalas e divisão proporcional.",
     "alta", "escala divisão proporcional diretamente inversamente"),
    ("regra-de-tres", "📐", "Regra de três",
     "Simples e composta, com o método das setas e o atalho da causa e consequência.",
     "alta", "regra de três composta simples operários dias"),
    ("juros", "💰", "Juros simples e compostos",
     "Capital, taxa, tempo e montante; taxas equivalentes e desconto.",
     "media", "juros montante capital taxa desconto financeira"),
    ("equacoes", "✖️", "Equações e sistemas",
     "1º e 2º grau, soma e produto das raízes, sistemas lineares e problemas.",
     "alta", "equação bhaskara delta sistema incógnita"),
    ("funcoes", "📈", "Funções",
     "Função afim e quadrática, gráfico, vértice, raízes e sinais.",
     "media", "função afim quadrática vértice gráfico parábola"),
    ("sequencias", "🔁", "Sequências, PA e PG",
     "Padrões numéricos, termo geral e soma de progressões.",
     "media", "progressão aritmética geométrica sequência padrão"),
    ("geometria", "📏", "Geometria plana e espacial",
     "Ângulos, triângulos, Pitágoras, áreas, perímetros e volumes.",
     "media", "área perímetro volume pitágoras triângulo círculo"),
    ("estatistica", "📊", "Estatística básica",
     "Média, mediana, moda, média ponderada, variância e leitura de gráficos.",
     "media", "média mediana moda desvio variância gráfico"),
    ("combinatoria", "🎲", "Análise combinatória",
     "Princípio multiplicativo, permutação, arranjo e combinação sem decoreba.",
     "alta", "permutação arranjo combinação anagrama fatorial"),
    ("probabilidade", "🎯", "Probabilidade",
     "Casos favoráveis, eventos complementares, “e” e “ou”, probabilidade condicional.",
     "alta", "chance evento complementar condicional"),
    ("logica", "🧠", "Raciocínio lógico",
     "Proposições, conectivos, negações, equivalências, tabela-verdade e argumentos.",
     "alta", "proposição negação equivalência tabela verdade silogismo"),
]

TODAS = GUIAS + CADERNOS


def menu_lateral(atual: str, prefixo: str) -> str:
    def itens(lista):
        out = []
        for slug, icone, titulo, *_ in lista:
            classe = ' class="ativo"' if slug == atual else ""
            out.append(
                f'<li data-slug="{slug}"><a href="{prefixo}{slug}.html"{classe}>'
                f'<span>{icone}</span> {escape(titulo)}<span class="feito"></span></a></li>'
            )
        return "\n".join(out)

    return f"""<aside class="lateral">
  <button type="button" class="botao secundario botao-menu">☰ Todos os cadernos</button>
  <div class="lista-cadernos">
    <h3>Comece aqui</h3>
    <ul>
{itens(GUIAS)}
    </ul>
    <h3>Cadernos</h3>
    <ul>
{itens(CADERNOS)}
    </ul>
  </div>
</aside>"""


def pagina(titulo: str, descricao: str, corpo: str, raiz: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(titulo)}</title>
<meta name="description" content="{escape(descricao)}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>➗</text></svg>">
<link rel="stylesheet" href="{raiz}assets/css/style.css">
<script src="{raiz}assets/js/app.js"></script>
</head>
<body>
<header class="topo">
  <a class="marca" href="{raiz}index.html">Aprenda <span>Matemática</span></a>
  <nav>
    <a href="{raiz}cadernos/estrategias.html">Estratégias</a>
    <a href="{raiz}cadernos/formulario.html">Formulário</a>
    <button type="button" class="botao-tema">🌙 Escuro</button>
  </nav>
</header>
{corpo}
<footer class="site">
  {SITE}: conteúdo livre e original para quem estuda para concursos.
  Encontrou um erro? <a href="https://github.com/CarlosGabriel-UX/APRENDA-MATEMATICA/issues">Avise no GitHub</a>.
</footer>
</body>
</html>
"""


def selo_frequencia(freq: str) -> str:
    if freq == "alta":
        return '<span class="selo alta">Cai muito</span>'
    if freq == "media":
        return '<span class="selo media">Cai com frequência</span>'
    return f'<span class="selo">{escape(freq)}</span>'


def gerar_caderno(i: int, item) -> None:
    slug, icone, titulo, resumo, freq, _ = item
    conteudo = (SRC / f"{slug}.html").read_text(encoding="utf-8").strip()
    anterior = TODAS[i - 1] if i > 0 else None
    proximo = TODAS[i + 1] if i + 1 < len(TODAS) else None
    nav_ant = (f'<a class="botao secundario" href="{anterior[0]}.html">← {escape(anterior[2])}</a>'
               if anterior else '<span></span>')
    nav_prox = (f'<a class="botao secundario" href="{proximo[0]}.html">{escape(proximo[2])} →</a>'
                if proximo else '<span></span>')
    corpo = f"""<div class="container layout">
{menu_lateral(slug, "")}
<article class="caderno">
  <h1>{icone} {escape(titulo)}</h1>
  <p class="subtitulo">{escape(resumo)}</p>
  <div class="selos">{selo_frequencia(freq)}</div>
  <nav class="sumario" data-sumario><strong>Neste caderno</strong></nav>
{conteudo}
  <div class="rodape-caderno">
    {nav_ant}
    <button type="button" class="botao marcar-estudado" data-alvo="{slug}">Marcar como estudado</button>
    {nav_prox}
  </div>
</article>
</div>"""
    html = pagina(f"{titulo} · {SITE}", resumo, corpo, "../")
    (SAIDA / f"{slug}.html").write_text(html, encoding="utf-8")


def cartao(item) -> str:
    slug, icone, titulo, resumo, freq, termos = item
    rotulo = {"alta": "Cai muito", "media": "Cai com frequência"}.get(freq, freq)
    return f"""  <a class="cartao" href="cadernos/{slug}.html" data-slug="{slug}" data-termos="{escape(termos)}">
    <span class="icone">{icone}</span>
    <h3>{escape(titulo)}</h3>
    <p>{escape(resumo)}</p>
    <span class="rodape"><span>{escape(rotulo)}</span><span class="ok"></span></span>
  </a>"""


def gerar_inicio() -> None:
    cartoes_guias = "\n".join(cartao(c) for c in GUIAS)
    cartoes = "\n".join(cartao(c) for c in CADERNOS)
    corpo = f"""<main class="container">
  <section class="hero">
    <h1>Matemática para concursos,<br>direto ao ponto.</h1>
    <p>Cadernos gratuitos com teoria enxuta, atalhos que economizam minutos na prova,
    pegadinhas comuns das bancas e exercícios com resolução comentada.</p>
    <div class="acoes">
      <a class="botao" href="cadernos/estrategias.html">Comece pelas estratégias</a>
      <a class="botao secundario" href="cadernos/formulario.html">Ver formulário de bolso</a>
    </div>
  </section>

  <input class="busca" type="search" placeholder="Buscar assunto (ex.: porcentagem, MMC, Bhaskara, negação…)" aria-label="Buscar assunto">
  <div class="progresso-geral"><span class="valor"></span><div class="barra"><span></span></div></div>

  <div class="grade">
{cartoes_guias}
{cartoes}
  </div>

  <section class="secao-inicio">
    <h2>Como estudar com os cadernos</h2>
    <div class="passos">
      <div><h3>Leia a teoria curta</h3><p>Cada caderno começa pelo essencial. Nada de páginas de definição que nunca caem.</p></div>
      <div><h3>Grave os atalhos</h3><p>As caixas verdes mostram o caminho mais rápido. É ali que você ganha tempo.</p></div>
      <div><h3>Evite as pegadinhas</h3><p>As caixas vermelhas mostram os erros que as bancas adoram explorar.</p></div>
      <div><h3>Treine e marque</h3><p>Resolva as questões, confira a explicação e marque o caderno como estudado.</p></div>
    </div>
  </section>
</main>"""
    html = pagina(f"{SITE}: matemática para concursos",
                  "Cadernos gratuitos de matemática para concursos com teoria enxuta, atalhos para ganhar tempo e exercícios comentados.",
                  corpo, "")
    (RAIZ / "index.html").write_text(html, encoding="utf-8")


def main() -> None:
    SAIDA.mkdir(exist_ok=True)
    for i, item in enumerate(TODAS):
        gerar_caderno(i, item)
    gerar_inicio()
    print(f"Geradas {len(TODAS)} páginas de caderno e index.html")


if __name__ == "__main__":
    main()
