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
import re
import subprocess
from datetime import date
from html import escape
from html.parser import HTMLParser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
SRC = RAIZ / "src" / "cadernos"
SAIDA = RAIZ / "cadernos"

SITE = "Aprenda Matemática"
URL_BASE = "https://carlosgabriel-ux.github.io/APRENDA-MATEMATICA/"
# Caminho do site no domínio: a página 404 usa links absolutos porque pode abrir em qualquer pasta.
CAMINHO_SITE = "/APRENDA-MATEMATICA/"
# Imagem que aparece ao compartilhar um link (WhatsApp, redes sociais): 1200 x 630.
IMAGEM_OG = "assets/og-imagem.png"

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

# Banco de questões: uma página por banca, com as questões separadas por matéria.
# As questões ficam em src/questoes/<banca>-*.html, dentro de <section data-materia="slug">.
QUESTOES_SRC = RAIZ / "src" / "questoes"
BANCO = ("questoes", "?", "Banco de questões",
         "Questões originais separadas por banca e por matéria, com figuras, gráficos, tabelas e código.",
         "Treino", "questões exercícios banco treino vunesp cebraspe")
# (slug, ícone, título, resumo, para quais concursos, termos, prefixo dos arquivos)
BANCAS = [
    ("questoes-vunesp", "V", "Questões estilo VUNESP",
     "Múltipla escolha com 5 alternativas, no estilo das provas da PM-SP e da GCM São Paulo, separadas por matéria.",
     "PM-SP · GCM", "questões vunesp múltipla escolha pm gcm soldado guarda", "vunesp"),
    ("questoes-cebraspe", "C/E", "Questões estilo CEBRASPE",
     "Itens de Certo ou Errado no estilo das provas da Polícia Federal e do Perito Criminal Federal, separados por matéria.",
     "PF · Perito", "questões cebraspe cespe certo errado pf perito agente escrivão", "cebraspe"),
]
PROVAS = ("provas-oficiais", "⎙", "Provas oficiais",
          "Onde achar as provas e os gabaritos oficiais da VUNESP e da CEBRASPE e como transformá-los num simulado.",
          "Treino real", "provas anteriores gabarito oficial baixar pdf simulado")
PAGINAS_QUESTOES = [BANCO] + [b[:6] for b in BANCAS] + [PROVAS]
SLUGS_BANCAS = {b[0]: b for b in BANCAS}
# Ordem das matérias em cada banco (as que não estiverem aqui vão para o fim).
ORDEM_BANCO = {
    "vunesp": ["portugues", "porcentagem", "razao-proporcao", "regra-de-tres", "fracoes", "aritmetica",
               "equacoes", "funcoes", "geometria", "estatistica", "sequencias", "juros", "combinatoria",
               "probabilidade", "logica", "direito-constitucional",
               "direito-administrativo", "direito-penal", "processo-penal", "legislacao-especial",
               "informatica", "historia", "geografia", "realidade-sp"],
    "cebraspe": ["portugues", "direito-constitucional", "direito-administrativo", "direito-penal",
                 "processo-penal", "legislacao-especial", "direitos-humanos", "informatica", "logica",
                 "estatistica", "combinatoria", "probabilidade", "contabilidade", "criminalistica",
                 "ti-redes-seguranca", "ti-forense", "ti-programacao-dados"],
}

PAGINAS_IMERSAO = [IMERSAO] + CONCURSOS + APOSTILAS + PAGINAS_QUESTOES
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
    "questoes": "#3156f5", "questoes-vunesp": "#c2410c", "questoes-cebraspe": "#0e7490",
    "provas-oficiais": "#475569",
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
        '<rect width="32" height="32" rx="8" fill="#2a44c7"/>'
        '<rect x="6.5" y="13.5" width="19" height="5" rx="2.5" fill="#ffd84a"/>'
        '<circle cx="16" cy="8.5" r="2.6" fill="#fff"/><circle cx="16" cy="23.5" r="2.6" fill="#fff"/></svg>')
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
           "%3Crect width='32' height='32' rx='8' fill='%232a44c7'/%3E"
           "%3Crect x='6.5' y='13.5' width='19' height='5' rx='2.5' fill='%23ffd84a'/%3E"
           "%3Ccircle cx='16' cy='8.5' r='2.6' fill='%23fff'/%3E%3Ccircle cx='16' cy='23.5' r='2.6' fill='%23fff'/%3E%3C/svg%3E")

