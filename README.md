# Aprenda Matemática

Site gratuito para concursos: cadernos de matemática com atalhos para ganhar tempo na prova e uma **imersão** para PM-SP (Soldado), GCM São Paulo, Polícia Federal (Agente, Escrivão e Papiloscopista) e Perito Criminal Federal (Informática), com apostilas de todas as matérias.

## Cadernos

| Comece aqui | Cadernos |
|---|---|
| Estratégias de prova · Trilhas por banca e área · Formulário de bolso · Meu caderno de erros | Aritmética e divisibilidade · Frações e decimais · Porcentagem · Razão e proporção · Regra de três · Juros simples e compostos · Equações e sistemas · Funções · Sequências, PA e PG · Geometria plana e espacial · Estatística básica · Análise combinatória · Probabilidade · Raciocínio lógico |

## Imersão concursos

| Guias de concurso | Apostilas |
|---|---|
| Imersão (visão geral) · PM-SP · GCM São Paulo · Polícia Federal · Perito Criminal Federal (Área 3) | Língua Portuguesa · Informática · Direito Constitucional · Direito Administrativo · Direito Penal · Processo Penal · Legislação Penal Especial · Direitos Humanos · História · Geografia · Atualidades e Realidade de SP · Contabilidade · Criminalística · Redes e Segurança · Computação Forense · Programação, SO e Dados |

Cada guia traz a ficha do concurso, o que cai, um **mapa de matérias** na ordem de estudo (com o progresso de quem marca as páginas como estudadas), um plano semana a semana e a estratégia de prova da banca. As listas de matérias de cada concurso ficam em `MATERIAS`, no `build.py`, e o mapa entra no lugar do comentário `<!-- mapa -->` do guia. As apostilas aceitam questões de múltipla escolha (5 alternativas) e itens Certo ou Errado (2 alternativas, Certo primeiro).

Todo o conteúdo é original e livre para estudo. Os guias seguem os editais de 2025; confira sempre o edital do seu concurso.

## Banco de questões

Questões originais separadas por banca e por matéria, muitas com figura (SVG), gráfico, tabela ou código: uma página para o estilo **VUNESP** (PM-SP e GCM, 5 alternativas) e outra para o estilo **CEBRASPE** (PF e Perito, Certo ou Errado), com filtro por matéria e placar da matéria filtrada. A página **Provas oficiais** mostra onde achar as provas e os gabaritos oficiais de cada banca e como usá-los num simulado. Nenhuma prova ou apostila de terceiros é copiada para o site.

As questões ficam em `src/questoes/<banca>-*.html`, cada matéria dentro de `<section data-materia="slug">`, e cada questão tem um `data-id` fixo (ex.: `v-geometria-03`) para o caderno de erros não se perder quando novas questões entrarem. A ordem das matérias de cada banco fica em `ORDEM_BANCO`, no `build.py`.

- **Caderno de erros com revisão espaçada:** toda questão errada em qualquer caderno é guardada automaticamente (no navegador). Cada acerto agenda a próxima revisão para 1, 3 e 7 dias depois; quem acerta na revisão de 7 dias tira a questão da lista, e um novo erro recomeça a contagem.
- **Backup do progresso:** na página inicial e no caderno de erros, o aluno exporta o progresso para um arquivo `.json` e importa em outro aparelho.
- **Busca em todo o site:** o `build.py` gera `assets/busca.json`, com um trecho de texto por seção (título `h2`) de cada página. A busca da página inicial só baixa esse arquivo quando o aluno clica no campo; o ícone de lupa do topo leva para ela.
- **Trilhas:** ordem de estudo e prioridades por estilo de banca (Cebraspe, FGV, FCC, Vunesp, Cesgranrio) e por área do cargo.
- **SEO:** cada página tem descrição, link canônico, Open Graph com imagem de compartilhamento (`assets/og-imagem.png`, 1200 × 630) e dados estruturados (schema.org). O `build.py` também gera o `sitemap.xml`, com a data do último commit de cada página, e a `404.html`, que o GitHub Pages mostra quando o endereço não existe.

## Como funciona

O site é estático (HTML, CSS e JavaScript puro) e roda direto no GitHub Pages. A única biblioteca é o [KaTeX](https://katex.org) (licença MIT), copiado em `assets/vendor/katex/` para desenhar as fórmulas sem depender de CDN. As fontes Inter (texto) e Fraunces (títulos), ambas com licença SIL OFL, ficam em `assets/vendor/fontes/`. Se ele não carregar, a fórmula aparece em texto simples.

```
src/cadernos/*.html   conteúdo de cada caderno (só o miolo, em HTML simples)
src/questoes/*.html   questões do banco, separadas por banca e por matéria
build.py              monta as páginas finais com menu, cabeçalho e rodapé
cadernos/*.html       páginas geradas (não edite à mão)
index.html            página inicial gerada
assets/css, assets/js estilo e interações (tema escuro, menu em gaveta no celular, questões, progresso, busca)
```

### Editar ou criar um caderno

1. Edite o arquivo em `src/cadernos/`. Para um caderno novo, crie o arquivo e acrescente uma linha na lista `CADERNOS` em `build.py`.
2. Rode `python3 build.py`.
3. Abra `index.html` no navegador para conferir.

Blocos disponíveis no conteúdo:

```html
<div class="caixa atalho"><span class="rotulo">Atalho</span><p>…</p></div>
<div class="caixa pegadinha"><span class="rotulo">Pegadinha</span><p>…</p></div>
<div class="caixa dica"><span class="rotulo">Dica</span><p>…</p></div>
<span class="formula" data-tex="M = C\,(1 + i)^t">M = C × (1 + i)ᵗ</span>   <!-- data-tex em LaTeX; o texto é o reserva -->
<figure class="figura"><svg …>…</svg><figcaption>Legenda</figcaption></figure>

<details class="exemplo"><summary>Enunciado do exemplo</summary>
<div class="resolucao"><p class="passo">…</p><p class="resposta-final">Resposta: …</p></div></details>

<div class="questao" data-correta="c">
  <p class="enunciado">Pergunta</p>
  <ol class="alternativas"><li>A</li><li>B</li><li>C</li><li>D</li><li>E</li></ol>
  <div class="explicacao"><p>Por que a C está certa.</p></div>
</div>
```

## Publicar no GitHub Pages

Em **Settings → Pages**, escolha *Deploy from a branch*, branch `main`, pasta `/ (root)`. O site fica em `https://carlosgabriel-ux.github.io/APRENDA-MATEMATICA/`.

Para aparecer mais rápido no Google, cadastre o site no [Google Search Console](https://search.google.com/search-console) e envie o endereço do `sitemap.xml`.

## Contribuir

Encontrou um erro ou quer sugerir um assunto? Abra uma *issue* ou um *pull request*.
