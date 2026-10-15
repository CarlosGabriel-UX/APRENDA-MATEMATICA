#!/usr/bin/env python3
"""Gera as páginas do site a partir dos fragmentos em src/.

Uso:  python3 build.py

Cada caderno é escrito só com o conteúdo (HTML simples) em
src/cadernos/<slug>.html. Este script envolve o conteúdo com o
cabeçalho, o menu lateral e o rodapé, e grava o resultado em
cadernos/<slug>.html. Também gera a página inicial (index.html).
Não precisa de nenhuma biblioteca: só Python 3.
"""
import json
from html import escape
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
SRC = RAIZ / "src" / "cadernos"
SAIDA = RAIZ / "cadernos"

SITE = "Aprenda Matemática"
URL_BASE = "https://carlosgabriel-ux.github.io/APRENDA-MATEMATICA/"

# (slug, ícone (glifo), título, resumo, frequência em provas, termos extras de busca)
GUIAS = [
    ("estrategias", "≈", "Estratégias de prova",
     "Como ganhar tempo: ordem de resolução, eliminação de alternativas, estimativa e teste das respostas.",
     "Leia primeiro", "tempo chute eliminar alternativas estimativa"),
    ("trilhas", "↗", "Trilhas por banca e área",
     "Em que ordem estudar e onde concentrar o tempo conforme o estilo da banca e a área do cargo.",
     "Planejamento", "banca cebraspe fgv vunesp fcc cesgranrio policial fiscal bancário tribunais roteiro"),
    ("formulario", "∑", "Formulário de bolso",
     "Todas as fórmulas e atalhos dos cadernos numa página só, para revisar na véspera.",
     "Revisão", "fórmulas resumo revisão véspera"),
]

CADERNOS = [
    ("aritmetica", "÷", "Aritmética e divisibilidade",
     "Operações, potências, raízes, critérios de divisibilidade, MMC e MDC.",
     "alta", "mmc mdc primos potência raiz divisores expressão numérica"),
    ("fracoes", "½", "Frações e números decimais",
     "Simplificar, comparar e operar frações; dízimas periódicas e conversões.",
     "alta", "fração decimal dízima geratriz"),
    ("porcentagem", "%", "Porcentagem",
     "Fator multiplicativo, aumentos e descontos sucessivos, variação percentual.",
     "alta", "por cento desconto acréscimo aumento lucro prejuízo"),
    ("razao-proporcao", "a:b", "Razão e proporção",
     "Razões, propriedades das proporções, escalas e divisão proporcional.",
     "alta", "escala divisão proporcional diretamente inversamente"),
    ("regra-de-tres", "∝", "Regra de três",
     "Simples e composta, com o método das setas e o atalho da causa e consequência.",
     "alta", "regra de três composta simples operários dias"),
    ("juros", "R$", "Juros simples e compostos",
     "Capital, taxa, tempo e montante; taxas equivalentes e desconto.",
     "media", "juros montante capital taxa desconto financeira"),
    ("equacoes", "x=", "Equações e sistemas",
     "1º e 2º grau, soma e produto das raízes, sistemas lineares e problemas.",
     "alta", "equação bhaskara delta sistema incógnita"),
    ("funcoes", "f(x)", "Funções",
     "Função afim e quadrática, gráfico, vértice, raízes e sinais.",
     "media", "função afim quadrática vértice gráfico parábola"),
    ("sequencias", "aₙ", "Sequências, PA e PG",
     "Padrões numéricos, termo geral e soma de progressões.",
     "media", "progressão aritmética geométrica sequência padrão"),
    ("geometria", "△", "Geometria plana e espacial",
     "Ângulos, triângulos, Pitágoras, áreas, perímetros e volumes.",
     "media", "área perímetro volume pitágoras triângulo círculo"),
    ("estatistica", "x̄", "Estatística básica",
     "Média, mediana, moda, média ponderada, variância e leitura de gráficos.",
     "media", "média mediana moda desvio variância gráfico"),
    ("combinatoria", "n!", "Análise combinatória",
     "Princípio multiplicativo, permutação, arranjo e combinação sem decoreba.",
     "alta", "permutação arranjo combinação anagrama fatorial"),
    ("probabilidade", "P", "Probabilidade",
     "Casos favoráveis, eventos complementares, “e” e “ou”, probabilidade condicional.",
     "alta", "chance evento complementar condicional"),
    ("logica", "∧", "Raciocínio lógico",
     "Proposições, conectivos, negações, equivalências, tabela-verdade e argumentos.",
     "alta", "proposição negação equivalência tabela verdade silogismo"),
]

