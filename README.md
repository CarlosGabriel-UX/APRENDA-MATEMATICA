# Aprenda Matemática

Site gratuito de matemática para concursos: teoria enxuta, atalhos para ganhar tempo na prova, pegadinhas comuns das bancas e questões com resolução comentada.

## Cadernos

| Comece aqui | Cadernos |
|---|---|
| Estratégias de prova · Trilhas por banca e área · Formulário de bolso · Meu caderno de erros | Aritmética e divisibilidade · Frações e decimais · Porcentagem · Razão e proporção · Regra de três · Juros simples e compostos · Equações e sistemas · Funções · Sequências, PA e PG · Geometria plana e espacial · Estatística básica · Análise combinatória · Probabilidade · Raciocínio lógico |

Todo o conteúdo é original e livre para estudo.

- **Caderno de erros:** toda questão errada em qualquer caderno é guardada automaticamente (no navegador) e sai da lista quando o aluno acerta.
- **Trilhas:** ordem de estudo e prioridades por estilo de banca (Cebraspe, FGV, FCC, Vunesp, Cesgranrio) e por área do cargo.
- **SEO:** cada página tem descrição, link canônico, Open Graph e dados estruturados (schema.org). O `build.py` também gera o `sitemap.xml`.

## Como funciona

O site é estático (HTML, CSS e JavaScript puro) e roda direto no GitHub Pages. A única biblioteca é o [KaTeX](https://katex.org) (licença MIT), copiado em `assets/vendor/katex/` para desenhar as fórmulas sem depender de CDN. Se ele não carregar, a fórmula aparece em texto simples.

```
src/cadernos/*.html   conteúdo de cada caderno (só o miolo, em HTML simples)
build.py              monta as páginas finais com menu, cabeçalho e rodapé
cadernos/*.html       páginas geradas (não edite à mão)
index.html            página inicial gerada
assets/css, assets/js estilo e interações (tema escuro, questões, progresso, busca)
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
