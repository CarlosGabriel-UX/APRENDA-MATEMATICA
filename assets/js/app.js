/* Aprenda Matemática: interações do site (tema, questões, progresso, busca). */
(function () {
  "use strict";

  var CHAVE_TEMA = "am-tema";
  var CHAVE_FEITOS = "am-cadernos-estudados";

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

    montarSumario();
    montarQuestoes();
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

  /* ---------- questões de múltipla escolha ---------- */
  function montarQuestoes() {
    var questoes = document.querySelectorAll(".questao");
    if (!questoes.length) return;
    var acertos = 0, respondidas = 0, total = questoes.length;
    var letras = "abcde";

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
          veredito.textContent = acertou
            ? "Correto! Alternativa " + correta.toUpperCase() + "."
            : "Não foi dessa vez. A resposta é a alternativa " + correta.toUpperCase() + ".";
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
