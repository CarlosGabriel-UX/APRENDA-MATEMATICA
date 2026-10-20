/* Aprenda Matemática: interações do site (tema, questões, progresso, revisão, backup, busca). */
(function () {
  "use strict";

  var CHAVE_TEMA = "am-tema";
  var CHAVE_FEITOS = "am-cadernos-estudados";
  var CHAVE_ERROS = "am-caderno-de-erros";
  var CHAVE_FONTE = "am-tamanho-fonte";
  var CHAVE_ULTIMO = "am-ultimo-caderno";
  var CHAVE_RESPOSTAS = "am-respostas";
  var TAMANHOS = [100, 112.5, 125, 90];
  /* Revisão espaçada: depois de cada acerto, a questão volta em 1, 3 e 7 dias. */
  var INTERVALOS = [1, 3, 7];
  var DIA = 24 * 60 * 60 * 1000;

  function ler(chave, padrao) {
    try {
      var v = localStorage.getItem(chave);
      return v === null ? padrao : JSON.parse(v);
    } catch (e) {
      return padrao;
    }
  }
  function gravar(chave, valor) {
    try { localStorage.setItem(chave, JSON.stringify(valor)); } catch (e) { /* sem armazenamento */ }
  }

  /* ---------- tema claro/escuro ---------- */
  var raiz = document.documentElement;
  var ICONE_SOL = '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
    'stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6 6 6M18 18l1.4 1.4' +
    'M2.5 12h2M19.5 12h2M4.6 19.4 6 18M18 6l1.4-1.4"/></svg>';
  var ICONE_LUA = '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>';
  function aplicarTema(t) {
    raiz.setAttribute("data-theme", t);
    document.querySelectorAll(".botao-tema").forEach(function (b) {
      var rotulo = t === "dark" ? "Usar tema claro" : "Usar tema escuro";
      b.innerHTML = t === "dark" ? ICONE_SOL : ICONE_LUA;
      b.setAttribute("aria-label", rotulo);
      b.title = rotulo;
    });
  }

  /* ---------- tamanho da letra ---------- */
  function aplicarFonte(pct) {
    raiz.style.fontSize = pct === 100 ? "" : pct + "%";
    document.querySelectorAll(".botao-fonte").forEach(function (b) {
      b.setAttribute("aria-label", "Mudar o tamanho da letra (agora " + pct + "%)");
      b.title = "Tamanho da letra: " + pct + "%";
    });
  }
  var fonteSalva = ler(CHAVE_FONTE, 100);
  if (TAMANHOS.indexOf(fonteSalva) === -1) fonteSalva = 100;
  aplicarFonte(fonteSalva);
  var temaSalvo = ler(CHAVE_TEMA, null);
  var prefereEscuro = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  aplicarTema(temaSalvo || (prefereEscuro ? "dark" : "light"));

  document.addEventListener("DOMContentLoaded", function () {
    aplicarTema(raiz.getAttribute("data-theme"));
    aplicarFonte(fonteSalva);
    document.querySelectorAll(".botao-tema").forEach(function (b) {
      b.addEventListener("click", function () {
        var novo = raiz.getAttribute("data-theme") === "dark" ? "light" : "dark";
        aplicarTema(novo);
        gravar(CHAVE_TEMA, novo);
      });
    });
    document.querySelectorAll(".botao-fonte").forEach(function (b) {
      b.addEventListener("click", function () {
        fonteSalva = TAMANHOS[(TAMANHOS.indexOf(fonteSalva) + 1) % TAMANHOS.length];
        aplicarFonte(fonteSalva);
        gravar(CHAVE_FONTE, fonteSalva);
      });
    });

    montarMenu();

    embrulharTabelas();
    renderizarFormulas();
    lembrarUltimo();
    montarListaErros();
    montarSumario();
    montarQuestoes();
    montarFiltro();
    atualizarContagemErros();
    montarInicio();
    montarLeitura();
    montarProgresso();
    montarBusca();
    montarBackup();

    /* Ao imprimir, abre todas as resoluções. */
    window.addEventListener("beforeprint", function () {
      document.querySelectorAll("details.exemplo, details.sumario").forEach(function (d) { d.open = true; });
    });
  });

  /* ---------- menu lateral: no celular vira uma gaveta ---------- */
  function montarMenu() {
    var lateral = document.querySelector(".lateral");
    if (!lateral) return;
    var botao = document.querySelector(".botao-menu");
    var fundo = document.createElement("div");
    fundo.className = "fundo-menu";
    document.body.appendChild(fundo);
    var gaveta = window.matchMedia("(max-width: 900px)");
    function abrir(sim) {
      lateral.classList.toggle("aberta", sim);
      document.body.classList.toggle("menu-aberto", sim);
      if (botao) botao.setAttribute("aria-expanded", sim ? "true" : "false");
      if (sim && gaveta.matches) {
        var ativo = lateral.querySelector("a.ativo") || lateral.querySelector("a");
        if (ativo) { ativo.scrollIntoView({ block: "center" }); ativo.focus({ preventScroll: true }); }
      } else if (!sim && botao && gaveta.matches) {
        botao.focus({ preventScroll: true });
      }
    }
    if (botao) botao.addEventListener("click", function () { abrir(!lateral.classList.contains("aberta")); });
    fundo.addEventListener("click", function () { abrir(false); });
    var fechar = lateral.querySelector(".fechar-menu");
    if (fechar) fechar.addEventListener("click", function () { abrir(false); });
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && lateral.classList.contains("aberta")) abrir(false);
    });
    document.querySelectorAll(".abrir-menu").forEach(function (a) {
      a.addEventListener("click", function (ev) { ev.preventDefault(); abrir(true); });
    });
  }

  /* ---------- tabelas largas rolam de lado dentro de uma caixa ---------- */
  function embrulharTabelas() {
    document.querySelectorAll("article.caderno table").forEach(function (t) {
      if (t.parentNode.classList.contains("rolagem-tabela")) return;
      var caixa = document.createElement("div");
      caixa.className = "rolagem-tabela";
      t.parentNode.insertBefore(caixa, t);
      caixa.appendChild(t);
    });
  }

  /* ---------- fórmulas com KaTeX (o texto simples fica se o KaTeX não carregar) ---------- */
  function renderizarFormulas() {
    if (!window.katex) return;
    document.querySelectorAll(".formula[data-tex]").forEach(function (el) {
      try {
        window.katex.render(el.getAttribute("data-tex"), el, { displayMode: true, throwOnError: false });
        el.classList.add("renderizada");
      } catch (e) { /* mantém o texto original */ }
    });
  }

  /* ---------- "continue de onde parou" ---------- */
  var PAGINAS_SEM_HISTORICO = ["inicio", "erros", "sobre"];
  function lembrarUltimo() {
    var pagina = document.body.getAttribute("data-pagina");
    if (!pagina || PAGINAS_SEM_HISTORICO.indexOf(pagina) !== -1) return;
    gravar(CHAVE_ULTIMO, { slug: pagina, titulo: document.body.getAttribute("data-titulo") || "" });
  }

  /* ---------- painel da página inicial ---------- */
  function montarInicio() {
    var painel = document.querySelector(".painel");
    if (!painel) return;
    var ultimo = ler(CHAVE_ULTIMO, null);
    var link = painel.querySelector("[data-continuar]");
    if (ultimo && ultimo.slug && /^[a-z0-9-]+$/.test(ultimo.slug)) {
      link.href = "cadernos/" + ultimo.slug + ".html";
      link.querySelector(".titulo-continuar").textContent = ultimo.titulo || ultimo.slug;
      link.hidden = false;
    }
    var respostas = ler(CHAVE_RESPOSTAS, {});
    var ids = Object.keys(respostas || {});
    var certas = ids.filter(function (k) { return respostas[k] === 1; }).length;
    var feitos = ler(CHAVE_FEITOS, []);
    var estat = function (nome, valor) {
      var el = painel.querySelector('[data-estat="' + nome + '"]');
      if (el) el.textContent = valor;
    };
    estat("estudados", Array.isArray(feitos) ? feitos.length : 0);
    estat("resolvidas", ids.length);
    estat("acerto", ids.length ? Math.round(100 * certas / ids.length) + "%" : "–");
    estat("erros", lerPendentes().length);
  }

  /* ---------- barra de leitura e botão de voltar ao topo ---------- */
  function montarLeitura() {
    var barra = document.querySelector(".progresso-leitura > span");
    var topo = document.querySelector(".voltar-topo");
    var artigo = document.querySelector("article.caderno");
    if (!artigo && barra) barra.parentNode.remove();
    var agendado = false;
    function atualizar() {
      agendado = false;
      var y = window.scrollY || document.documentElement.scrollTop;
      if (artigo && barra) {
        var fim = artigo.offsetTop + artigo.offsetHeight - window.innerHeight;
        var pct = fim > 0 ? Math.min(100, Math.max(0, 100 * y / fim)) : 100;
        barra.style.width = pct + "%";
      }
      if (topo) topo.hidden = y < 700;
    }
    window.addEventListener("scroll", function () {
      if (!agendado) { agendado = true; window.requestAnimationFrame(atualizar); }
    }, { passive: true });
    if (topo) {
      topo.addEventListener("click", function () {
        window.scrollTo({ top: 0, behavior: "smooth" });
        var alvo = document.getElementById("conteudo");
        if (alvo) { alvo.setAttribute("tabindex", "-1"); alvo.focus({ preventScroll: true }); }
      });
    }
    atualizar();
  }

  /* ---------- sumário automático a partir dos h2 ---------- */
  function montarSumario() {
    var titulos = document.querySelectorAll("article.caderno h2");
    /* Os ids valem em toda página: os links da busca apontam para eles. */
    titulos.forEach(function (h, i) { if (!h.id) h.id = "secao-" + (i + 1); });
    var alvo = document.querySelector("[data-sumario]");
    if (!alvo) return;
    if (!titulos.length) { alvo.remove(); return; }
    var nav = document.createElement("nav");
    nav.setAttribute("aria-label", "Nesta página");
    var ol = document.createElement("ol");
    nav.appendChild(ol);
    titulos.forEach(function (h) {
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = "#" + h.id;
      a.textContent = h.textContent;
      li.appendChild(a);
      ol.appendChild(li);
    });
    alvo.appendChild(nav);
    /* No celular o sumário começa fechado para o texto aparecer logo. */
    if (window.matchMedia("(max-width: 700px)").matches) alvo.open = false;
    ol.addEventListener("click", function (ev) {
      if (ev.target.closest("a") && window.matchMedia("(max-width: 700px)").matches) alvo.open = false;
    });
  }

  /* ---------- caderno de erros ---------- */
  function lerErros() {
    var e = ler(CHAVE_ERROS, []);
    return Array.isArray(e) ? e : [];
  }
  /* Questões antigas, gravadas antes da revisão espaçada, não têm data: valem para hoje. */
  function vence(e) { return !e.proxima || e.proxima <= Date.now(); }
  function lerPendentes() { return lerErros().filter(vence); }
  function guardarErro(item) {
    var erros = lerErros().filter(function (e) { return e.id !== item.id; });
    item.etapa = 0;
    item.proxima = Date.now();
    erros.push(item);
    gravar(CHAVE_ERROS, erros);
    atualizarContagemErros();
  }
  /* Acerto numa questão do caderno de erros: agenda a próxima revisão ou tira da lista.
     Devolve null (não estava na lista), 0 (saiu da lista) ou os dias até a próxima revisão. */
  function revisarAcerto(id) {
    var erros = lerErros();
    var e = erros.filter(function (x) { return x.id === id; })[0];
    if (!e) return null;
    var etapa = e.etapa || 0;
    var dias = 0;
    if (etapa >= INTERVALOS.length) {
      erros = erros.filter(function (x) { return x.id !== id; });
    } else {
      dias = INTERVALOS[etapa];
      e.etapa = etapa + 1;
      e.proxima = Date.now() + dias * DIA;
    }
    gravar(CHAVE_ERROS, erros);
    atualizarContagemErros();
    return dias;
  }
  function reiniciarRevisao(id) {
    var erros = lerErros();
    erros.forEach(function (e) { if (e.id === id) { e.etapa = 0; e.proxima = Date.now(); } });
    gravar(CHAVE_ERROS, erros);
  }
  function atualizarContagemErros() {
    var n = lerPendentes().length;
    document.querySelectorAll("[data-contagem-erros]").forEach(function (el) {
      el.textContent = n ? String(n) : "";
      el.hidden = !n;
    });
  }

  /* Na página do caderno de erros, monta as questões salvas antes de ativá-las. */
  function montarListaErros() {
    var alvo = document.querySelector("[data-lista-erros]");
    if (!alvo) return;
    var todos = lerErros();
    var erros = todos.filter(vence);
    var agendados = todos.filter(function (e) { return !vence(e); })
      .sort(function (a, b) { return a.proxima - b.proxima; });
    var htmlAgenda = "";
    if (agendados.length) {
      htmlAgenda = '<details class="agenda-revisao"><summary>Próximas revisões <span>' + agendados.length +
        "</span></summary><ul>";
      agendados.forEach(function (e) {
        var caixa = document.createElement("div");
        caixa.innerHTML = e.html;
        var enunciado = caixa.querySelector(".enunciado");
        var texto = (enunciado ? enunciado.textContent : "").trim();
        if (texto.length > 110) texto = texto.slice(0, 107) + "…";
        var li = document.createElement("li");
        var quando = document.createElement("strong");
        quando.textContent = new Date(e.proxima).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
        li.appendChild(quando);
        li.appendChild(document.createTextNode(" " + e.titulo + (texto ? ": " + texto : "")));
        htmlAgenda += li.outerHTML;
      });
      htmlAgenda += "</ul></details>";
    }
    if (!erros.length) {
      alvo.innerHTML = (todos.length
        ? '<div class="caixa dica"><span class="rotulo">Nada para revisar hoje</span>' +
          "<p>Todas as questões que você errou estão agendadas. Elas voltam aqui no dia marcado abaixo.</p></div>"
        : '<div class="caixa nota"><span class="rotulo">Nenhum erro guardado</span>' +
          "<p>Quando você errar uma questão em qualquer caderno, ela aparece aqui automaticamente. " +
          "Cada acerto agenda uma nova revisão (em 1, 3 e 7 dias); depois disso, ela sai da lista.</p></div>") + htmlAgenda;
      return;
    }
    var grupos = {};
    var ordem = [];
    erros.forEach(function (e) {
      if (!grupos[e.slug]) { grupos[e.slug] = { titulo: e.titulo, itens: [] }; ordem.push(e.slug); }
      grupos[e.slug].itens.push(e);
    });
    var html = '<p class="resumo-erros"><span>Você tem <strong>' + erros.length + "</strong> questão(ões) para revisar hoje." +
      (agendados.length ? " Outras " + agendados.length + " estão agendadas." : "") + "</span>" +
      '<button type="button" class="botao secundario limpar-erros">Limpar tudo</button></p>' + htmlAgenda;
    ordem.forEach(function (slug) {
      var g = grupos[slug];
      html += '<h2>' + g.titulo + "</h2>";
      html += '<p><a href="' + encodeURIComponent(slug) + '.html">Rever a teoria deste caderno →</a></p>';
      g.itens.forEach(function (e) { html += e.html; });
    });
    alvo.innerHTML = html;
    var questoes = alvo.querySelectorAll(".questao");
    var lista = [];
    ordem.forEach(function (slug) { lista = lista.concat(grupos[slug].itens); });
    questoes.forEach(function (q, i) { q.setAttribute("data-id", lista[i].id); });
    alvo.querySelector(".limpar-erros").addEventListener("click", function () {
      if (!window.confirm("Apagar todas as questões do caderno de erros?")) return;
      gravar(CHAVE_ERROS, []);
      atualizarContagemErros();
      window.location.reload();
    });
  }

  /* ---------- questões de múltipla escolha ---------- */
  function montarQuestoes() {
    var questoes = document.querySelectorAll(".questao");
    if (!questoes.length) return;
    var acertos = 0, respondidas = 0, total = questoes.length;
    var letras = "abcde";
    var pagina = document.body.getAttribute("data-pagina") || "";
    var tituloPagina = document.body.getAttribute("data-titulo") || document.title;

    var placar = document.createElement("div");
    placar.className = "placar";
    placar.innerHTML = '<span class="texto"></span><button type="button" class="botao secundario refazer">Refazer questões</button>';
    var ultima = questoes[questoes.length - 1];
    var ancora = ultima.closest("[data-banco]") || ultima;
    ancora.parentNode.insertBefore(placar, ancora.nextSibling);

    var primeira = questoes[0];
    var dica = document.createElement("p");
    dica.className = "dica-teclado";
    dica.innerHTML = "Dica: responda com as teclas <kbd>A</kbd> a <kbd>E</kbd>. Vale a questão destacada, a mais próxima do centro da tela.";
    primeira.parentNode.insertBefore(dica, primeira);

    var flutuante = document.createElement("a");
    flutuante.className = "placar-flutuante";
    flutuante.href = "#" + (primeira.id || (primeira.id = "primeira-questao"));
    flutuante.setAttribute("aria-label", "Ir para as questões");
    document.body.appendChild(flutuante);

    /* No banco de questões, o placar conta só as questões da matéria filtrada. */
    function atualizarPlacar() {
      var visiveis = Array.prototype.filter.call(questoes, function (q) { return !q.closest("[hidden]"); });
      total = visiveis.length;
      respondidas = visiveis.filter(function (q) { return q.classList.contains("respondida"); }).length;
      acertos = visiveis.filter(function (q) { return q.classList.contains("acertou"); }).length;
      placar.querySelector(".texto").textContent =
        "Questões: " + respondidas + "/" + total + " respondidas · " + acertos + " acerto(s)";
      flutuante.innerHTML = "Questões <strong>" + acertos + "✓</strong> · " + respondidas + "/" + total;
      flutuante.hidden = respondidas === 0; /* só aparece depois da primeira resposta */
    }

    function questaoAtiva() {
      var meio = window.innerHeight / 2, melhor = null, menor = Infinity;
      questoes.forEach(function (q) {
        if (q.classList.contains("respondida") || q.closest("[hidden]")) return;
        var r = q.getBoundingClientRect();
        if (r.bottom < 0 || r.top > window.innerHeight) return;
        var d = Math.abs((r.top + r.bottom) / 2 - meio);
        if (d < menor) { menor = d; melhor = q; }
      });
      return melhor;
    }
    function marcarAtiva() {
      var a = questaoAtiva();
      questoes.forEach(function (q) { q.classList.toggle("ativa", q === a); });
    }
    window.addEventListener("scroll", function () { window.requestAnimationFrame(marcarAtiva); }, { passive: true });
    document.addEventListener("keydown", function (ev) {
      if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
      var alvo = ev.target;
      if (alvo && (alvo.tagName === "INPUT" || alvo.tagName === "TEXTAREA" || alvo.isContentEditable)) return;
      var letra = (ev.key || "").toLowerCase();
      if (letras.indexOf(letra) === -1 || letra.length !== 1) return;
      var q = questaoAtiva();
      if (!q) return;
      var b = q.querySelector('ol.alternativas button[data-letra="' + letra + '"]');
      if (b) { ev.preventDefault(); b.click(); b.focus({ preventScroll: true }); }
    });

    questoes.forEach(function (q, idx) {
      var id = q.getAttribute("data-id") || (pagina + "#" + (idx + 1));
      var original = q.outerHTML;
      var correta = (q.getAttribute("data-correta") || "").toLowerCase();
      var num = document.createElement("div");
      num.className = "num";
      var secao = q.closest("section[data-materia]");
      num.textContent = "Questão " + (secao
        ? Array.prototype.indexOf.call(secao.querySelectorAll(".questao"), q) + 1 : idx + 1);
      q.insertBefore(num, q.firstChild);

      var veredito = document.createElement("p");
      veredito.className = "veredito";
      veredito.setAttribute("role", "status");
      var exp = q.querySelector(".explicacao");
      if (exp) exp.insertBefore(veredito, exp.firstChild);

      var itens = q.querySelectorAll("ol.alternativas > li");
      if (itens.length === 2) q.classList.add("ce"); /* item Certo ou Errado */
      itens.forEach(function (li, i) {
        var botao = document.createElement("button");
        botao.type = "button";
        botao.dataset.letra = letras[i];
        botao.innerHTML = '<span class="letra">' + letras[i].toUpperCase() + "</span><span>" + li.innerHTML + "</span>";
        li.innerHTML = "";
        li.appendChild(botao);
        botao.addEventListener("click", function () {
          if (q.classList.contains("respondida")) return;
          q.classList.add("respondida");
          respondidas++;
          var acertou = botao.dataset.letra === correta;
          if (acertou) acertos++;
          q.querySelectorAll("ol.alternativas button").forEach(function (b) {
            b.disabled = true;
            if (b.dataset.letra === correta) b.classList.add("certa");
          });
          if (!acertou) botao.classList.add("errada");
          q.classList.add(acertou ? "acertou" : "errou");
          var respostas = ler(CHAVE_RESPOSTAS, {}) || {};
          respostas[id] = acertou ? 1 : 0;
          gravar(CHAVE_RESPOSTAS, respostas);
          window.setTimeout(marcarAtiva, 50);
          veredito.className = "veredito " + (acertou ? "ok" : "nao");
          var texto = acertou
            ? (q.classList.contains("ce") ? "Correto! O item está " + (correta === "a" ? "Certo" : "Errado") + "."
              : "Correto! Alternativa " + correta.toUpperCase() + ".")
            : (q.classList.contains("ce")
              ? "Não foi dessa vez. O item está " + (correta === "a" ? "Certo" : "Errado") + "."
              : "Não foi dessa vez. A resposta é a alternativa " + correta.toUpperCase() + ".");
          if (acertou) {
            var dias = revisarAcerto(id);
            if (dias === 0) texto += " Revisão concluída: ela saiu do seu caderno de erros.";
            else if (dias) texto += " Ela volta para revisão em " + dias + (dias === 1 ? " dia." : " dias.");
          } else if (pagina !== "erros") {
            guardarErro({ id: id, slug: pagina, titulo: tituloPagina, html: original });
            texto += " Guardada no seu caderno de erros.";
          } else {
            reiniciarRevisao(id);
            texto += " A revisão recomeça: ela continua na lista de hoje.";
          }
          veredito.textContent = texto;
          atualizarPlacar();
        });
      });
    });

    placar.querySelector(".refazer").addEventListener("click", function () {
      questoes.forEach(function (q) {
        if (q.closest("[hidden]")) return;
        q.classList.remove("respondida", "acertou", "errou");
        q.querySelectorAll("ol.alternativas button").forEach(function (b) {
          b.disabled = false;
          b.classList.remove("certa", "errada");
        });
      });
      atualizarPlacar();
      var primeiraVisivel = Array.prototype.filter.call(questoes, function (q) { return !q.closest("[hidden]"); })[0];
      if (primeiraVisivel) primeiraVisivel.scrollIntoView({ behavior: "smooth", block: "center" });
      window.setTimeout(marcarAtiva, 400);
    });

    document.addEventListener("am-filtro", function () { atualizarPlacar(); marcarAtiva(); });
    atualizarPlacar();
    marcarAtiva();
  }

  /* ---------- banco de questões: filtro por matéria ---------- */
  function montarFiltro() {
    var filtro = document.querySelector("[data-filtro]");
    if (!filtro) return;
    var botoes = filtro.querySelectorAll("button[data-materia]");
    var secoes = document.querySelectorAll("[data-banco] section[data-materia]");
    function aplicar(materia, rolar) {
      var existe = !materia || Array.prototype.some.call(secoes, function (s) { return s.getAttribute("data-materia") === materia; });
      if (!existe) materia = "";
      secoes.forEach(function (s) { s.hidden = !!materia && s.getAttribute("data-materia") !== materia; });
      botoes.forEach(function (b) {
        var ativo = b.getAttribute("data-materia") === materia;
        b.classList.toggle("ativo", ativo);
        b.setAttribute("aria-pressed", ativo ? "true" : "false");
        /* Deixa o botão ativo à vista na faixa que rola de lado. */
        if (ativo) filtro.scrollLeft = b.offsetLeft - (filtro.clientWidth - b.offsetWidth) / 2;
      });
      document.dispatchEvent(new CustomEvent("am-filtro"));
      if (rolar) filtro.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    botoes.forEach(function (b) {
      b.addEventListener("click", function () {
        var materia = b.getAttribute("data-materia");
        if (window.history && history.replaceState) {
          history.replaceState(null, "", materia ? "#" + materia : window.location.pathname);
        }
        aplicar(materia, true);
      });
    });
    var inicial = decodeURIComponent((window.location.hash || "").slice(1));
    if (inicial) {
      aplicar(inicial, false);
      window.setTimeout(function () { filtro.scrollIntoView({ block: "start" }); }, 0);
    }
  }

  /* ---------- progresso (cadernos marcados como estudados) ---------- */
  function montarProgresso() {
    var feitos = ler(CHAVE_FEITOS, []);
    if (!Array.isArray(feitos)) feitos = [];

    function marcarVisual() {
      document.querySelectorAll("[data-slug]").forEach(function (el) {
        var slug = el.getAttribute("data-slug");
        var ok = feitos.indexOf(slug) !== -1;
        var noMenu = el.querySelector(".feito");
        if (noMenu) noMenu.textContent = ok ? "✓" : "";
        var noCartao = el.querySelector(".ok");
        if (noCartao) noCartao.textContent = ok ? "✓ estudado" : "";
      });
      var barra = document.querySelector(".progresso-geral");
      if (barra) {
        var naMatematica = Array.prototype.slice.call(
          document.querySelectorAll('[data-bloco="matematica"] .cartao[data-slug]'));
        var total = naMatematica.length;
        var n = naMatematica.filter(function (c) { return feitos.indexOf(c.getAttribute("data-slug")) !== -1; }).length;
        barra.querySelector(".valor").textContent = n + " de " + total + " cadernos de matemática estudados";
        barra.querySelector(".barra > span").style.width = (total ? (100 * n / total) : 0) + "%";
      }
      /* Concursos: quantas matérias do plano já foram estudadas. */
      document.querySelectorAll(".cartao.concurso[data-materias]").forEach(function (c) {
        var lista = c.getAttribute("data-materias").split(",");
        var feitas = lista.filter(function (s) { return feitos.indexOf(s) !== -1; }).length;
        var alvo = c.querySelector(".ok-concurso");
        if (alvo) alvo.textContent = feitas ? feitas + "/" + lista.length + " ✓" : "";
        c.style.setProperty("--progresso", (100 * feitas / lista.length) + "%");
      });
      document.querySelectorAll("[data-mapa]").forEach(function (m) {
        var itens = m.querySelectorAll("li[data-slug]");
        var feitas = Array.prototype.filter.call(itens, function (li) {
          var ok = feitos.indexOf(li.getAttribute("data-slug")) !== -1;
          li.classList.toggle("estudada", ok);
          return ok;
        }).length;
        var txt = m.querySelector(".mapa-progresso");
        if (txt) txt.textContent = feitas + " de " + itens.length + " matérias estudadas" +
          (feitas === itens.length ? ". Plano completo: agora é revisão e questões!" : "");
        m.style.setProperty("--progresso", (100 * feitas / itens.length) + "%");
      });
    }

    var botao = document.querySelector(".marcar-estudado");
    if (botao) {
      var slug = botao.getAttribute("data-alvo");
      var pintar = function () {
        var ok = feitos.indexOf(slug) !== -1;
        botao.textContent = ok ? "✓ Caderno estudado" : "Marcar como estudado";
        botao.classList.toggle("feito", ok);
      };
      botao.addEventListener("click", function () {
        var i = feitos.indexOf(slug);
        if (i === -1) feitos.push(slug); else feitos.splice(i, 1);
        gravar(CHAVE_FEITOS, feitos);
        pintar();
        marcarVisual();
      });
      pintar();
    }
    marcarVisual();
  }

  /* ---------- busca: filtra os cartões e procura dentro de todas as páginas ---------- */
  function normalizar(s) {
    return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }
  function escaparHtml(s) {
    return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
  }
  /* Trecho do texto em volta do primeiro termo encontrado, com os termos marcados. */
  function trecho(texto, termos) {
    var norm = normalizar(texto);
    var pos = norm.indexOf(termos[0]);
    var ini = Math.max(0, pos - 60);
    var fim = Math.min(texto.length, ini + 180);
    var pedaco = texto.slice(ini, fim);
    var pedacoNorm = norm.slice(ini, fim);
    var marcas = [];
    termos.forEach(function (t) {
      var i = pedacoNorm.indexOf(t);
      while (i !== -1) { marcas.push([i, i + t.length]); i = pedacoNorm.indexOf(t, i + t.length); }
    });
    marcas.sort(function (a, b) { return a[0] - b[0]; });
    var html = "", cursor = 0;
    marcas.forEach(function (m) {
      if (m[0] < cursor) return;
      html += escaparHtml(pedaco.slice(cursor, m[0])) + "<mark>" + escaparHtml(pedaco.slice(m[0], m[1])) + "</mark>";
      cursor = m[1];
    });
    html += escaparHtml(pedaco.slice(cursor));
    return (ini > 0 ? "…" : "") + html + (fim < texto.length ? "…" : "");
  }
  function montarBusca() {
    var campo = document.querySelector(".busca");
    if (!campo) return;
    var saida = document.querySelector(".resultados-busca");
    var indice = null, carregando = false;
    function carregarIndice() {
      if (indice || carregando || !campo.getAttribute("data-indice") || !window.fetch) return;
      carregando = true;
      fetch(campo.getAttribute("data-indice")).then(function (r) { return r.json(); }).then(function (dados) {
        indice = dados.map(function (s) {
          return { p: s.p, u: s.u, h: s.h, t: s.t, n: normalizar(s.p + " " + s.h + " " + s.t), nh: normalizar(s.h) };
        });
        buscar();
      }).catch(function () { carregando = false; });
    }
    function buscarConteudo(termo) {
      if (!saida) return false;
      var termos = termo.split(/\s+/).filter(function (t) { return t.length > 1; });
      if (!termos.length || !indice) { saida.hidden = true; saida.innerHTML = ""; return false; }
      var achados = [];
      indice.forEach(function (s) {
        if (!termos.every(function (t) { return s.n.indexOf(t) !== -1; })) return;
        var pontos = 0;
        termos.forEach(function (t) {
          if (s.nh.indexOf(t) !== -1) pontos += 10;
          pontos += Math.min(5, s.n.split(t).length - 1);
        });
        achados.push({ s: s, pontos: pontos });
      });
      achados.sort(function (a, b) { return b.pontos - a.pontos; });
      if (!achados.length) { saida.hidden = true; saida.innerHTML = ""; return false; }
      var html = "<h2>Dentro das páginas <small>" + achados.length + (achados.length === 1 ? " trecho" : " trechos") + "</small></h2><ol>";
      achados.slice(0, 15).forEach(function (a) {
        var s = a.s;
        var achouNoTexto = termos.some(function (t) { return normalizar(s.t).indexOf(t) !== -1; });
        html += '<li><a href="' + escaparHtml(s.u) + '"><span class="onde">' + escaparHtml(s.p) +
          (s.h ? " › " + escaparHtml(s.h) : "") + "</span>" +
          (achouNoTexto ? '<span class="trecho">' + trecho(s.t, termos) + "</span>" : "") + "</a></li>";
      });
      html += "</ol>";
      saida.innerHTML = html;
      saida.hidden = false;
      return true;
    }
    function buscar() {
      var termo = normalizar(campo.value.trim());
      document.querySelectorAll(".grade .cartao").forEach(function (c) {
        var texto = normalizar(c.textContent + " " + (c.getAttribute("data-termos") || ""));
        c.style.display = !termo || texto.indexOf(termo) !== -1 ? "" : "none";
      });
      var algum = false;
      document.querySelectorAll(".grupo-cadernos").forEach(function (g) {
        var visiveis = Array.prototype.some.call(g.querySelectorAll(".cartao"), function (c) { return c.style.display !== "none"; });
        g.hidden = !visiveis;
        if (visiveis) algum = true;
      });
      document.querySelectorAll(".titulo-bloco").forEach(function (t) { t.hidden = !!termo; });
      var noConteudo = buscarConteudo(termo);
      var vazio = document.querySelector(".sem-resultado");
      if (vazio) vazio.hidden = algum || noConteudo || (!indice && !!termo);
    }
    campo.addEventListener("focus", carregarIndice);
    campo.addEventListener("input", function () { carregarIndice(); buscar(); });
    /* O botão de busca do topo leva para index.html#busca. */
    if (window.location.hash === "#busca") {
      campo.focus();
      carregarIndice();
    }
  }

  /* ---------- backup do progresso (exportar e importar um arquivo) ---------- */
  function montarBackup() {
    document.querySelectorAll("[data-backup]").forEach(function (caixa) {
      var aviso = caixa.querySelector(".aviso-backup");
      var entrada = caixa.querySelector('input[type="file"]');
      function avisar(texto) { if (aviso) aviso.textContent = texto; }
      caixa.querySelector(".exportar").addEventListener("click", function () {
        var dados = {};
        try {
          for (var i = 0; i < localStorage.length; i++) {
            var k = localStorage.key(i);
            if (k && k.indexOf("am-") === 0) dados[k] = localStorage.getItem(k);
          }
        } catch (e) { avisar("Este navegador não deixa ler o progresso salvo."); return; }
        var hoje = new Date().toISOString().slice(0, 10);
        var arquivo = new Blob([JSON.stringify({ site: "aprenda-matematica", versao: 1, data: hoje, dados: dados }, null, 1)],
          { type: "application/json" });
        var a = document.createElement("a");
        a.href = URL.createObjectURL(arquivo);
        a.download = "aprenda-matematica-progresso-" + hoje + ".json";
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
        avisar("Arquivo salvo. Guarde-o para levar o progresso para outro aparelho.");
      });
      caixa.querySelector(".importar").addEventListener("click", function () { entrada.click(); });
      entrada.addEventListener("change", function () {
        var f = entrada.files && entrada.files[0];
        if (!f) return;
        var leitor = new FileReader();
        leitor.onload = function () {
          var pacote;
          try { pacote = JSON.parse(leitor.result); } catch (e) { pacote = null; }
          if (!pacote || pacote.site !== "aprenda-matematica" || typeof pacote.dados !== "object") {
            avisar("Esse arquivo não é um backup do Aprenda Matemática.");
            entrada.value = "";
            return;
          }
          if (!window.confirm("Trocar o progresso deste aparelho pelo do arquivo de " + (pacote.data || "backup") + "?")) {
            entrada.value = "";
            return;
          }
          try {
            Object.keys(pacote.dados).forEach(function (k) {
              if (k.indexOf("am-") === 0 && typeof pacote.dados[k] === "string") localStorage.setItem(k, pacote.dados[k]);
            });
          } catch (e) { avisar("Não deu para gravar o progresso neste navegador."); return; }
          window.location.reload();
        };
        leitor.readAsText(f);
      });
    });
  }
})();