# Imersão concursos: guias de cada concurso e apostilas das outras matérias.
IMERSAO = ("imersao", "★", "Imersão concursos",
           "Escolha o concurso e siga o plano: o que cai, em que ordem estudar e as apostilas de cada matéria.",
           "Comece aqui", "imersão plano de estudos policial pm gcm pf perito")

# (slug, ícone, título, resumo, banca, termos)
CONCURSOS = [
    ("concurso-pmsp", "PM", "PM-SP: Soldado",
     "Soldado de 2ª Classe da Polícia Militar de São Paulo. Banca VUNESP, múltipla escolha.",
     "VUNESP", "polícia militar soldado sp vunesp pmsp"),
    ("concurso-gcm-sp", "GCM", "GCM São Paulo",
     "Guarda Civil Metropolitana da cidade de São Paulo. Banca VUNESP, 60 questões.",
     "VUNESP", "guarda civil metropolitana municipal gcm sp vunesp"),
    ("concurso-pf", "PF", "Polícia Federal: Agente, Escrivão e Papiloscopista",
     "Carreira policial federal de nível superior. Banca CEBRASPE, 120 itens de Certo ou Errado.",
     "CEBRASPE", "polícia federal agente escrivão papiloscopista cebraspe cespe pf"),
    ("concurso-perito-pf", "PCF", "Perito Criminal Federal: Informática",
     "Perito da Polícia Federal, Área 3 (Informática Forense), o perito cibernético. Banca CEBRASPE.",
     "CEBRASPE", "perito criminal federal cibernético informática forense ti área 3 pcf"),
]

# (slug, ícone, título, resumo, concursos que cobram, termos)
APOSTILAS = [
    ("portugues", "Aa", "Língua Portuguesa",
     "Interpretação, concordância, regência, crase, pontuação e reescrita, com os atalhos de cada banca.",
     "Todos", "português gramática interpretação crase concordância regência vírgula pontuação"),
    ("informatica", "⌨", "Noções de Informática",
     "Windows, Word, Excel, internet, e-mail, nuvem e segurança da informação.",
     "Todos", "informática windows excel word internet email segurança atalhos linux"),
    ("direito-constitucional", "CF", "Direito Constitucional",
     "Direitos fundamentais, direitos políticos, administração pública e segurança pública (art. 144).",
     "Todos", "constituição constitucional art 5 144 direitos fundamentais remédios habeas corpus"),
    ("direito-administrativo", "Adm", "Direito Administrativo",
     "Princípios, atos e poderes administrativos, agentes, improbidade e Lei de Acesso à Informação.",
     "Todos", "administrativo limpe atos poderes improbidade lai acesso informação 8112"),
    ("direito-penal", "CP", "Direito Penal",
     "Princípios, teoria do crime, excludentes e os crimes que mais caem em provas policiais.",
     "GCM · PF", "penal crime código penal furto roubo homicídio peculato legítima defesa"),
    ("processo-penal", "CPP", "Processo Penal",
     "Inquérito, ação penal, prisões, provas, cadeia de custódia e Juizados Especiais.",
     "GCM · PF", "processo penal inquérito prisão flagrante preventiva provas custódia algemas"),
    ("legislacao-especial", "Lei", "Legislação Penal Especial",
     "Drogas, desarmamento, tortura, abuso de autoridade, Maria da Penha, ECA, guardas municipais e mais.",
     "GCM · PF", "drogas desarmamento tortura abuso autoridade maria da penha eca idoso guardas susp lgpd"),
    ("direitos-humanos", "DH", "Direitos Humanos",
     "Características, tratados, sistema interamericano, Regras de Mandela e uso da força.",
     "PF · Perito", "direitos humanos dudh san josé mandela uso da força"),
    ("historia", "⌛", "História",
     "Século XX no mundo e no Brasil: guerras, Guerra Fria, Era Vargas, regime militar e redemocratização.",
     "PM-SP", "história vargas ditadura guerra fria constituições"),
    ("geografia", "Geo", "Geografia",
     "Brasil físico e humano, urbanização, energia, meio ambiente e geopolítica.",
     "PM-SP", "geografia biomas clima urbanização energia globalização"),
    ("realidade-sp", "SP", "Atualidades e Realidade de SP",
     "Como estudar atualidades e o que sempre cai sobre a cidade de São Paulo.",
     "PM-SP · GCM", "atualidades realidades municipais cidade de são paulo subprefeituras"),
    ("contabilidade", "D/C", "Contabilidade Geral",
     "Patrimônio, débito e crédito, balanço, DRE e regimes contábeis.",
     "PF (Agente e Escrivão)", "contabilidade patrimônio balanço dre débito crédito"),
    ("criminalistica", "⌕", "Noções de Criminalística",
     "Vestígios, local de crime, cadeia de custódia, laudo pericial e balística.",
     "Perito", "criminalística perícia vestígio local de crime laudo cadeia de custódia"),
    ("ti-redes-seguranca", "IP", "Redes e Segurança",
     "TCP/IP, sub-redes, protocolos, ataques, criptografia e certificados digitais.",
     "Perito", "redes tcp ip osi sub-rede criptografia hash segurança firewall"),
    ("ti-forense", "#", "Computação Forense",
     "Coleta e preservação, imagem forense, sistemas de arquivos, artefatos e celulares.",
     "Perito", "forense computacional perícia digital ntfs imagem hash volatility celular"),
    ("ti-programacao-dados", "{}", "Programação, SO e Dados",
     "Arquitetura, sistemas operacionais, SQL, Python, algoritmos e aprendizado de máquina.",
     "Perito", "python sql banco de dados sistemas operacionais algoritmos machine learning"),
]

