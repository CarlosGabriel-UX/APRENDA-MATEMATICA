/* Aprenda Matemática: interações do site (tema, questões, progresso, busca). */
(function () {
  "use strict";

  var CHAVE_TEMA = "am-tema";
  var CHAVE_FEITOS = "am-cadernos-estudados";
  var CHAVE_ERROS = "am-caderno-de-erros";

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
    var b = document.querySelector(".botao-tema");
    if (b) b.textContent = t === "dark" ? "☀️ Claro" : "🌙 Escuro";
  }
  var temaSalvo = ler(CHAVE_TEMA, null);
  var prefereEscuro = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  aplicarTema(temaSalvo || (prefereEscuro ? "dark" : "light"));

  document.addEventListener("DOMContentLoaded", function () {
    aplicarTema(raiz.getAttribute("data-theme"));
    var botaoTema = document.querySelector(".botao-tema");
    if (botaoTema) {
      botaoTema.addEventListener("click", function () {
        var novo = raiz.getAttribute("data-theme") === "dark" ? "light" : "dark";
        aplicarTema(novo);
        gravar(CHAVE_TEMA, novo);
      });
    }

    var menu = document.querySelector(".botao-menu");
    if (menu) {
      menu.addEventListener("click", function () {
        document.querySelector(".lateral").classList.toggle("aberta");
      });
    }

    montarListaErros();
    montarSumario();
    montarQuestoes();
    atualizarContagemErros();
    montarProgresso();
    montarBusca();

    /* Ao imprimir, abre todas as resoluções. */
    window.addEventListener("beforeprint", function () {
      document.querySelectorAll("details.exemplo").forEach(function (d) { d.open = true; });
    });
  });

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
    ultima.parentNode.insertBefore(placar, ultima.nextSibling);

    function atualizarPlacar() {
      placar.querySelector(".texto").textContent =
        "Questões: " + respondidas + "/" + total + " respondidas · " + acertos + " acerto(s)";
    }

    questoes.forEach(function (q, idx) {
      var id = q.getAttribute("data-id") || (pagina + "#" + (idx + 1));
      var original = q.outerHTML;
      var correta = (q.getAttribute("data-correta") || "").toLowerCase();
      var num = document.createElement("div");
      num.className = "num";
      num.textContent = "Questão " + (idx + 1);
      q.insertBefore(num, q.firstChild);

      var veredito = document.createElement("p");
      veredito.className = "veredito";
      var exp = q.querySelector(".explicacao");
      if (exp) exp.insertBefore(veredito, exp.firstChild);

      var itens = q.querySelectorAll("ol.alternativas > li");
      itens.forEach(function (li, i) {
        var botao = document.createElement("button");
        botao.type = "button";
        botao.dataset.letra = letras[i];
        botao.innerHTML = '<span class="letra">' + letras[i].toUpperCase() + ")</span><span>" + li.innerHTML + "</span>";
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
          veredito.className = "veredito " + (acertou ? "ok" : "nao");
          var texto = acertou
            ? "Correto! Alternativa " + correta.toUpperCase() + "."
            : "Não foi dessa vez. A resposta é a alternativa " + correta.toUpperCase() + ".";
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
      acertos = 0; respondidas = 0;
      questoes.forEach(function (q) {
        q.classList.remove("respondida");
        q.querySelectorAll("ol.alternativas button").forEach(function (b) {
          b.disabled = false;
          b.classList.remove("certa", "errada");
        });
      });
      atualizarPlacar();
      questoes[0].scrollIntoView({ behavior: "smooth", block: "center" });
    });

    atualizarPlacar();
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
        var total = document.querySelectorAll(".grade .cartao[data-slug]").length;
        var n = feitos.filter(function (s) { return document.querySelector('.grade .cartao[data-slug="' + s + '"]'); }).length;
        barra.querySelector(".valor").textContent = n + " de " + total + " cadernos estudados";
        barra.querySelector(".barra > span").style.width = (total ? (100 * n / total) : 0) + "%";
      }
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
    });
  }
})();
