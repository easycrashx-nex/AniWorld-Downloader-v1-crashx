(function () {
  const queueId = window.CAPTCHA_QUEUE_ID;
  if (!queueId) return;

  const img = document.getElementById("captchaPageScreenshot");
  const hint = document.getElementById("captchaPageHint");
  const state = document.getElementById("captchaPageState");
  const reloadBtn = document.getElementById("captchaReloadBtn");
  const backBtn = document.getElementById("captchaBackBtn");

  let refreshTimer = null;
  let statusTimer = null;
  let sawActiveSession = false;

  function setHint(message) {
    if (hint) hint.textContent = message;
  }

  function setState(label, kind) {
    if (!state) return;
    state.textContent = label;
    state.classList.remove("is-success", "is-warning", "is-error");
    if (kind) state.classList.add(kind);
  }

  function stopPolling() {
    if (refreshTimer) {
      clearInterval(refreshTimer);
      refreshTimer = null;
    }
    if (statusTimer) {
      clearInterval(statusTimer);
      statusTimer = null;
    }
  }

  function refreshScreenshot() {
    if (!img) return;
    img.src = "/api/captcha/" + queueId + "/screenshot?t=" + Date.now();
  }

  function closeOrReturn() {
    try {
      window.close();
    } catch (e) {
      /* ignore */
    }
    window.location.href = window.CAPTCHA_RETURN_URL || "/";
  }

  async function pollStatus() {
    try {
      const resp = await fetch("/api/captcha/" + queueId + "/status");
      const data = await resp.json();

      if (data.active) {
        sawActiveSession = true;
        if (data.done) {
          stopPolling();
          setState("Solved", "is-success");
          setHint("Captcha solved. The download is resuming now.");
          setTimeout(closeOrReturn, 1200);
          return;
        }
        setState("Active", "");
        setHint("Click inside the browser surface to solve the captcha.");
        return;
      }

      if (sawActiveSession) {
        stopPolling();
        setState("Finished", "is-success");
        setHint("The captcha session ended. Return to the downloader and check the queue.");
        return;
      }

      setState("Waiting", "is-warning");
      setHint("Waiting for the captcha browser session to become available...");
    } catch (error) {
      setState("Error", "is-error");
      setHint("Captcha status could not be loaded right now.");
    }
  }

  if (img) {
    img.addEventListener("click", function (e) {
      if (!queueId || !img.naturalWidth || !img.naturalHeight) return;
      const rect = img.getBoundingClientRect();
      const scaleX = img.naturalWidth / img.clientWidth;
      const scaleY = img.naturalHeight / img.clientHeight;
      const x = Math.round((e.clientX - rect.left) * scaleX);
      const y = Math.round((e.clientY - rect.top) * scaleY);
      fetch("/api/captcha/" + queueId + "/click", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ x, y }),
      }).catch(function () {});
    });

    img.addEventListener("load", function () {
      if (sawActiveSession) {
        setHint("Click inside the browser surface to solve the captcha.");
      }
    });
  }

  if (reloadBtn) {
    reloadBtn.addEventListener("click", refreshScreenshot);
  }

  if (backBtn) {
    backBtn.addEventListener("click", closeOrReturn);
  }

  refreshScreenshot();
  pollStatus();
  refreshTimer = setInterval(refreshScreenshot, 700);
  statusTimer = setInterval(pollStatus, 1200);
})();