# Ícones de traço (24x24) do cabeçalho e da barra inferior do celular.
def svg(caminho: str) -> str:
    return ('<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{caminho}</svg>')


ICONES = {
    "inicio": svg('<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M10 21v-6h4v6"/>'),
    "imersao": svg('<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2"/>'),
    "questoes": svg('<path d="M9 11.5 11 13.5 15.5 9"/><rect x="3.5" y="3.5" width="17" height="17" rx="4"/>'),
    "erros": svg('<path d="M6 3.5h12v17l-6-4-6 4z"/><path d="m9.5 8 5 5M14.5 8l-5 5"/>'),
    "menu": svg('<path d="M4 6h16M4 12h16M4 18h10"/>'),
    "lua": svg('<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>'),
    "fechar": svg('<path d="M6 6l12 12M18 6 6 18"/>'),
    "busca": svg('<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/>'),
    "conta": svg('<circle cx="12" cy="8" r="4"/><path d="M4.5 20.5c1.2-4 4.1-6 7.5-6s6.3 2 7.5 6"/>'),
}

# Exportar e importar o progresso (fica na página inicial e no caderno de erros).
BACKUP = """<div class="backup" data-backup>
    <p><strong>Seu progresso fica só neste aparelho.</strong> Salve um arquivo para não perder nada ou para continuar em outro celular ou computador.</p>
    <div class="acoes-backup">
      <button type="button" class="botao secundario exportar">Exportar progresso</button>
      <button type="button" class="botao secundario importar">Importar progresso</button>
      <input type="file" accept="application/json,.json" hidden>
    </div>
    <p class="aviso-backup" role="status"></p>
    <p class="dica-conta"><span data-estado-conta></span> <button type="button" class="link-conta" data-abrir-conta="criar">Prefere não se preocupar com isso? Crie uma conta e o progresso é salvo sozinho.</button></p>
  </div>"""


def icone(slug: str, glifo: str, classe: str = "icone") -> str:
    tamanho = "longo" if len(glifo) >= 3 else ("medio" if len(glifo) == 2 else "curto")
    return (f'<span class="{classe} {tamanho}" style="--cor: {COR.get(slug, "#2357d9")}" '
            f'aria-hidden="true">{escape(glifo)}</span>')
SEM_BOTAO_ESTUDADO = ({"erros", "sobre", "imersao"} | {c[0] for c in CONCURSOS}
                      | {p[0] for p in PAGINAS_QUESTOES})
SEM_SELOS = {"erros", "sobre", "imersao", "questoes", "provas-oficiais"}
SEM_SUMARIO = set(SLUGS_BANCAS) | {"questoes"}


def icone_menu(slug: str, glifo: str) -> str:
    return icone(slug, glifo, "icone mini")


def botao_menu(rotulo: str) -> str:
    return (f'<button type="button" class="botao-menu" aria-controls="menu-lateral" aria-expanded="false">'
            f'{ICONES["menu"]} {rotulo}</button>')


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

    return f"""{botao_menu("Todos os cadernos")}
<aside class="lateral" id="menu-lateral" aria-label="Todos os cadernos">
  <div class="cabeca-gaveta"><strong>Todos os cadernos</strong>
    <button type="button" class="botao-icone fechar-menu" aria-label="Fechar o menu">{ICONES["fechar"]}</button></div>
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
    return f"""{botao_menu("Concursos e matérias")}
<aside class="lateral" id="menu-lateral" aria-label="Concursos e matérias">
  <div class="cabeca-gaveta"><strong>Concursos e matérias</strong>
    <button type="button" class="botao-icone fechar-menu" aria-label="Fechar o menu">{ICONES["fechar"]}</button></div>
  <div class="lista-cadernos">
    <h3>Imersão</h3>
    <ul>
{itens([IMERSAO] + CONCURSOS)}
    </ul>
    <h3>Questões</h3>
    <ul>
{itens(PAGINAS_QUESTOES)}
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


def secao(slug: str) -> str:
    """Seção do site a que a página pertence (para destacar o atalho certo no menu)."""
    if slug in {p[0] for p in PAGINAS_QUESTOES}:
        return "questoes"
    if slug in SLUGS_IMERSAO:
        return "imersao"
    return slug


