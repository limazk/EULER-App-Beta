(() => {
  const title = document.getElementById("title");
  const message = document.getElementById("message");
  const eyebrow = document.getElementById("eyebrow");
  const actions = document.getElementById("actions");
  const retry = document.getElementById("retry");
  const hint = document.getElementById("hint");

  let slowTimer;
  let failTimer;

  function clearTimers() {
    window.clearTimeout(slowTimer);
    window.clearTimeout(failTimer);
  }

  function setState(state, heading, body, label, showRetry = false) {
    document.body.className = state;
    title.textContent = heading;
    message.textContent = body;
    eyebrow.textContent = label;
    actions.hidden = !showRetry;
  }

  function startTimers() {
    clearTimers();

    if (!navigator.onLine) {
      setOffline();
      return;
    }

    setState(
      "connecting",
      "Conectando à EULER...",
      "Preparando seu ambiente de trabalho.",
      "INICIANDO"
    );
    hint.textContent = "A primeira conexão pode levar alguns segundos.";

    slowTimer = window.setTimeout(() => {
      setState(
        "warming",
        "O servidor está iniciando",
        "O ambiente da EULER está sendo preparado. Isso pode levar alguns segundos.",
        "AGUARDANDO SERVIDOR"
      );
      hint.textContent = "Você pode manter esta janela aberta.";
    }, 12000);

    failTimer = window.setTimeout(() => {
      setState(
        "failed",
        "A conexão está demorando",
        "Não foi possível abrir a EULER até agora. Você pode tentar novamente sem fechar o aplicativo.",
        "CONEXÃO NÃO CONCLUÍDA",
        true
      );
      hint.textContent = "Se o problema continuar, verifique sua internet e tente novamente.";
    }, 45000);
  }

  function setOffline() {
    clearTimers();
    setState(
      "offline",
      "EULER está offline",
      "Não foi possível conectar ao servidor. Verifique sua conexão com a internet e tente novamente.",
      "SEM CONEXÃO",
      true
    );
    hint.textContent = "Nenhum dado industrial é armazenado nesta tela.";
  }

  retry.addEventListener("click", () => {
    if (!navigator.onLine) {
      setOffline();
      return;
    }
    startTimers();
  });

  window.addEventListener("offline", setOffline);
  window.addEventListener("online", () => {
    setState(
      "failed",
      "Conexão restaurada",
      "A internet voltou. Tente conectar novamente à EULER.",
      "ONLINE",
      true
    );
    hint.textContent = "Clique em Tentar novamente para continuar.";
  });

  startTimers();
})();