# Agrupamento das apostilas no menu e nas páginas da imersão.
GRUPOS_APOSTILAS = [
    ("Básicas", ["portugues", "informatica"]),
    ("Direito", ["direito-constitucional", "direito-administrativo", "direito-penal",
                 "processo-penal", "legislacao-especial", "direitos-humanos"]),
    ("Conhecimentos gerais", ["historia", "geografia", "realidade-sp"]),
    ("Específicas", ["contabilidade", "criminalistica", "ti-redes-seguranca", "ti-forense",
                     "ti-programacao-dados"]),
]
# Matérias de cada concurso, na ordem sugerida de estudo (apostilas e cadernos de matemática).
MATERIAS = {
    "concurso-pmsp": ["portugues", "porcentagem", "razao-proporcao", "regra-de-tres", "fracoes",
                      "aritmetica", "equacoes", "geometria", "estatistica", "logica",
                      "direito-constitucional", "direito-administrativo", "informatica",
                      "historia", "geografia", "realidade-sp"],
    "concurso-gcm-sp": ["legislacao-especial", "direito-constitucional", "direito-penal",
                        "processo-penal", "direito-administrativo", "portugues", "porcentagem",
                        "razao-proporcao", "regra-de-tres", "fracoes", "aritmetica", "equacoes",
                        "geometria", "estatistica", "sequencias", "logica", "realidade-sp",
                        "informatica"],
    "concurso-pf": ["portugues", "direito-constitucional", "direito-administrativo", "direito-penal",
                    "processo-penal", "legislacao-especial", "informatica", "ti-redes-seguranca",
                    "logica", "estatistica", "combinatoria", "probabilidade", "contabilidade"],
    "concurso-perito-pf": ["ti-redes-seguranca", "ti-forense", "ti-programacao-dados", "informatica",
                           "criminalistica", "portugues", "direito-constitucional",
                           "direito-administrativo", "direito-penal", "processo-penal",
                           "direitos-humanos", "logica", "combinatoria", "probabilidade"],
}

PAGINAS_IMERSAO = [IMERSAO] + CONCURSOS + APOSTILAS
SLUGS_IMERSAO = {p[0] for p in PAGINAS_IMERSAO}

# Páginas de ferramenta: aparecem no menu, mas não contam como caderno estudado.
FERRAMENTAS = [
    ("erros", "✗", "Meu caderno de erros",
     "As questões que você errou nos cadernos, reunidas para revisar até acertar.",
     "Revisão", "erros revisão"),
]

# Páginas institucionais: fora do menu de cadernos.
INSTITUCIONAIS = [
    ("sobre", "i", "Sobre o projeto",
     "O que é o Aprenda Matemática, como o conteúdo é feito e como contribuir.",
     "Projeto", "sobre"),
]

TODAS = GUIAS + CADERNOS