def pagina(titulo: str, descricao: str, corpo: str, raiz: str, caminho: str,
           slug: str = "inicio", titulo_curto: str = "", dados_estruturados: str = "",
           com_formulas: bool = False) -> str:
    url = URL_BASE + caminho
    indexar = slug not in ("erros", "404")
    atual = secao(slug)

    def link_nav(alvo: str, rotulo: str, href: str) -> str:
        marca = (' aria-current="page"' if href.endswith(f"/{slug}.html") or (slug == "inicio" and alvo == "inicio")
                 else (' aria-current="true"' if alvo == atual else ""))
        return f'<a href="{raiz}{href}"{marca}>{rotulo}</a>'

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
{f'<link rel="canonical" href="{url}">' if indexar else '<meta name="robots" content="noindex">'}
<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="{SITE}">
<meta property="og:title" content="{escape(titulo)}">
<meta property="og:description" content="{escape(descricao)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{URL_BASE}{IMAGEM_OG}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Aprenda Matemática: estude para concursos sem perder tempo">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#f7f5ef" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#121316" media="(prefers-color-scheme: dark)">
<link rel="icon" href="{FAVICON}">
<link rel="stylesheet" href="{raiz}assets/css/style.css">
<script src="{raiz}assets/js/conta.js"></script>
<script src="{raiz}assets/js/app.js"></script>
{katex}{dados_estruturados}</head>
<body data-pagina="{slug}" data-titulo="{escape(titulo_curto or titulo)}">
<a class="pular" href="#conteudo">Pular para o conteúdo</a>
<header class="topo">
  <div class="topo-interno">
  <a class="marca" href="{raiz}index.html">{LOGO}<span class="nome">Aprenda <span>Matemática</span></span></a>
  <nav class="nav-topo" aria-label="Atalhos">
    {link_nav("imersao", "Imersão concursos", "cadernos/imersao.html")}
    {link_nav("questoes", "Questões", "cadernos/questoes.html")}
    {link_nav("trilhas", "Trilhas", "cadernos/trilhas.html")}
    {link_nav("formulario", "Formulário", "cadernos/formulario.html")}
    {link_nav("erros", 'Erros <span class="contador" data-contagem-erros hidden></span>', "cadernos/erros.html")}
  </nav>
  <div class="ajustes">
    <button type="button" class="botao-icone botao-conta" aria-label="Entrar ou criar conta">{ICONES["conta"]}</button>
    <a class="botao-icone botao-busca" href="{raiz}index.html#busca" aria-label="Buscar no site" title="Buscar no site">{ICONES["busca"]}</a>
    <button type="button" class="botao-icone botao-fonte" aria-label="Mudar o tamanho da letra"><span aria-hidden="true">Aa</span></button>
    <button type="button" class="botao-icone botao-tema" aria-label="Alternar tema claro ou escuro">{ICONES["lua"]}</button>
  </div>
  </div>
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
  {link_nav("inicio", ICONES["inicio"] + "<span>Início</span>", "index.html")}
  {link_nav("imersao", ICONES["imersao"] + "<span>Imersão</span>", "cadernos/imersao.html")}
  {link_nav("questoes", ICONES["questoes"] + "<span>Questões</span>", "cadernos/questoes.html")}
  {link_nav("erros", ICONES["erros"] + '<span>Erros</span><span class="contador" data-contagem-erros hidden></span>', "cadernos/erros.html")}
  <a href="{raiz}index.html#cadernos" class="abrir-menu" aria-controls="menu-lateral">{ICONES["menu"]}<span>Matérias</span></a>
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
    if slug in SLUGS_BANCAS:
        return f'<span class="selo cai-em">Para: {escape(freq)}</span>'
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
    if "<!-- banco -->" in conteudo:
        conteudo = conteudo.replace("<!-- banco -->", montar_banco(SLUGS_BANCAS[slug][6]))
    if "<!-- backup -->" in conteudo:
        conteudo = conteudo.replace("<!-- backup -->", BACKUP)
    if "<!-- bancas -->" in conteudo:
        conteudo = conteudo.replace("<!-- bancas -->", tabela_bancas())
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
  <header class="cabeca-caderno">
  <h1>{icone(slug, glifo)} <span>{escape(titulo)}</span></h1>
  <p class="subtitulo">{escape(resumo)}</p>
  {selos}
  </header>
  {"" if slug in SEM_SUMARIO else '<details class="sumario" data-sumario open><summary>Nesta página</summary></details>'}
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


