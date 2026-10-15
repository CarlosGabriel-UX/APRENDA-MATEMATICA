/* Aprenda Matemática: interações do site (tema, questões, progresso, busca). */
(function () {
  "use strict";

  var CHAVE_TEMA = "am-tema";
  var CHAVE_FEITOS = "am-cadernos-estudados";
  var CHAVE_ERROS = "am-caderno-de-erros";
  var CHAVE_FONTE = "am-tamanho-fonte";
  var CHAVE_ULTIMO = "am-ultimo-caderno";
  var CHAVE_RESPOSTAS = "am-respostas";
  var TAMANHOS = [100, 112.5, 125, 90];

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
  function aplicarTema(t) {
    raiz.setAttribute("data-theme", t);
    document.querySelectorAll(".botao-tema").forEach(function (b) {
      if (!b.closest(".nav-inferior")) b.textContent = t === "dark" ? "☀️ Claro" : "🌙 Escuro";
      b.setAttribute("aria-pressed", t === "dark" ? "true" : "false");
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

    var menu = document.querySelector(".botao-menu");
    if (menu) {
      menu.addEventListener("click", function () {
        document.querySelector(".lateral").classList.toggle("aberta");
      });
    }

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

    /* Ao imprimir, abre todas as resoluções. */
    window.addEventListener("beforeprint", function () {
      document.querySelectorAll("details.exemplo").forEach(function (d) { d.open = true; });
    });
  });

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
    estat("erros", lerErros().length);
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
    var alvo = document.querySelector("[data-sumario]");
    if (!alvo) return;
    var titulos = document.querySelectorAll("article.caderno h2");
    if (!titulos.length) { alvo.remove(); return; }
    var ol = document.createElement("ol");
    titulos.forEach(function (h, i) {
      if (!h.id) h.id = "secao-" + (i + 1);
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = "#" + h.id;
      a.textContent = h.textContent;
      li.appendChild(a);
      ol.appendChild(li);
    });
    alvo.appendChild(ol);
  }

  /* ---------- caderno de erros ---------- */
  function lerErros() {
    var e = ler(CHAVE_ERROS, []);
    return Array.isArray(e) ? e : [];
  }
  function guardarErro(item) {
    var erros = lerErros().filter(function (e) { return e.id !== item.id; });
    erros.push(item);
    gravar(CHAVE_ERROS, erros);
    atualizarContagemErros();
  }
  function removerErro(id) {
    var erros = lerErros();
    var restantes = erros.filter(function (e) { return e.id !== id; });
    if (restantes.length !== erros.length) {
      gravar(CHAVE_ERROS, restantes);
      atualizarContagemErros();
      return true;
    }
    return false;
  }
  function atualizarContagemErros() {
    var n = lerErros().length;
    document.querySelectorAll("[data-contagem-erros]").forEach(function (el) {
      el.textContent = n ? String(n) : "";
      el.hidden = !n;
    });
  }

  /* Na página do caderno de erros, monta as questões salvas antes de ativá-las. */
  function montarListaErros() {
    var alvo = document.querySelector("[data-lista-erros]");
    if (!alvo) return;
    var erros = lerErros();
    if (!erros.length) {
      alvo.innerHTML = '<div class="caixa nota"><span class="rotulo">Nenhum erro guardado</span>' +
        "<p>Quando você errar uma questão em qualquer caderno, ela aparece aqui automaticamente. " +
        "Ao acertá-la (aqui ou no caderno), ela sai da lista.</p></div>";
      return;
    }
    var grupos = {};
    var ordem = [];
    erros.forEach(function (e) {
      if (!grupos[e.slug]) { grupos[e.slug] = { titulo: e.titulo, itens: [] }; ordem.push(e.slug); }
      grupos[e.slug].itens.push(e);
    });
    var html = '<p class="resumo-erros"><span>Você tem <strong>' + erros.length + "</strong> questão(ões) para revisar.</span>" +
      '<button type="button" class="botao secundario limpar-erros">Limpar tudo</button></p>';
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
            if (removerErro(id)) texto += " Ela saiu do seu caderno de erros.";
          } else if (pagina !== "erros") {
            guardarErro({ id: id, slug: pagina, titulo: tituloPagina, html: original });
            texto += " Guardada no seu caderno de erros.";
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

  /* ---------- busca na página inicial ---------- */
  function montarBusca() {
    var campo = document.querySelector(".busca");
    if (!campo) return;
    function normalizar(s) {
      return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
    }
    campo.addEventListener("input", function () {
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
      var vazio = document.querySelector(".sem-resultado");
      if (vazio) vazio.hidden = algum;
    });
  }
})();