# Cor de cada assunto (usada no ícone, no cartão e no título).
COR = {
    "estrategias": "#475569", "trilhas": "#0f766e", "formulario": "#4338ca",
    "erros": "#b91c1c", "sobre": "#475569",
    "aritmetica": "#1d4ed8", "fracoes": "#c2410c", "porcentagem": "#15803d",
    "razao-proporcao": "#6d28d9", "regra-de-tres": "#0e7490", "juros": "#a16207",
    "equacoes": "#be185d", "funcoes": "#4338ca", "sequencias": "#0f766e",
    "geometria": "#b45309", "estatistica": "#1e40af", "combinatoria": "#9333ea",
    "probabilidade": "#a21caf", "logica": "#6d28d9",
    "imersao": "#b45309", "concurso-pmsp": "#1e3a8a", "concurso-gcm-sp": "#0f766e",
    "concurso-pf": "#4b5563", "concurso-perito-pf": "#7c3aed",
    "portugues": "#be123c", "informatica": "#0369a1", "direito-constitucional": "#166534",
    "direito-administrativo": "#4d7c0f", "direito-penal": "#991b1b", "processo-penal": "#9a3412",
    "legislacao-especial": "#7e22ce", "direitos-humanos": "#0e7490", "historia": "#92400e",
    "geografia": "#15803d", "realidade-sp": "#b91c1c", "contabilidade": "#0f766e",
    "criminalistica": "#334155", "ti-redes-seguranca": "#1d4ed8", "ti-forense": "#4338ca",
    "ti-programacao-dados": "#a16207",
}

# Agrupamento dos cadernos na página inicial.
NIVEIS = [
    ("Básico", "A base que aparece em quase toda prova.",
     ["aritmetica", "fracoes", "porcentagem", "razao-proporcao", "regra-de-tres", "equacoes"]),
    ("Intermediário", "Assuntos que exigem a base bem firme.",
     ["funcoes", "sequencias", "geometria", "estatistica", "logica"]),
    ("Avançado", "Onde as bancas separam quem treinou de quem não treinou.",
     ["juros", "combinatoria", "probabilidade"]),
]

LOGO = ('<svg class="logo" viewBox="0 0 32 32" aria-hidden="true">'
        '<defs><linearGradient id="gradiente-logo" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#3156f5"/><stop offset="1" stop-color="#7c3aed"/></linearGradient></defs>'
        '<rect width="32" height="32" rx="9" fill="url(#gradiente-logo)"/>'
        '<rect x="8" y="14.5" width="16" height="3" rx="1.5" fill="#fff"/>'
        '<circle cx="16" cy="9" r="2.6" fill="#fff"/><circle cx="16" cy="23" r="2.6" fill="#fff"/></svg>')
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
           "%3Crect width='32' height='32' rx='9' fill='%233156f5'/%3E"
           "%3Crect x='8' y='14.5' width='16' height='3' rx='1.5' fill='%23fff'/%3E"
           "%3Ccircle cx='16' cy='9' r='2.6' fill='%23fff'/%3E%3Ccircle cx='16' cy='23' r='2.6' fill='%23fff'/%3E%3C/svg%3E")


def icone(slug: str, glifo: str, classe: str = "icone") -> str:
    tamanho = "longo" if len(glifo) >= 3 else ("medio" if len(glifo) == 2 else "curto")
    return (f'<span class="{classe} {tamanho}" style="--cor: {COR.get(slug, "#2357d9")}" '
            f'aria-hidden="true">{escape(glifo)}</span>')
SEM_BOTAO_ESTUDADO = {"erros", "sobre", "imersao"} | {c[0] for c in CONCURSOS}
SEM_SELOS = {"erros", "sobre", "imersao"}


def icone_menu(slug: str, glifo: str) -> str:
    return icone(slug, glifo, "icone mini")