def ler_banco(prefixo: str):
    """Junta as seções de src/questoes/<prefixo>-*.html: [(slug da matéria, [questões])]."""
    materias = {}
    for arq in sorted(QUESTOES_SRC.glob(f"{prefixo}-*.html")):
        texto = arq.read_text(encoding="utf-8")
        for m in re.finditer(r'<section data-materia="([a-z0-9-]+)">(.*?)</section>', texto, re.S):
            partes = re.split(r'(?=<div class="questao")', m.group(2).strip())
            questoes = [q.strip() for q in partes if q.startswith('<div class="questao"')]
            materias.setdefault(m.group(1), []).extend(questoes)
    ordem = ORDEM_BANCO.get(prefixo, [])
    return sorted(materias.items(), key=lambda kv: ordem.index(kv[0]) if kv[0] in ordem else len(ordem))


def montar_banco(prefixo: str) -> str:
    por_slug = {p[0]: p for p in TODAS + APOSTILAS}
    banco = ler_banco(prefixo)
    total = sum(len(q) for _, q in banco)
    botoes = [f'<button type="button" class="ativo" data-materia="" aria-pressed="true">Todas <span>{total}</span></button>']
    secoes = []
    for slug, questoes in banco:
        _, glifo, titulo, *_ = por_slug[slug]
        botoes.append(f'<button type="button" data-materia="{slug}" aria-pressed="false">'
                      f'{icone(slug, glifo, "icone mini")} {escape(titulo)} <span>{len(questoes)}</span></button>')
        secoes.append(f"""<section class="bloco-questoes" data-materia="{slug}" style="--cor: {COR.get(slug, "#2357d9")}">
<h2 id="{slug}">{icone(slug, glifo, "icone mini")} {escape(titulo)}</h2>
<p class="teoria"><a href="{slug}.html">Rever a teoria de {escape(titulo)} →</a> · {len(questoes)} questões</p>
{chr(10).join(questoes)}
</section>""")
    return (f'<div class="filtro-materias" data-filtro role="group" aria-label="Filtrar por matéria">\n'
            + "\n".join(botoes) + "\n</div>\n<div class=\"banco\" data-banco>\n"
            + "\n".join(secoes) + "\n</div>")


def contar_banco(prefixo: str) -> int:
    return sum(len(q) for _, q in ler_banco(prefixo))


def tabela_bancas() -> str:
    por_slug = {p[0]: p for p in TODAS + APOSTILAS}
    contagens = {b[6]: dict(ler_banco(b[6])) for b in BANCAS}
    slugs = []
    for b in BANCAS:
        for s, _ in ler_banco(b[6]):
            if s not in slugs:
                slugs.append(s)
    cartoes = "\n".join(cartao_extra(b[:6], f"{contar_banco(b[6])} questões", "") for b in BANCAS)
    cartoes += "\n" + cartao_extra(PROVAS, "Links oficiais", "")
    linhas = []
    for s in slugs:
        celulas = []
        for b in BANCAS:
            n = len(contagens[b[6]].get(s, []))
            celulas.append(f'<td class="sim"><a href="{b[0]}.html#{s}">{n}</a></td>' if n else '<td class="nao">–</td>')
        linhas.append(f'<tr><td><a href="{s}.html">{escape(por_slug[s][2])}</a></td>{"".join(celulas)}</tr>')
    cab = "".join(f"<th>{escape(b[2].replace('Questões estilo ', ''))}</th>" for b in BANCAS)
    return (f'<div class="grade">\n{cartoes}\n</div>\n<h2>Questões por matéria</h2>\n'
            f'<p>Toque no número para abrir só as questões daquela matéria.</p>\n'
            f'<table class="matriz">\n<tr><th>Matéria</th>{cab}</tr>\n' + "\n".join(linhas) + "\n</table>")


