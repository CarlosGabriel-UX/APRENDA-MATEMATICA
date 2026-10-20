/* Aprenda Matemática: conta do aluno (Supabase) e sincronização do progresso na nuvem.
   Usa só fetch nas APIs REST do Supabase (Auth e PostgREST), sem biblioteca. */
(function () {
  "use strict";

  var SUPABASE = "https://eluozdegkowuktwhckup.supabase.co";
  var CHAVE_API = "sb_publishable_pQ1IaV7YiE_II6t8sSKKow_jf4LAJNj"; /* chave pública: o acesso é limitado pelo RLS */
  var SITE = "https://carlosgabriel-ux.github.io/APRENDA-MATEMATICA/";
  var CHAVE_SESSAO = "am-sessao";
  var CHAVE_SYNC = "am-sync";
  /* Só o progresso de estudo vai para a nuvem; tema e tamanho da letra ficam em cada aparelho. */
  var SINCRONIZADAS = ["am-cadernos-estudados", "am-caderno-de-erros", "am-respostas", "am-ultimo-caderno"];

  function ler(chave, padrao) {
    try {
      var v = localStorage.getItem(chave);
      return v === null ? padrao : JSON.parse(v);
    } catch (e) { return padrao; }
  }
  function gravar(chave, valor) {
    try {
      if (valor === null) localStorage.removeItem(chave);
      else localStorage.setItem(chave, JSON.stringify(valor));
    } catch (e) { /* sem armazenamento */ }
  }

  /* ---------- chamadas às APIs ---------- */
  function erroDeRede() { return { erro: "Sem conexão com o servidor. Confira a internet e tente de novo." }; }
  function traduzir(r) {
    var codigo = (r && (r.error_code || r.code || r.error)) || "";
    var msg = (r && (r.msg || r.error_description || r.message)) || "";
    if (codigo === "invalid_credentials" || (codigo === "invalid_grant" && /credentials/i.test(msg))) return "E-mail ou senha incorretos.";
    if (codigo === "email_not_confirmed") return "Confirme seu e-mail antes de entrar: procure a mensagem na caixa de entrada e no spam.";
    if (codigo === "user_already_exists" || /already registered/i.test(msg)) return "Já existe uma conta com esse e-mail. Use a aba Entrar.";
    if (codigo === "weak_password" || /password should be/i.test(msg)) return "A senha precisa ter pelo menos 6 caracteres.";
    if (codigo === "validation_failed" || /invalid.*email|email.*invalid/i.test(msg)) return "Confira o e-mail digitado.";
    if (/rate limit/i.test(codigo + msg)) return "Muitas tentativas em pouco tempo. Espere alguns minutos e tente de novo.";
    if (codigo === "same_password") return "A nova senha precisa ser diferente da antiga.";
    return "Não deu certo (" + (msg || codigo || "erro desconhecido") + ").";
  }
  function auth(caminho, corpo, token, metodo) {
    var cab = { apikey: CHAVE_API, "Content-Type": "application/json" };
    if (token) cab.Authorization = "Bearer " + token;
    return fetch(SUPABASE + "/auth/v1/" + caminho, {
      method: metodo || "POST", headers: cab, body: corpo ? JSON.stringify(corpo) : undefined
    }).then(function (resp) {
      return resp.text().then(function (t) {
        var dados = {};
        try { dados = t ? JSON.parse(t) : {}; } catch (e) { dados = {}; }
        return resp.ok ? dados : { erro: traduzir(dados), status: resp.status };
      });
    }, erroDeRede);
  }

  /* ---------- sessão ---------- */
  function sessao() { return ler(CHAVE_SESSAO, null); }
  function guardarSessao(r) {
    if (!r || !r.access_token) return null;
    var s = {
      access_token: r.access_token,
      refresh_token: r.refresh_token,
      expira: Date.now() + (r.expires_in || 3600) * 1000,
      email: (r.user && r.user.email) || (sessao() || {}).email || "",
      id: (r.user && r.user.id) || (sessao() || {}).id || ""
    };
    gravar(CHAVE_SESSAO, s);
    return s;
  }
  /* Devolve uma sessão com token válido (renovando se precisar) ou null. */
  function sessaoValida() {
    var s = sessao();
    if (!s) return Promise.resolve(null);
    if (s.expira - Date.now() > 60 * 1000) return Promise.resolve(s);
    return auth("token?grant_type=refresh_token", { refresh_token: s.refresh_token }).then(function (r) {
      if (r.erro) {
        if (r.status && r.status < 500) sair(true); /* refresh recusado: a sessão acabou */
        return null;
      }
      return guardarSessao(r);
    });
  }
  function sair(silencioso) {
    var s = sessao();
    gravar(CHAVE_SESSAO, null);
    gravar(CHAVE_SYNC, null);
    if (s && !silencioso) auth("logout", null, s.access_token).catch(function () {});
    pintarBotao();
  }

  /* ---------- progresso na nuvem ---------- */
  function rest(metodo, consulta, corpo, token, extra) {
    var cab = { apikey: CHAVE_API, Authorization: "Bearer " + token, "Content-Type": "application/json" };
    if (extra) Object.keys(extra).forEach(function (k) { cab[k] = extra[k]; });
    return fetch(SUPABASE + "/rest/v1/progresso" + consulta, {
      method: metodo, headers: cab, body: corpo ? JSON.stringify(corpo) : undefined, keepalive: metodo !== "GET"
    }).then(function (resp) {
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      return metodo === "GET" ? resp.json() : null;
    });
  }
  function dadosLocais() {
    var d = {};
    SINCRONIZADAS.forEach(function (k) { var v = ler(k, null); if (v !== null) d[k] = v; });
    return d;
  }
  function aplicar(dados) {
    var antes = JSON.stringify(dadosLocais());
    SINCRONIZADAS.forEach(function (k) { gravar(k, dados && k in dados ? dados[k] : null); });
    return antes !== JSON.stringify(dadosLocais());
  }
  /* Junta o progresso de dois aparelhos sem perder nada; em conflito, vale o deste aparelho. */
  function mesclar(local, remoto) {
    var m = {};
    var respostas = {};
    [remoto["am-respostas"], local["am-respostas"]].forEach(function (o) {
      if (o && typeof o === "object") Object.keys(o).forEach(function (k) { respostas[k] = o[k]; });
    });
    if (Object.keys(respostas).length) m["am-respostas"] = respostas;
    var feitos = [];
    [remoto["am-cadernos-estudados"], local["am-cadernos-estudados"]].forEach(function (l) {
      (Array.isArray(l) ? l : []).forEach(function (s) { if (feitos.indexOf(s) === -1) feitos.push(s); });
    });
    if (feitos.length) m["am-cadernos-estudados"] = feitos;
    var erros = {}, ordem = [];
    [remoto["am-caderno-de-erros"], local["am-caderno-de-erros"]].forEach(function (l) {
      (Array.isArray(l) ? l : []).forEach(function (e) {
        if (!e || !e.id) return;
        if (!(e.id in erros)) ordem.push(e.id);
        erros[e.id] = e;
      });
    });
    if (ordem.length) m["am-caderno-de-erros"] = ordem.map(function (id) { return erros[id]; });
    var ultimo = local["am-ultimo-caderno"] || remoto["am-ultimo-caderno"];
    if (ultimo) m["am-ultimo-caderno"] = ultimo;
    return m;
  }

  var envio = null, enviando = false;
  function estadoSync() { return ler(CHAVE_SYNC, { ts: 0, sujo: false }) || { ts: 0, sujo: false }; }
  function enviar() {
    if (enviando) { agendarEnvio(); return Promise.resolve(); }
    enviando = true;
    return sessaoValida().then(function (s) {
      if (!s) return;
      var agora = new Date().toISOString();
      return rest("POST", "", { user_id: s.id, dados: dadosLocais(), atualizado_em: agora }, s.access_token,
        { Prefer: "resolution=merge-duplicates,return=minimal" }).then(function () {
        gravar(CHAVE_SYNC, { ts: Date.parse(agora), sujo: false });
        mostrarEstado();
      });
    }).catch(function () { mostrarEstado("Não foi possível salvar agora. Tentaremos de novo."); })
      .then(function () { enviando = false; });
  }
  function agendarEnvio() {
    window.clearTimeout(envio);
    envio = window.setTimeout(enviar, 2500);
  }
  /* Busca o progresso da nuvem. primeiraVez: acabou de entrar neste aparelho, então junta os dois. */
  function sincronizar(primeiraVez) {
    return sessaoValida().then(function (s) {
      if (!s) return false;
      return rest("GET", "?select=dados,atualizado_em", null, s.access_token).then(function (linhas) {
        var est = estadoSync();
        var remoto = linhas && linhas[0];
        if (!remoto) return enviar().then(function () { return false; });
        var tsRemoto = Date.parse(remoto.atualizado_em) || 0;
        var mudou = false;
        if (primeiraVez || (tsRemoto > est.ts && est.sujo)) {
          mudou = aplicar(mesclar(dadosLocais(), remoto.dados || {}));
          return enviar().then(function () { return mudou; });
        }
        if (tsRemoto > est.ts) {
          mudou = aplicar(remoto.dados || {});
          gravar(CHAVE_SYNC, { ts: tsRemoto, sujo: false });
          mostrarEstado();
          return mudou;
        }
        if (est.sujo) return enviar().then(function () { return false; });
        return false;
      });
    }).catch(function () { return false; });
  }
  /* Se a nuvem trouxe progresso novo, recarrega uma vez para a página mostrar os dados certos. */
  function recarregarSeMudou(mudou) {
    if (!mudou) return;
    try {
      /* Evita recarregar em sequência se algo der errado. */
      if (Date.now() - (+sessionStorage.getItem("am-recarregou") || 0) < 15000) return;
      sessionStorage.setItem("am-recarregou", String(Date.now()));
    } catch (e) { return; }
    window.location.reload();
  }

  /* app.js avisa a cada gravação. */
  document.addEventListener("am-gravou", function (ev) {
    if (!sessao() || SINCRONIZADAS.indexOf(ev.detail) === -1) return;
    var est = estadoSync();
    est.sujo = true;
    gravar(CHAVE_SYNC, est);
    agendarEnvio();
  });
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden" && sessao() && estadoSync().sujo) { window.clearTimeout(envio); enviar(); }
  });

  /* ---------- volta do e-mail de confirmação ou de nova senha (tokens no #) ---------- */
  var recuperacao = false, retornou = false;
  (function lerRetorno() {
    var h = window.location.hash || "";
    if (h.indexOf("access_token=") === -1 && h.indexOf("error_description=") === -1) return;
    var p = {};
    h.slice(1).split("&").forEach(function (par) {
      var i = par.indexOf("=");
      if (i > 0) p[decodeURIComponent(par.slice(0, i))] = decodeURIComponent(par.slice(i + 1).replace(/\+/g, " "));
    });
    if (window.history && history.replaceState) history.replaceState(null, "", window.location.pathname + window.location.search);
    if (p.error_description) { window.amAvisoConta = "O link do e-mail não funcionou: " + p.error_description; return; }
    retornou = true;
    guardarSessao({ access_token: p.access_token, refresh_token: p.refresh_token, expires_in: +p.expires_in || 3600 });
    recuperacao = p.type === "recovery";
    window.amAvisoConta = recuperacao ? "" : "E-mail confirmado. Você já está conectado.";
    auth("user", null, p.access_token, "GET").then(function (u) {
      if (u && u.id) {
        var s = sessao();
        s.email = u.email; s.id = u.id;
        gravar(CHAVE_SESSAO, s);
        pintarBotao();
        if (!recuperacao) sincronizar(true).then(recarregarSeMudou);
      }
    });
  })();

  /* ---------- interface ---------- */
  var dialogo = null;
  function el(tag, attrs, texto) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (texto) e.textContent = texto;
    return e;
  }
  function pintarBotao() {
    var s = sessao();
    document.querySelectorAll(".botao-conta").forEach(function (b) {
      b.classList.toggle("conectado", !!s);
      var rotulo = s ? "Sua conta (" + s.email + ")" : "Entrar ou criar conta";
      b.setAttribute("aria-label", rotulo);
      b.title = rotulo;
      var nome = b.querySelector(".nome-conta"), email = b.querySelector(".email-conta");
      if (nome) nome.textContent = s ? s.email.split("@")[0] : "Visitante";
      if (email) email.textContent = s ? s.email : "Entrar ou criar conta";
    });
    document.querySelectorAll(".cartao-nuvem").forEach(function (c) { c.hidden = !!s; });
    document.querySelectorAll(".dica-conta .link-conta").forEach(function (b) { b.hidden = !!s; });
    document.querySelectorAll("[data-estado-conta]").forEach(function (p) {
      p.textContent = s ? "Conectado como " + s.email + ": seu progresso é salvo automaticamente." : "";
    });
  }
  function mostrarEstado(msg) {
    if (!dialogo) return;
    var alvo = dialogo.querySelector(".estado-sync");
    if (!alvo) return;
    var est = estadoSync();
    alvo.textContent = msg || (est.ts ? "Progresso salvo na nuvem em " +
      new Date(est.ts).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) + "." :
      "Salvando seu progresso…");
  }
  function formulario(modo) {
    var f = el("form", { class: "form-conta", novalidate: "" });
    var titulos = { entrar: "Entrar", criar: "Criar conta", esqueci: "Recuperar a senha", nova: "Escolher nova senha" };
    if (modo !== "esqueci" && modo !== "nova") {
      var abas = el("div", { class: "abas-conta", role: "tablist" });
      ["entrar", "criar"].forEach(function (m) {
        var b = el("button", { type: "button", role: "tab", "aria-selected": m === modo ? "true" : "false" }, titulos[m]);
        b.addEventListener("click", function () { abrir(m); });
        abas.appendChild(b);
      });
      f.appendChild(abas);
    } else {
      f.appendChild(el("h2", {}, titulos[modo]));
    }
    var intro = {
      entrar: "Entre para salvar o progresso na nuvem e continuar em qualquer aparelho.",
      criar: "Com uma conta, as questões resolvidas, o caderno de erros e os cadernos estudados ficam salvos automaticamente.",
      esqueci: "Digite o e-mail da conta. Enviaremos um link para você escolher uma nova senha.",
      nova: "Digite a nova senha da sua conta."
    }[modo];
    f.appendChild(el("p", { class: "intro-conta" }, intro));
    if (modo !== "nova") {
      var le = el("label", {}, "E-mail");
      le.appendChild(el("input", { type: "email", name: "email", autocomplete: "email", required: "" }));
      f.appendChild(le);
    }
    if (modo !== "esqueci") {
      var ls = el("label", {}, modo === "nova" ? "Nova senha" : "Senha");
      ls.appendChild(el("input", {
        type: "password", name: "senha", minlength: "6", required: "",
        autocomplete: modo === "entrar" ? "current-password" : "new-password"
      }));
      f.appendChild(ls);
    }
    var msg = el("p", { class: "msg-conta", role: "status" });
    f.appendChild(msg);
    var enviarBotao = el("button", { type: "submit", class: "botao" },
      { entrar: "Entrar", criar: "Criar conta", esqueci: "Enviar link", nova: "Salvar nova senha" }[modo]);
    f.appendChild(enviarBotao);
    if (modo === "entrar") {
      var esq = el("button", { type: "button", class: "link-conta" }, "Esqueci a senha");
      esq.addEventListener("click", function () { abrir("esqueci"); });
      f.appendChild(esq);
    }
    if (modo === "esqueci") {
      var volta = el("button", { type: "button", class: "link-conta" }, "Voltar para Entrar");
      volta.addEventListener("click", function () { abrir("entrar"); });
      f.appendChild(volta);
    }
    f.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var email = f.email ? f.email.value.trim() : "";
      var senha = f.senha ? f.senha.value : "";
      if (f.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { msg.className = "msg-conta erro"; msg.textContent = "Confira o e-mail digitado."; return; }
      if (f.senha && senha.length < 6) { msg.className = "msg-conta erro"; msg.textContent = "A senha precisa ter pelo menos 6 caracteres."; return; }
      enviarBotao.disabled = true;
      msg.className = "msg-conta";
      msg.textContent = "Aguarde…";
      var pedido;
      if (modo === "entrar") pedido = auth("token?grant_type=password", { email: email, password: senha });
      else if (modo === "criar") pedido = auth("signup?redirect_to=" + encodeURIComponent(SITE), { email: email, password: senha });
      else if (modo === "esqueci") pedido = auth("recover?redirect_to=" + encodeURIComponent(SITE), { email: email });
      else pedido = sessaoValida().then(function (s) {
        return s ? auth("user", { password: senha }, s.access_token, "PUT") : { erro: "O link expirou. Peça outro em Esqueci a senha." };
      });
      pedido.then(function (r) {
        enviarBotao.disabled = false;
        if (r.erro) { msg.className = "msg-conta erro"; msg.textContent = r.erro; return; }
        if (modo === "esqueci") {
          msg.className = "msg-conta ok";
          msg.textContent = "Se houver uma conta com esse e-mail, o link chega em alguns minutos (veja também o spam).";
          return;
        }
        if (modo === "nova") {
          recuperacao = false;
          window.amAvisoConta = "Senha alterada.";
          sincronizar(true).then(function (mudou) { abrir(); recarregarSeMudou(mudou); });
          return;
        }
        var s = guardarSessao(r);
        if (!s) {
          /* Cadastro com confirmação de e-mail ligada: ainda não há sessão. */
          msg.className = "msg-conta ok";
          msg.textContent = "Conta criada! Enviamos um e-mail para " + email +
            ". Abra o link da mensagem para confirmar e entrar (veja também o spam).";
          return;
        }
        pintarBotao();
        msg.textContent = "Juntando o progresso deste aparelho com o da conta…";
        sincronizar(true).then(function (mudou) {
          window.amAvisoConta = "Pronto! Seu progresso agora é salvo automaticamente.";
          abrir();
          recarregarSeMudou(mudou);
        });
      });
    });
    return f;
  }
  function painelConectado() {
    var s = sessao();
    var d = el("div", { class: "form-conta" });
    d.appendChild(el("h2", {}, "Sua conta"));
    if (window.amAvisoConta) { d.appendChild(el("p", { class: "msg-conta ok" }, window.amAvisoConta)); window.amAvisoConta = ""; }
    d.appendChild(el("p", { class: "intro-conta" }, "Conectado como " + s.email + "."));
    d.appendChild(el("p", { class: "estado-sync", role: "status" }));
    var agora = el("button", { type: "button", class: "botao secundario" }, "Sincronizar agora");
    agora.addEventListener("click", function () {
      mostrarEstado("Sincronizando…");
      sincronizar(false).then(function (mudou) { mostrarEstado(); recarregarSeMudou(mudou); });
    });
    var fora = el("button", { type: "button", class: "botao secundario" }, "Sair");
    fora.addEventListener("click", function () {
      var pronto = estadoSync().sujo ? enviar() : Promise.resolve();
      pronto.then(function () { sair(false); abrir("entrar"); });
    });
    var acoes = el("div", { class: "acoes-conta" });
    acoes.appendChild(agora);
    acoes.appendChild(fora);
    d.appendChild(acoes);
    d.appendChild(el("p", { class: "nota-conta" },
      "Ao sair, o progresso continua neste aparelho, mas deixa de ser salvo na nuvem até você entrar de novo."));
    return d;
  }
  function abrir(modo) {
    if (!dialogo) {
      dialogo = el("dialog", { class: "dialogo-conta", "aria-label": "Conta" });
      document.body.appendChild(dialogo);
      dialogo.addEventListener("click", function (ev) { if (ev.target === dialogo) dialogo.close(); });
    }
    dialogo.innerHTML = "";
    var fechar = el("button", { type: "button", class: "botao-icone fechar-conta", "aria-label": "Fechar" }, "×");
    fechar.addEventListener("click", function () { dialogo.close(); });
    dialogo.appendChild(fechar);
    if (recuperacao) modo = "nova";
    var conteudo = sessao() && modo !== "nova" ? painelConectado() : formulario(modo || "entrar");
    dialogo.appendChild(conteudo);
    if (!dialogo.open) dialogo.showModal();
    mostrarEstado();
    var primeiro = dialogo.querySelector("input");
    if (primeiro) primeiro.focus();
  }

  document.addEventListener("DOMContentLoaded", function () {
    pintarBotao();
    document.addEventListener("click", function (ev) {
      var alvo = ev.target.closest(".botao-conta, [data-abrir-conta]");
      if (!alvo) return;
      ev.preventDefault();
      abrir(sessao() ? undefined : (alvo.getAttribute("data-abrir-conta") || "entrar"));
    });
    if (recuperacao || window.amAvisoConta) abrir(recuperacao ? "nova" : undefined);
    if (sessao() && !retornou) sincronizar(false).then(recarregarSeMudou);
  });
})();