def menu_lateral(atual: str, prefixo: str) -> str:
    if atual in SLUGS_IMERSAO:
        return menu_imersao(atual, prefixo)

    def itens(lista):
        out = []
        for slug, glifo, titulo, *_ in lista:
            classe = ' class="ativo"' if slug == atual else ""
            out.append(
                f'<li data-slug="{slug}"><a href="{prefixo}{slug}.html"{classe}>'
                f'{icone_menu(slug, glifo)} {escape(titulo)}<span class="feito"></span></a></li>'
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
    <h3>Revisão</h3>
    <ul>
{itens(FERRAMENTAS)}
    </ul>
    <h3>Outras matérias</h3>
    <ul>
{itens([IMERSAO])}
    </ul>
  </div>
</aside>"""


def menu_imersao(atual: str, prefixo: str) -> str:
    por_slug = {p[0]: p for p in PAGINAS_IMERSAO}

    def itens(lista):
        out = []
        for slug, glifo, titulo, *_ in lista:
            classe = ' class="ativo"' if slug == atual else ""
            out.append(
                f'<li data-slug="{slug}"><a href="{prefixo}{slug}.html"{classe}>'
                f'{icone_menu(slug, glifo)} {escape(titulo)}<span class="feito"></span></a></li>'
            )
        return "\n".join(out)

    grupos = "\n".join(
        f"    <h3>{escape(nome)}</h3>\n    <ul>\n{itens([por_slug[s] for s in slugs])}\n    </ul>"
        for nome, slugs in GRUPOS_APOSTILAS)
    return f"""<aside class="lateral">
  <button type="button" class="botao secundario botao-menu">☰ Concursos e matérias</button>
  <div class="lista-cadernos">
    <h3>Imersão</h3>
    <ul>
{itens([IMERSAO] + CONCURSOS)}
    </ul>
{grupos}
    <h3>Matemática</h3>
    <ul>
{itens(GUIAS[1:2])}
    <li><a href="{prefixo}../index.html#cadernos">{icone_menu("aritmetica", "÷")} Todos os cadernos de matemática</a></li>
    </ul>
    <h3>Revisão</h3>
    <ul>
{itens(FERRAMENTAS)}
    </ul>
  </div>
</aside>"""


def pagina(titulo: str, descricao: str, corpo: str, raiz: str, caminho: str,
           slug: str = "inicio", titulo_curto: str = "", dados_estruturados: str = "",
           com_formulas: bool = False) -> str:
    url = URL_BASE + caminho
    katex = (f'<link rel="stylesheet" href="{raiz}assets/vendor/katex/katex.min.css">\n'
             f'<script defer src="{raiz}assets/vendor/katex/katex.min.js"></script>\n'
             if com_formulas else "")
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(titulo)}</title>
<meta name="description" content="{escape(descricao)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="{SITE}">
<meta property="og:title" content="{escape(titulo)}">
<meta property="og:description" content="{escape(descricao)}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<meta name="theme-color" content="#3156f5">{'<meta name="robots" content="noindex">' if slug == "erros" else ""}
<link rel="icon" href="{FAVICON}">
<link rel="stylesheet" href="{raiz}assets/css/style.css">
<script src="{raiz}assets/js/app.js"></script>
{katex}{dados_estruturados}</head>
<body data-pagina="{slug}" data-titulo="{escape(titulo_curto or titulo)}">
<a class="pular" href="#conteudo">Pular para o conteúdo</a>
<header class="topo">
  <a class="marca" href="{raiz}index.html">{LOGO}<span class="nome">Aprenda <span>Matemática</span></span></a>
  <nav class="nav-topo" aria-label="Atalhos">
    <a href="{raiz}cadernos/imersao.html" class="destaque">Imersão concursos</a>
    <a href="{raiz}cadernos/trilhas.html">Trilhas</a>
    <a href="{raiz}cadernos/formulario.html">Formulário</a>
    <a href="{raiz}cadernos/erros.html">Erros <span class="contador" data-contagem-erros hidden></span></a>
    <button type="button" class="botao-fonte" aria-label="Mudar o tamanho da letra">Aa</button>
    <button type="button" class="botao-tema" aria-label="Alternar tema claro ou escuro">🌙 Escuro</button>
  </nav>
</header>
<div class="progresso-leitura" aria-hidden="true"><span></span></div>
{corpo}
<footer class="site">
  <span class="rodape-marca">{SITE}</span>
  Conteúdo livre e original para quem estuda para concursos.<br>
  <a href="{raiz}cadernos/sobre.html">Sobre o projeto</a> ·
  <a href="https://github.com/CarlosGabriel-UX/APRENDA-MATEMATICA/issues">Avise sobre um erro</a>
</footer>
<button type="button" class="voltar-topo" aria-label="Voltar ao topo" hidden>↑</button>
<nav class="nav-inferior" aria-label="Navegação principal">
  <a href="{raiz}index.html"><span aria-hidden="true">⌂</span>Início</a>
  <a href="{raiz}cadernos/imersao.html"><span aria-hidden="true">★</span>Imersão</a>
  <a href="{raiz}cadernos/erros.html"><span aria-hidden="true">✗</span>Erros<span class="contador" data-contagem-erros hidden></span></a>
  <button type="button" class="botao-fonte" aria-label="Mudar o tamanho da letra"><span aria-hidden="true">Aa</span>Letra</button>
  <button type="button" class="botao-tema" aria-label="Alternar tema claro ou escuro">Tema</button>
</nav>
</body>
</html>
"""


def json_ld(dados: dict) -> str:
    texto = json.dumps(dados, ensure_ascii=False, indent=1).replace("</", "<\\/")
    return f'<script type="application/ld+json">\n{texto}\n</script>\n'


def selo_frequencia(freq: str, slug: str = "") -> str:
    if slug in {c[0] for c in CONCURSOS}:
        return f'<span class="selo banca">Banca {escape(freq)}</span>'
    if slug in {a[0] for a in APOSTILAS}:
        return f'<span class="selo cai-em">Cai em: {escape(freq)}</span>'
    if freq == "alta":
        return '<span class="selo alta">Cai muito</span>'
    if freq == "media":
        return '<span class="selo media">Cai com frequência</span>'
    return f'<span class="selo">{escape(freq)}</span>'


def gerar_caderno(item, anterior=None, proximo=None) -> None:
    slug, glifo, titulo, resumo, freq, _ = item
    conteudo = (SRC / f"{slug}.html").read_text(encoding="utf-8").strip()
    if "<!-- mapa -->" in conteudo:
        conteudo = conteudo.replace("<!-- mapa -->", mapa_materias(MATERIAS[slug]))
    nav_ant = (f'<a class="botao secundario" href="{anterior[0]}.html">← {escape(anterior[2])}</a>'
               if anterior else '<span></span>')
    nav_prox = (f'<a class="botao secundario" href="{proximo[0]}.html">{escape(proximo[2])} →</a>'
                if proximo else '<span></span>')
    botao = ("<span></span>" if slug in SEM_BOTAO_ESTUDADO else
             f'<button type="button" class="botao marcar-estudado" data-alvo="{slug}">Marcar como estudado</button>')
    rodape = "" if slug in SEM_SELOS else f"""
  <div class="rodape-caderno">
    {nav_ant}
    {botao}
    {nav_prox}
  </div>"""
    selos = f'<div class="selos">{selo_frequencia(freq, slug)}</div>' if slug not in SEM_SELOS else ""
    corpo = f"""<div class="container layout">
{menu_lateral(slug, "")}
<article class="caderno" id="conteudo" style="--cor: {COR.get(slug, "#2357d9")}">
  <h1>{icone(slug, glifo)} <span>{escape(titulo)}</span></h1>
  <p class="subtitulo">{escape(resumo)}</p>
  {selos}
  <nav class="sumario" data-sumario><strong>Nesta página</strong></nav>
{conteudo}{rodape}
</article>
</div>"""
    caminho = f"cadernos/{slug}.html"
    dados = json_ld({
        "@context": "https://schema.org",
        "@type": "LearningResource",
        "name": titulo,
        "description": resumo,
        "url": URL_BASE + caminho,
        "inLanguage": "pt-BR",
        "isAccessibleForFree": True,
        "educationalLevel": "Concursos públicos",
        "learningResourceType": ("Guia de estudos" if slug in SEM_BOTAO_ESTUDADO
                                 else "Apostila com exercícios"),
        "isPartOf": {"@type": "WebSite", "name": SITE, "url": URL_BASE},
    }) if slug not in ("erros",) else ""
    html = pagina(f"{titulo} · {SITE}", resumo, corpo, "../", caminho, slug, titulo, dados,
                  com_formulas='class="formula"' in conteudo)
    (SAIDA / f"{slug}.html").write_text(html, encoding="utf-8")


def mapa_materias(slugs) -> str:
    por_slug = {p[0]: p for p in TODAS + APOSTILAS}
    itens = []
    for i, s in enumerate(slugs, 1):
        slug, glifo, titulo, resumo, *_ = por_slug[s]
        tipo = "Matemática" if s in {c[0] for c in CADERNOS} else "Apostila"
        itens.append(
            f'  <li data-slug="{slug}"><a href="{slug}.html" style="--cor: {COR.get(slug, "#2357d9")}">'
            f'<span class="ordem">{i}</span>{icone(slug, glifo, "icone mini")}'
            f'<span class="texto"><strong>{escape(titulo)}</strong><small>{tipo}</small></span>'
            f'<span class="feito"></span></a></li>')
    return (f'<div class="mapa" data-mapa>\n<p class="mapa-progresso" aria-live="polite"></p>\n'
            f'<ol class="mapa-materias">\n' + "\n".join(itens) + "\n</ol>\n</div>")


def cartao_concurso(item) -> str:
    slug, glifo, titulo, resumo, banca, termos = item
    materias = MATERIAS[slug]
    return f"""  <a class="cartao concurso" href="cadernos/{slug}.html" data-materias="{",".join(materias)}" data-termos="{escape(termos)}" style="--cor: {COR.get(slug, "#2357d9")}">
    <span class="faixa">{icone(slug, glifo)}<span class="chip">{escape(banca)}</span></span>
    <h3>{escape(titulo)}</h3>
    <p>{escape(resumo)}</p>
    <span class="rodape"><span>{len(materias)} matérias no plano</span><span class="ok-concurso"></span></span>
  </a>"""


def cartao(item) -> str:
    slug, glifo, titulo, resumo, freq, termos = item
    rotulo = {"alta": "Cai muito", "media": "Cai com frequência"}.get(freq, freq)
    if slug in {a[0] for a in APOSTILAS}:
        rotulo = f"Cai em: {freq}"
    return f"""  <a class="cartao" href="cadernos/{slug}.html" data-slug="{slug}" data-termos="{escape(termos)}" style="--cor: {COR.get(slug, "#2357d9")}">
    {icone(slug, glifo)}
    <h3>{escape(titulo)}</h3>
    <p>{escape(resumo)}</p>
    <span class="rodape"><span>{escape(rotulo)}</span><span class="ok"></span></span>
  </a>"""


def gerar_inicio() -> None:
    cartoes_guias = "\n".join(cartao(c) for c in GUIAS)
    por_slug = {c[0]: c for c in CADERNOS}
    grupos = []
    for nome, descricao_nivel, slugs in NIVEIS:
        cartoes = "\n".join(cartao(por_slug[s]) for s in slugs)
        grupos.append(f"""  <section class="grupo-cadernos">
    <h2>{escape(nome)} <small>{escape(descricao_nivel)}</small></h2>
    <div class="grade">
{cartoes}
    </div>
  </section>""")
    grupos_html = "\n".join(grupos)
    por_slug_ap = {a[0]: a for a in APOSTILAS}
    grupos_ap = "\n".join(f"""  <section class="grupo-cadernos">
    <h2>{escape(nome)}</h2>
    <div class="grade">
{chr(10).join(cartao(por_slug_ap[s]) for s in slugs)}
    </div>
  </section>""" for nome, slugs in GRUPOS_APOSTILAS)
    cartoes_concursos = "\n".join(cartao_concurso(c) for c in CONCURSOS)
    total_questoes = sum((SRC / f"{c[0]}.html").read_text(encoding="utf-8").count('class="questao"')
                         for c in TODAS + APOSTILAS if (SRC / f"{c[0]}.html").exists())
    corpo = f"""<main class="container" id="conteudo">
  <section class="hero">
    <div class="hero-texto">
      <p class="sobretitulo">Gratuito · {len(CADERNOS)} cadernos de matemática · {len(APOSTILAS)} apostilas · {total_questoes} questões comentadas</p>
      <h1>Estude para concursos<br><span>sem perder tempo.</span></h1>
      <p>Matemática com atalhos de prova e uma imersão completa para PM-SP, GCM São Paulo,
      Polícia Federal e Perito Criminal Federal: o que cai, em que ordem estudar e apostilas de todas as matérias.</p>
      <div class="acoes">
        <a class="botao" href="cadernos/imersao.html">Começar a imersão</a>
        <a class="botao secundario" href="#cadernos">Cadernos de matemática</a>
      </div>
    </div>
    <div class="hero-arte" aria-hidden="true">
      <span style="--cor:#15803d">%</span><span style="--cor:#166534">CF</span><span style="--cor:#6d28d9">∧</span>
      <span style="--cor:#be123c">Aa</span><span style="--cor:#991b1b">CP</span><span style="--cor:#1d4ed8">IP</span>
    </div>
  </section>

  <section class="painel" aria-label="Seu progresso">
    <a class="continuar" data-continuar hidden href="#">
      <span class="rotulo-pequeno">Continue de onde parou</span>
      <strong class="titulo-continuar"></strong>
      <span class="seta" aria-hidden="true">→</span>
    </a>
    <div class="estatisticas">
      <div><strong data-estat="resolvidas">0</strong><span>questões resolvidas</span></div>
      <div><strong data-estat="acerto">–</strong><span>de acerto</span></div>
      <a href="cadernos/erros.html"><strong data-estat="erros">0</strong><span>no caderno de erros</span></a>
    </div>
  </section>

  <input class="busca" type="search" placeholder="Buscar concurso, matéria ou assunto (ex.: PF, crase, porcentagem, flagrante…)" aria-label="Buscar concurso, matéria ou assunto">
  <p class="sem-resultado" hidden>Nada encontrado. Tente outra palavra.</p>

  <section class="grupo-cadernos destaque-imersao">
    <h2>Imersão: escolha seu concurso <small>Cada guia traz o mapa das matérias, a ordem de estudo e um plano semana a semana.</small></h2>
    <div class="grade concursos">
{cartoes_concursos}
    </div>
  </section>

  <div class="bloco" data-bloco="matematica">
  <div class="titulo-bloco" id="cadernos">
    <h2>Matemática e raciocínio lógico</h2>
    <div class="progresso-geral"><span class="valor"></span><div class="barra"><span></span></div></div>
  </div>
  <section class="grupo-cadernos">
    <h2>Comece aqui <small>Leia antes dos cadernos.</small></h2>
    <div class="grade">
{cartoes_guias}
    </div>
  </section>
{grupos_html}
  </div>

  <div class="titulo-bloco" id="apostilas">
    <h2>Apostilas das outras matérias</h2>
    <p>Teoria enxuta, atalhos, pegadinhas e questões no estilo VUNESP e CEBRASPE.</p>
  </div>
{grupos_ap}

  <section class="secao-inicio">
    <h2>Como estudar aqui</h2>
    <div class="passos">
      <div><h3>Escolha o concurso</h3><p>O guia mostra as matérias na ordem que dá mais pontos por hora de estudo.</p></div>
      <div><h3>Grave os atalhos</h3><p>As caixas verdes mostram o caminho mais rápido. É ali que você ganha tempo.</p></div>
      <div><h3>Evite as pegadinhas</h3><p>As caixas vermelhas mostram os erros que as bancas adoram explorar.</p></div>
      <div><h3>Treine e revise</h3><p>Resolva as questões. As que você errar vão para o caderno de erros até você acertar.</p></div>
    </div>
  </section>
</main>"""
    descricao = ("Matemática e apostilas gratuitas para concursos: imersão para PM-SP, GCM São Paulo, "
                 "Polícia Federal e Perito Criminal Federal, com atalhos de prova e questões comentadas.")
    dados = json_ld({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE,
        "url": URL_BASE,
        "description": descricao,
        "inLanguage": "pt-BR",
    })
    html = pagina(f"{SITE}: matemática e apostilas para concursos grátis", descricao, corpo, "", "",
                  "inicio", SITE, dados)
    (RAIZ / "index.html").write_text(html, encoding="utf-8")


def gerar_sitemap() -> None:
    caminhos = [""] + [f"cadernos/{c[0]}.html" for c in TODAS + PAGINAS_IMERSAO + INSTITUCIONAIS]
    urls = "\n".join(
        f"  <url><loc>{URL_BASE}{c}</loc></url>" for c in caminhos
    )
    (RAIZ / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n</urlset>\n", encoding="utf-8")


def main() -> None:
    SAIDA.mkdir(exist_ok=True)
    for i, item in enumerate(TODAS):
        anterior = TODAS[i - 1] if i > 0 else None
        proximo = TODAS[i + 1] if i + 1 < len(TODAS) else None
        gerar_caderno(item, anterior, proximo)
    for lista in (CONCURSOS, APOSTILAS):
        for i, item in enumerate(lista):
            anterior = lista[i - 1] if i > 0 else None
            proximo = lista[i + 1] if i + 1 < len(lista) else None
            gerar_caderno(item, anterior, proximo)
    for item in [IMERSAO] + FERRAMENTAS + INSTITUCIONAIS:
        gerar_caderno(item)
    gerar_inicio()
    gerar_sitemap()
    total = len(TODAS) + len(PAGINAS_IMERSAO) + len(FERRAMENTAS) + len(INSTITUCIONAIS)
    print(f"Geradas {total} páginas, index.html e sitemap.xml")


if __name__ == "__main__":
    main()