def cartao_extra(item, rodape: str, prefixo: str) -> str:
    """Cartão de página que não conta como caderno estudado (sem data-slug)."""
    slug, glifo, titulo, resumo, _, termos = item
    return f"""  <a class="cartao" href="{prefixo}{slug}.html" data-termos="{escape(termos)}" style="--cor: {COR.get(slug, "#2357d9")}">
    {icone(slug, glifo)}
    <h3>{escape(titulo)}</h3>
    <p>{escape(resumo)}</p>
    <span class="rodape"><span>{escape(rodape)}</span></span>
  </a>"""


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
    total_questoes += sum(contar_banco(b[6]) for b in BANCAS)
    cartoes_questoes = "\n".join(
        [cartao_extra(b[:6], f"{contar_banco(b[6])} questões · {b[4]}", "cadernos/") for b in BANCAS]
        + [cartao_extra(PROVAS, "Links oficiais", "cadernos/")])
    corpo = f"""<main class="container" id="conteudo">
  <section class="hero">
    <div class="hero-texto">
      <p class="sobretitulo">Gratuito · {len(CADERNOS)} cadernos de matemática · {len(APOSTILAS)} apostilas · {total_questoes} questões comentadas</p>
      <h1>Estude para concursos <mark>sem perder tempo.</mark></h1>
      <p>Matemática com atalhos de prova e uma imersão completa para PM-SP, GCM São Paulo,
      Polícia Federal e Perito Criminal Federal: o que cai, em que ordem estudar e apostilas de todas as matérias.</p>
      <div class="acoes">
        <a class="botao" href="cadernos/imersao.html">Começar a imersão</a>
        <a class="botao secundario" href="#cadernos">Cadernos de matemática</a>
      </div>
    </div>
    <div class="hero-arte" aria-hidden="true">
      <div class="amostra">
        <span class="amostra-num">Questão · Porcentagem</span>
        <p>Um produto de R$ 200 sobe 10% e depois cai 10%. O preço final é:</p>
        <span class="amostra-alt"><b>A</b>R$ 200</span>
        <span class="amostra-alt certa"><b>B</b>R$ 198</span>
        <span class="amostra-alt"><b>C</b>R$ 202</span>
        <span class="amostra-atalho"><strong>Atalho:</strong> 200 × 1,1 × 0,9 = 198</span>
      </div>
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
      <a href="cadernos/erros.html"><strong data-estat="erros">0</strong><span>erros para revisar hoje</span></a>
    </div>
  <details class="guardar-progresso">
  <summary>Guardar o progresso ou levar para outro aparelho</summary>
  {BACKUP}
  </details>
  </section>

  <input class="busca" id="busca" type="search" data-indice="assets/busca.json" placeholder="Buscar em todo o site (ex.: PF, crase, Bhaskara, habeas corpus…)" aria-label="Buscar em todo o site">
  <p class="sem-resultado" hidden>Nada encontrado. Tente outra palavra.</p>
  <section class="resultados-busca" aria-live="polite" hidden></section>

  <section class="grupo-cadernos destaque-imersao">
    <h2>Imersão: escolha seu concurso <small>Cada guia traz o mapa das matérias, a ordem de estudo e um plano semana a semana.</small></h2>
    <div class="grade concursos">
{cartoes_concursos}
    </div>
  </section>

  <section class="grupo-cadernos" id="questoes">
    <h2>Banco de questões <small>Separadas por banca e por matéria, com figuras, gráficos, tabelas e código.</small></h2>
    <div class="grade">
{cartoes_questoes}
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


def data_git(*caminhos: Path) -> str:
    """Data do último commit que mexeu nos arquivos (AAAA-MM-DD); hoje, se não houver git."""
    try:
        saida = subprocess.run(["git", "log", "-1", "--format=%cs", "--", *map(str, caminhos)],
                               cwd=RAIZ, capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        saida = ""
    return saida or date.today().isoformat()


def gerar_sitemap() -> None:
    def fontes(slug: str):
        lista = [SRC / f"{slug}.html"]
        if slug in SLUGS_BANCAS:
            lista += sorted(QUESTOES_SRC.glob(f"{SLUGS_BANCAS[slug][6]}-*.html"))
        return lista
    entradas = [("", data_git(SRC, QUESTOES_SRC, RAIZ / "build.py"))]
    entradas += [(f"cadernos/{c[0]}.html", data_git(*fontes(c[0])))
                 for c in TODAS + PAGINAS_IMERSAO + INSTITUCIONAIS]
    urls = "\n".join(
        f"  <url><loc>{URL_BASE}{c}</loc><lastmod>{d}</lastmod></url>" for c, d in entradas
    )
    (RAIZ / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n</urlset>\n", encoding="utf-8")


class LeitorBusca(HTMLParser):
    """Separa o texto do artigo de uma página gerada em trechos, um por título h2."""
    PULAR = {"script", "style", "svg", "button", "figure"}
    VAZIOS = {"br", "img", "input", "meta", "link", "hr", "source", "wbr", "col"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pilha = []          # tags abertas dentro do artigo
        self.no_artigo = False
        self.pular = 0
        self.no_h2 = False
        self.titulo_h2 = []
        self.n_h2 = 0
        self.trechos = [["", "", []]]   # [id, título, partes de texto]

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if not self.no_artigo:
            if tag == "article" and "caderno" in (a.get("class") or ""):
                self.no_artigo = True
            return
        if tag in self.VAZIOS:
            return
        self.pilha.append(tag)
        classes = a.get("class") or ""
        if self.pular or tag in self.PULAR or "rodape-caderno" in classes or "cabeca-caderno" in classes \
                or "filtro-materias" in classes or "sumario" in classes:
            self.pular += 1
            return
        if tag == "h2":
            self.n_h2 += 1
            self.no_h2 = True
            self.titulo_h2 = []
            self.trechos.append([a.get("id") or f"secao-{self.n_h2}", "", []])
        elif tag in ("p", "li", "td", "th", "h3", "h4", "summary", "div", "tr"):
            self.trechos[-1][2].append(" ")

    def handle_endtag(self, tag):
        if not self.no_artigo or tag in self.VAZIOS:
            return
        if tag == "article" and not self.pilha:
            self.no_artigo = False
            return
        if not self.pilha:
            return
        self.pilha.pop()
        if self.pular:
            self.pular -= 1
            return
        if tag == "h2" and self.no_h2:
            self.no_h2 = False
            self.trechos[-1][1] = " ".join("".join(self.titulo_h2).split())

    def handle_data(self, dados):
        if not self.no_artigo or self.pular:
            return
        if self.no_h2:
            self.titulo_h2.append(dados)
        else:
            self.trechos[-1][2].append(dados)


def gerar_indice_busca() -> None:
    """Grava assets/busca.json: um trecho por seção de cada página, para a busca da página inicial."""
    itens = []
    paginas = TODAS + PAGINAS_IMERSAO + FERRAMENTAS + INSTITUCIONAIS
    for slug, _, titulo, *_ in paginas:
        if slug == "erros":
            continue
        leitor = LeitorBusca()
        leitor.feed((SAIDA / f"{slug}.html").read_text(encoding="utf-8"))
        for ancora, titulo_h2, partes in leitor.trechos:
            texto = " ".join("".join(partes).split())
            if not texto and not titulo_h2:
                continue
            itens.append({"p": titulo, "h": titulo_h2,
                          "u": f"cadernos/{slug}.html" + (f"#{ancora}" if ancora else ""), "t": texto})
    (RAIZ / "assets" / "busca.json").write_text(
        json.dumps(itens, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def gerar_404() -> None:
    corpo = f"""<main class="container pagina-404" id="conteudo">
  <p class="sobretitulo">Erro 404</p>
  <h1>Esta página não existe.</h1>
  <p>O endereço pode ter mudado ou ter sido digitado com algum erro. Procure o assunto na busca ou volte ao início.</p>
  <div class="acoes">
    <a class="botao" href="{CAMINHO_SITE}index.html#busca">Buscar no site</a>
    <a class="botao secundario" href="{CAMINHO_SITE}index.html">Ir para o início</a>
    <a class="botao secundario" href="{CAMINHO_SITE}cadernos/questoes.html">Banco de questões</a>
  </div>
</main>"""
    html = pagina(f"Página não encontrada · {SITE}", "Página não encontrada.", corpo, CAMINHO_SITE,
                  "404.html", "404", "Página não encontrada")
    (RAIZ / "404.html").write_text(html, encoding="utf-8")


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
    for item in [IMERSAO] + PAGINAS_QUESTOES + FERRAMENTAS + INSTITUCIONAIS:
        gerar_caderno(item)
    gerar_inicio()
    gerar_404()
    gerar_sitemap()
    gerar_indice_busca()
    total = len(TODAS) + len(PAGINAS_IMERSAO) + len(FERRAMENTAS) + len(INSTITUCIONAIS)
    print(f"Geradas {total} páginas, index.html, 404.html, sitemap.xml e assets/busca.json")


if __name__ == "__main__":
    main()
