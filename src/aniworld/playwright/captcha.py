import threading as _threading
import queue as _queue_module
import time as _time
import random as _random

# Threading-local: set queue_id from the web worker to enable interactive mode
_local = _threading.local()

# Active captcha sessions keyed by queue_id (int)
_active_sessions = {}
_active_sessions_lock = _threading.Lock()

# Optional hooks set by app.py to avoid circular imports
_on_captcha_start = None  # callable(queue_id: int, url: str)
_on_captcha_end = None    # callable(queue_id: int)

# Global captcha state for status polling
_captcha_state_lock = _threading.Lock()
_captcha_state = None  # None or {"url": ..., "started_at": ..., "solved": bool}

# Serialise concurrent solve attempts
_captcha_lock = _threading.Lock()


def _ensure_virtual_display() -> None:
    """Best-effort xvfb bootstrap for Linux/server environments."""
    try:
        from ..autodeps import _ensure_xvfb
    except Exception:
        return
    try:
        _ensure_xvfb()
    except Exception:
        pass


def _click_turnstile(page, logger=None) -> bool:
    """Locate the Turnstile iframe and click its checkbox with human-like motion."""
    selectors = (
        "iframe[src*='challenges.cloudflare.com']",
        "iframe[src*='cdn-cgi/challenge-platform']",
    )
    for selector in selectors:
        try:
            iframe_el = page.locator(selector).first
            iframe_el.wait_for(state="visible", timeout=2500)
            box = iframe_el.bounding_box()
            if not box:
                continue

            x = box["x"] + 28 + _random.uniform(-4, 4)
            y = box["y"] + box["height"] / 2 + _random.uniform(-3, 3)

            page.mouse.move(x, y, steps=_random.randint(8, 20))
            page.wait_for_timeout(_random.randint(80, 250))
            page.mouse.down()
            page.wait_for_timeout(_random.randint(40, 100))
            page.mouse.up()

            if logger:
                logger.info("Turnstile checkbox clicked")
            return True
        except Exception:
            continue
    return False


def _is_turnstile_token_ready(page) -> bool:
    """Check whether the Turnstile hidden input already carries a token."""
    try:
        return page.evaluate(
            "() => { const el = document.querySelector"
            "('input[name=\"cf-turnstile-response\"]');"
            " return !!(el && el.value && el.value.length > 20); }"
        )
    except Exception:
        return False


def _neutralize_click_blockers(page) -> None:
    """Disable common overlays/popups that intercept submit clicks."""
    try:
        page.evaluate(
            """
            () => {
                const selectors = [
                    "iframe[id^='container-']",
                    "a[id^='lk']",
                    "div[id^='b'] iframe",
                ];

                for (const sel of selectors) {
                    for (const el of document.querySelectorAll(sel)) {
                        el.style.pointerEvents = "none";
                        el.style.display = "none";
                        el.setAttribute("aria-hidden", "true");
                    }
                }

                for (const iframe of document.querySelectorAll("iframe")) {
                    const r = iframe.getBoundingClientRect();
                    if (r.width >= 700 && r.height >= 500) {
                        iframe.style.pointerEvents = "none";
                        iframe.style.display = "none";
                        iframe.setAttribute("aria-hidden", "true");
                    }
                }
            }
            """
        )
    except Exception:
        pass


def _click_submit_button(page, logger=None) -> bool:
    """Click the gate submit button with normal, force, and JS fallbacks."""
    selectors = (
        'button[type="submit"]',
        "button:has-text('Weiter')",
    )

    for selector in selectors:
        try:
            button = page.locator(selector).first
            button.wait_for(state="visible", timeout=2000)
        except Exception:
            continue

        try:
            button.click(timeout=2000)
            return True
        except Exception as err:
            if logger:
                logger.warning(f"Submit normal click failed: {err}")

        _neutralize_click_blockers(page)

        try:
            button.click(force=True, timeout=2000)
            return True
        except Exception as err:
            if logger:
                logger.warning(f"Submit force-click failed: {err}")

        try:
            clicked = page.evaluate(
                """
                () => {
                    const byType = document.querySelector("button[type='submit']");
                    if (byType) {
                        byType.click();
                        return true;
                    }
                    const byText = Array.from(document.querySelectorAll("button"))
                        .find((b) => (b.textContent || "").trim().toLowerCase() === "weiter");
                    if (byText) {
                        byText.click();
                        return true;
                    }
                    return false;
                }
                """
            )
            if clicked:
                return True
        except Exception as err:
            if logger:
                logger.warning(f"Submit JS click failed: {err}")

    return False


def is_captcha_page(html: str, status_code: int = 200) -> bool:
    """Detect Cloudflare challenge / CAPTCHA pages."""
    if status_code in (403, 503):
        return True

    lower = html.lower()
    indicators = [
        "just a moment",
        "cf-turnstile",
        "checking your browser",
        "enable javascript and cookies",
        "ddos protection by cloudflare",
        "<title>attention required",
        "cdn-cgi/challenge-platform",
        "challenges.cloudflare.com",
        "challenge-running",
        "cf_chl_",
        "jschl-answer",
        "<title>just a moment",
        "hcaptcha.com",
        "newassets.hcaptcha",
        "g-recaptcha",
        # legacy aniworld check kept for safety
        "<title>stream wird vorbereitet...</title>",
        # s.to inline Turnstile modal
        "player-prepare-turnstile",
    ]
    return any(ind in lower for ind in indicators)


def get_captcha_status():
    """Return current captcha state dict for the web UI, or None."""
    with _captcha_state_lock:
        return dict(_captcha_state) if _captcha_state else None


def solve_captcha(url: str):
    """
    Solve a CAPTCHA for *url*.

    - WebUI mode  (queue_id set in threading-local): streams screenshots to the
      Web UI so the user can click inside the browser; injects cookies afterwards.
    - CLI mode: opens a visible browser window and waits for the user to solve.

    After a successful solve all browser cookies are injected into GLOBAL_SESSION
    so subsequent requests work without re-solving.

    Returns the final URL (str) on success — for redirect-based captchas this is
    the provider URL captured from an iframe.  Returns None on timeout / error.
    Callers that don't need the URL can ignore the return value.
    """
    queue_id = getattr(_local, "queue_id", None)
    if queue_id is not None:
        return _solve_captcha_interactive(url, queue_id)
    return _solve_captcha_cli(url)


def _solve_captcha_cli(url: str) -> bool:
    """CLI mode captcha solver — opens a visible browser, injects cookies on success."""
    try:
        from patchright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            "patchright ist nicht installiert. "
            "Bitte installieren mit: pip install patchright && patchright install chromium"
        )

    from ..config import GLOBAL_SESSION
    from ..logger import get_logger
    logger = get_logger(__name__)

    with _captcha_lock:
        global _captcha_state
        with _captcha_state_lock:
            _captcha_state = {"url": url, "started_at": _time.time(), "solved": False}

        logger.warning(f"CAPTCHA detected for {url} — opening browser for manual solving")

        try:
            _ensure_virtual_display()
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    )
                )
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded")

                timeout = 300  # 5 minutes
                start = _time.time()
                solved = False
                turnstile_clicked = False

                while _time.time() - start < timeout:
                    # Standard Cloudflare full-page challenge
                    if any(c["name"] == "cf_clearance" for c in context.cookies()):
                        solved = True
                        break

                    # s.to modal: form target="player-iframe" — after Weiter the VOE URL
                    # loads into that iframe. The modal HTML stays on the page, so
                    # is_captcha_page() would never become False. Instead poll the frame.
                    for frame in page.frames:
                        if frame.name == "player-iframe":
                            fu = frame.url
                            if fu and fu not in ("about:blank", "", url):
                                final_url = fu
                                solved = True
                                break
                    if solved:
                        break

                    # Also check page content for classic full-page solve
                    try:
                        if not is_captcha_page(page.content()):
                            solved = True
                            break
                    except Exception:
                        pass

                    if not turnstile_clicked and not _is_turnstile_token_ready(page):
                        if _click_turnstile(page, logger):
                            turnstile_clicked = True
                            page.wait_for_timeout(_random.randint(2000, 4000))
                            continue
                    elif turnstile_clicked and not _is_turnstile_token_ready(page):
                        turnstile_clicked = False

                    if _is_turnstile_token_ready(page):
                        try:
                            if _click_submit_button(page, logger):
                                page.wait_for_timeout(2000)
                        except Exception:
                            pass

                    _time.sleep(1.5)

                if solved:
                    for cookie in context.cookies():
                        GLOBAL_SESSION.cookies.set(
                            cookie["name"],
                            cookie["value"],
                            domain=cookie.get("domain", "").lstrip("."),
                        )
                    logger.info("CAPTCHA solved — cookies injected into session")
                else:
                    logger.warning("CAPTCHA timeout after 5 minutes")

                browser.close()

            with _captcha_state_lock:
                _captcha_state = None

            return final_url if solved else None

        except Exception as e:
            logger.error(f"Error while solving CAPTCHA: {e}", exc_info=True)
            with _captcha_state_lock:
                _captcha_state = None
            return None


class CaptchaSession:
    """Holds state for an in-progress interactive captcha solve (web UI mode)."""

    def __init__(self):
        self._screenshot = b""
        self._screenshot_lock = _threading.Lock()
        self._click_queue = _queue_module.Queue()
        self.done = False
        self.result_url = None

    def get_screenshot(self) -> bytes:
        with self._screenshot_lock:
            return self._screenshot

    def _store_screenshot(self, data: bytes):
        with self._screenshot_lock:
            self._screenshot = data

    def enqueue_click(self, x: int, y: int):
        self._click_queue.put_nowait((x, y))


def _solve_captcha_interactive(url: str, queue_id: int) -> bool:
    """WebUI mode: stream screenshots, accept clicks, inject cookies on success."""
    try:
        from patchright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            "patchright ist nicht installiert. "
            "Bitte installieren mit: pip install patchright && patchright install chromium"
        )

    from ..config import GLOBAL_SESSION
    from ..logger import get_logger
    logger = get_logger(__name__)

    session = CaptchaSession()
    with _active_sessions_lock:
        _active_sessions[queue_id] = session

    if _on_captcha_start is not None:
        try:
            _on_captcha_start(queue_id, url)
        except Exception:
            pass

    global _captcha_state
    try:
        _ensure_virtual_display()
        with sync_playwright() as p:
            # headless=False required for Cloudflare/Turnstile to work.
            # Window pushed off-screen to avoid visible popup on server desktops.
            browser = p.chromium.launch(
                headless=False,
                args=["--window-position=-32000,-32000", "--window-size=1280,720"],
            )
            context = browser.new_context(viewport={"width": 1280, "height": 720})
            page = context.new_page()
            page.goto(url)

            with _captcha_state_lock:
                _captcha_state = {"url": url, "started_at": _time.time(), "solved": False}

            solved = False
            turnstile_clicked = False
            for _ in range(300):  # up to ~5 minutes
                # Stream screenshot to Web UI
                try:
                    shot = page.screenshot(type="jpeg", quality=65)
                    session._store_screenshot(shot)
                except Exception:
                    pass

                # Forward pending click events from Web UI
                while not session._click_queue.empty():
                    try:
                        cx, cy = session._click_queue.get_nowait()
                        page.mouse.click(cx, cy)
                        page.wait_for_timeout(400)
                    except Exception:
                        pass

                # Check for cf_clearance cookie (classic Cloudflare challenge)
                if any(c["name"] == "cf_clearance" for c in context.cookies()):
                    solved = True
                    break

                # s.to modal: poll player-iframe for the VOE URL
                for frame in page.frames:
                    if frame.name == "player-iframe":
                        fu = frame.url
                        if fu and fu not in ("about:blank", "", url):
                            result_url = fu
                            solved = True
                            break
                if solved:
                    break

                # Classic full-page solve (no modal)
                try:
                    if not is_captcha_page(page.content()):
                        solved = True
                        break
                except Exception:
                    pass

                if not turnstile_clicked and not _is_turnstile_token_ready(page):
                    if _click_turnstile(page):
                        turnstile_clicked = True
                        page.wait_for_timeout(_random.randint(2000, 4000))
                        continue
                elif turnstile_clicked and not _is_turnstile_token_ready(page):
                    turnstile_clicked = False

                if _is_turnstile_token_ready(page):
                    try:
                        if _click_submit_button(page, logger):
                            page.wait_for_timeout(2000)
                    except Exception:
                        pass

                page.wait_for_timeout(1000)

            # Final screenshot
            try:
                shot = page.screenshot(type="jpeg", quality=65)
                session._store_screenshot(shot)
            except Exception:
                pass

            if solved:
                for cookie in context.cookies():
                    GLOBAL_SESSION.cookies.set(
                        cookie["name"],
                        cookie["value"],
                        domain=cookie.get("domain", "").lstrip("."),
                    )
                logger.info("CAPTCHA solved — cookies injected into session")
            else:
                logger.warning("CAPTCHA timeout after 5 minutes")

            final_url = page.url
            page.wait_for_timeout(400)
            browser.close()

        # Use the player-iframe URL if captured, otherwise fall back to page URL
        result_url = locals().get("result_url") or _extract_iframe_url(page, url)
        if result_url == url:
            result_url = final_url

        session.result_url = result_url or final_url
        session.done = True
        if solved:
            _time.sleep(2.0)

        with _captcha_state_lock:
            _captcha_state = None

        return result_url if solved else None

    finally:
        if _on_captcha_end is not None:
            try:
                _on_captcha_end(queue_id)
            except Exception:
                pass
        with _active_sessions_lock:
            _active_sessions.pop(queue_id, None)


def _extract_iframe_url(page, current_url: str) -> str:
    """
    After a modal is dismissed the provider player loads as an iframe on the same
    page (URL never changes).  Scan all frames for the first external URL.
    Returns the iframe URL if found, otherwise *current_url*.
    """
    try:
        from urllib.parse import urlparse
        current_netloc = urlparse(current_url).netloc.lstrip("www.")
        for frame in page.frames:
            u = frame.url
            if not u or u in ("about:blank", current_url):
                continue
            nl = urlparse(u).netloc.lstrip("www.")
            if nl and nl != current_netloc:
                return u
    except Exception:
        pass
    return current_url


def playwright_get_page_url(url: str) -> str:
    solve_captcha(url)
    from ..config import GLOBAL_SESSION
    return GLOBAL_SESSION.get(url).url


def _inject_session_cookies(context, url: str) -> None:
    """Copy GLOBAL_SESSION cookies into a patchright browser context."""
    try:
        from ..config import GLOBAL_SESSION
        from urllib.parse import urlparse
        base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        cookies = [
            {"name": c.name, "value": c.value, "url": base}
            for c in GLOBAL_SESSION.cookies
        ]
        if cookies:
            context.add_cookies(cookies)
    except Exception:
        pass


def _sto_redirect_path(expected_redirect_url: str | None) -> str | None:
    if not expected_redirect_url:
        return None
    try:
        from urllib.parse import urlparse

        parsed = urlparse(expected_redirect_url)
        path = parsed.path or ""
        if parsed.query:
            path = f"{path}?{parsed.query}"
        return path or None
    except Exception:
        return None


def _sto_is_external_provider_url(candidate_url: str | None, episode_netloc: str) -> bool:
    if not candidate_url:
        return False
    try:
        from urllib.parse import urlparse

        parsed = urlparse(candidate_url)
    except Exception:
        return False
    return bool(parsed.scheme and parsed.netloc and parsed.netloc != episode_netloc)


def _click_sto_provider_option(
    page,
    provider_name: str,
    language_label: str,
    expected_redirect_url: str | None = None,
) -> bool:
    """
    Trigger the original provider click on the episode page.

    s.to now resolves some provider opens client-side. Replaying the native page
    click is more reliable than hoping a raw GET on the redirect URL still
    leaves the site.
    """
    redirect_path = (_sto_redirect_path(expected_redirect_url) or "").strip()
    provider_name = str(provider_name or "").strip()
    language_label = str(language_label or "").strip()

    clicked = False
    try:
        selector_parts = ['[data-play-url][data-provider-name]']
        if provider_name:
            selector_parts.append(f'[data-provider-name="{provider_name}"]')
        selector = "".join(selector_parts)
        locator = page.locator(selector)
        if locator.count() > 0:
            target = locator.first
            try:
                target.scroll_into_view_if_needed(timeout=1500)
            except Exception:
                pass
            try:
                target.click(timeout=2000)
                page.wait_for_timeout(250)
                clicked = True
            except Exception:
                try:
                    target.click(timeout=2000, force=True)
                    page.wait_for_timeout(250)
                    clicked = True
                except Exception:
                    pass
    except Exception:
        pass

    try:
        dom_armed = bool(
            page.evaluate(
                """({ providerName, languageLabel, redirectPath }) => {
                    const norm = (v) => String(v || "").trim();
                    const nodes = [...document.querySelectorAll("[data-play-url][data-provider-name]")];
                    if (!nodes.length) return false;

                    let exactByPath = nodes.find((node) => {
                        const nodePath = norm(node.dataset.playUrl);
                        return (
                            redirectPath &&
                            nodePath === norm(redirectPath)
                        );
                    });

                    let providerMatches = nodes.filter((node) =>
                        !providerName || norm(node.dataset.providerName) === providerName
                    );

                    let match = exactByPath;

                    if (!match && providerMatches.length && languageLabel) {
                        match = providerMatches.find((node) =>
                            norm(node.dataset.languageLabel) === languageLabel
                        );
                    }

                    if (!match && providerMatches.length) {
                        match = providerMatches[0];
                    }

                    if (!match && exactByPath) {
                        match = exactByPath;
                    }

                    if (!match) return false;

                    for (const node of nodes) {
                        node.classList.toggle("active", node === match);
                    }

                    match.scrollIntoView({ block: "center", inline: "center" });

                    const clickable =
                        match.closest("a,button,[role='button'],label,.hosterSiteDirectNav,li,div") || match;
                    const playPath = redirectPath || norm(match.dataset.playUrl);
                    const fullPlayUrl = playPath ? new URL(playPath, window.location.origin).href : "";
                    const iframe =
                        document.querySelector('iframe[name="player-iframe"]') ||
                        document.querySelector("#player-iframe") ||
                        document.querySelector("article iframe") ||
                        document.querySelector("iframe");

                    if (typeof clickable.click === "function") clickable.click();
                    clickable.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, view: window }));
                    if (iframe && fullPlayUrl) {
                        iframe.setAttribute("src", fullPlayUrl);
                    }
                    return true;
                }""",
                {
                    "providerName": provider_name,
                    "languageLabel": language_label,
                    "redirectPath": redirect_path,
                },
            )
        )
        return bool(clicked or dom_armed)
    except Exception:
        return clicked


def solve_sto_modal(
    episode_url: str,
    provider_name: str,
    language_label: str,
    expected_redirect_url: str | None = None,
):
    """
    Open the s.to episode page in a browser, click the provider button,
    solve the Turnstile modal, click Weiter, and return the player-iframe
    URL (e.g. voe.sx/e/...).  Works in CLI and WebUI mode.
    Returns the iframe URL on success, None on timeout.
    """
    try:
        from patchright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            "patchright ist nicht installiert. "
            "Bitte installieren mit: pip install patchright && patchright install chromium"
        )

    from ..config import GLOBAL_SESSION
    from ..logger import get_logger
    logger = get_logger(__name__)

    queue_id = getattr(_local, "queue_id", None)
    session_obj = None
    if queue_id is not None:
        session_obj = CaptchaSession()
        with _active_sessions_lock:
            _active_sessions[queue_id] = session_obj
        if _on_captcha_start is not None:
            try:
                _on_captcha_start(queue_id, episode_url)
            except Exception:
                pass

    global _captcha_state
    try:
        extra_args = (
            ["--window-position=-32000,-32000", "--window-size=1280,720"]
            if queue_id is not None
            else []
        )

        _ensure_virtual_display()
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled", *extra_args],
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="de-DE",
                extra_http_headers={
                    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                },
            )
            _inject_session_cookies(context, episode_url)
            page = context.new_page()
            page.add_init_script(
                """() => {
                    window.__stoBridgeMessages = [];
                    window.addEventListener("message", (event) => {
                        try {
                            const data = event && event.data;
                            if (data && typeof data === "object" && data.type === "frameBridge") {
                                window.__stoBridgeMessages.push({
                                    origin: event.origin || "",
                                    type: String(data.type || ""),
                                    token: typeof data.t === "string" ? data.t : "",
                                    err: data.err == null ? null : String(data.err),
                                    ts: Date.now(),
                                });
                            }
                        } catch (_) {}
                    }, true);
                }"""
            )
            from urllib.parse import urlparse as _urlparse
            import re as _re

            episode_netloc = _urlparse(episode_url).netloc
            observed_external_url = None
            bridge_message_seen = False
            prepare_token_seen = False
            external_url_pattern = _re.compile(r"https?://[^\s\"'<>]+")

            def _capture_external_url(candidate_url: str):
                nonlocal observed_external_url
                if observed_external_url or not candidate_url:
                    return
                try:
                    parsed = _urlparse(candidate_url)
                except Exception:
                    return
                if not parsed.scheme or not parsed.netloc:
                    return
                if parsed.netloc != episode_netloc:
                    observed_external_url = candidate_url

            def _capture_external_url_from_text(body: str):
                if observed_external_url or not body:
                    return
                for match in external_url_pattern.findall(body):
                    candidate = str(match or "").rstrip(").,;\"'")
                    try:
                        parsed = _urlparse(candidate)
                    except Exception:
                        continue
                    if parsed.scheme and parsed.netloc and parsed.netloc != episode_netloc:
                        _capture_external_url(candidate)
                        if observed_external_url:
                            return

            def _capture_response(response):
                _capture_external_url(response.url)
                if observed_external_url:
                    return
                try:
                    request = response.request
                    resource_type = request.resource_type
                except Exception:
                    resource_type = ""
                if resource_type not in ("xhr", "fetch", "document", "iframe"):
                    return
                try:
                    if _urlparse(response.url).netloc != episode_netloc:
                        return
                except Exception:
                    return
                try:
                    _capture_external_url_from_text(response.text())
                except Exception:
                    return

            context.on("request", lambda request: _capture_external_url(request.url))
            context.on("response", _capture_response)

            with _captcha_state_lock:
                _captcha_state = {"url": episode_url, "started_at": _time.time(), "solved": False}

            logger.warning(f"Opening episode page for modal solving: {episode_url}")
            page.goto(episode_url, wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass
            page.wait_for_timeout(1800)

            # Single poll loop: streams screenshots from the start, waits for
            # Turnstile to auto-fill, clicks Weiter once, then waits for result.
            final_url = None
            provider_clicked = False
            weiter_clicked = False
            turnstile_clicked = False
            post_clearance_reclick = False
            last_provider_click_at = 0.0
            start = _time.time()

            while _time.time() - start < 300:
                # WebUI: stream screenshots + forward user clicks
                if session_obj is not None:
                    try:
                        session_obj._store_screenshot(page.screenshot(type="jpeg", quality=65))
                    except Exception:
                        pass
                    while not session_obj._click_queue.empty():
                        try:
                            cx, cy = session_obj._click_queue.get_nowait()
                            page.mouse.click(cx, cy)
                            page.wait_for_timeout(300)
                        except Exception:
                            pass

                if not provider_clicked:
                    provider_clicked = _click_sto_provider_option(
                        page,
                        provider_name,
                        language_label,
                        expected_redirect_url=expected_redirect_url,
                    )
                    if provider_clicked:
                        last_provider_click_at = _time.time()
                        logger.warning(
                            "Armed s.to provider option for %s / %s",
                            provider_name,
                            language_label,
                        )
                        page.wait_for_timeout(1200)

                try:
                    gate_state = page.evaluate(
                        """() => {
                            const byId = (id) => document.getElementById(id);
                            const root = byId("episode-redirect-gate-root");
                            const modal = byId("playerPrepareModal");
                            const iframe =
                                byId("player-iframe") ||
                                document.querySelector('iframe[name="player-iframe"]');
                            const prepareToken = byId("player-prepare-token")?.value || "";
                            const turnstileToken =
                                document.querySelector('input[name="cf-turnstile-response"]')?.value || "";
                            const turnstileSitekey = root?.dataset?.turnstileSitekey || "";
                            return {
                                prepareToken,
                                turnstileToken,
                                turnstileRequired: Boolean(turnstileSitekey),
                                iframeSrc: iframe?.getAttribute("src") || iframe?.src || "",
                                modalVisible: Boolean(
                                    modal &&
                                    (
                                        modal.classList.contains("show") ||
                                        modal.classList.contains("showing") ||
                                        modal.getAttribute("aria-hidden") === "false"
                                    )
                                ),
                            };
                        }"""
                    )
                except Exception:
                    gate_state = {
                        "prepareToken": "",
                        "turnstileToken": "",
                        "turnstileRequired": False,
                        "iframeSrc": "",
                        "modalVisible": False,
                    }

                prepare_token = str(gate_state.get("prepareToken") or "")
                turnstile_token = str(gate_state.get("turnstileToken") or "")
                turnstile_required = bool(gate_state.get("turnstileRequired"))
                iframe_src = str(gate_state.get("iframeSrc") or "")

                if prepare_token and not prepare_token_seen:
                    prepare_token_seen = True
                    logger.warning("Observed s.to player prepare token")

                if (
                    provider_clicked
                    and not prepare_token
                    and not bridge_message_seen
                    and not weiter_clicked
                    and (_time.time() - last_provider_click_at) > 6.0
                ):
                    if _click_sto_provider_option(
                        page,
                        provider_name,
                        language_label,
                        expected_redirect_url=expected_redirect_url,
                    ):
                        last_provider_click_at = _time.time()
                        logger.warning(
                            "Re-armed s.to provider option for %s / %s",
                            provider_name,
                            language_label,
                        )
                        page.wait_for_timeout(800)

                try:
                    bridge_messages = page.evaluate(
                        "() => Array.isArray(window.__stoBridgeMessages) ? window.__stoBridgeMessages.slice(-5) : []"
                    )
                except Exception:
                    bridge_messages = []
                if bridge_messages and not bridge_message_seen:
                    bridge_message_seen = True
                    latest_bridge = bridge_messages[-1]
                    logger.warning(
                        "Observed s.to frameBridge message (err=%s)",
                        latest_bridge.get("err") if isinstance(latest_bridge, dict) else None,
                    )

                current_page_url = page.url
                if current_page_url and current_page_url not in ("about:blank", "", episode_url):
                    if _urlparse(current_page_url).netloc != _urlparse(episode_url).netloc:
                        final_url = current_page_url
                        logger.warning(f"External page URL found: {final_url}")
                        break

                if observed_external_url:
                    final_url = observed_external_url
                    logger.warning(f"Observed external request URL: {final_url}")
                    break

                for frame in page.frames:
                    fu = frame.url
                    if not fu or fu in ("about:blank", ""):
                        continue
                    if _sto_is_external_provider_url(fu, episode_netloc):
                        final_url = fu
                        logger.warning(f"Frame URL found: {final_url}")
                        break
                if final_url:
                    break

                for pg in context.pages:
                    if pg is page:
                        continue
                    pu = pg.url
                    if pu and pu not in ("about:blank", ""):
                        if _urlparse(pu).netloc != _urlparse(episode_url).netloc:
                            final_url = pu
                            logger.warning(f"New page URL found: {final_url}")
                            break
                if final_url:
                    break

                if not weiter_clicked:
                    token_ready = len(turnstile_token) > 20 or _is_turnstile_token_ready(page)
                    gate_ready = bool(
                        prepare_token
                        or bridge_message_seen
                        or gate_state.get("modalVisible")
                        or iframe_src
                        or provider_clicked
                    )

                    if turnstile_required and not token_ready:
                        if not turnstile_clicked:
                            if _click_turnstile(page, logger):
                                turnstile_clicked = True
                                page.wait_for_timeout(_random.randint(2000, 4000))
                                continue
                        elif not _is_turnstile_token_ready(page):
                            turnstile_clicked = False

                    if gate_ready and (token_ready or not turnstile_required):
                        try:
                            _neutralize_click_blockers(page)
                            if _click_submit_button(page, logger):
                                logger.warning("Submit clicked for s.to gate")
                                weiter_clicked = True
                                page.wait_for_timeout(1200)
                            else:
                                logger.warning("Submit click failed for s.to gate (will retry)")
                        except Exception as e:
                            logger.warning(f"Submit button error: {e}")
                else:
                    has_clearance = any(
                        c["name"] == "cf_clearance" for c in context.cookies()
                    )
                    if has_clearance and not post_clearance_reclick:
                        if _click_sto_provider_option(
                            page,
                            provider_name,
                            language_label,
                            expected_redirect_url=expected_redirect_url,
                        ):
                            logger.warning(
                                "Re-clicked s.to provider after Turnstile clearance"
                            )
                            page.wait_for_timeout(800)
                        post_clearance_reclick = True
                    # Weiter was clicked – poll for the VOE URL
                    for frame in page.frames:
                        if frame.name == "player-iframe":
                            fu = frame.url
                            if _sto_is_external_provider_url(fu, episode_netloc):
                                final_url = fu
                                break
                    if final_url:
                        logger.warning(f"player-iframe URL found: {final_url}")
                        break

                    if iframe_src and _sto_is_external_provider_url(iframe_src, episode_netloc):
                        final_url = iframe_src
                        logger.warning(f"player-iframe src found: {final_url}")
                        break

                    # Also check if a new tab was opened
                    for pg in context.pages:
                        if pg is not page:
                            pu = pg.url
                            if pu and pu not in ("about:blank", ""):
                                if _urlparse(pu).netloc != _urlparse(episode_url).netloc:
                                    final_url = pu
                                    break
                    if final_url:
                        logger.warning(f"New page URL found: {final_url}")
                        break

                _time.sleep(0.8)

            if final_url:
                for cookie in context.cookies():
                    GLOBAL_SESSION.cookies.set(
                        cookie["name"],
                        cookie["value"],
                        domain=cookie.get("domain", "").lstrip("."),
                    )

            if session_obj is not None:
                try:
                    session_obj._store_screenshot(page.screenshot(type="jpeg", quality=65))
                except Exception:
                    pass

            browser.close()

        with _captcha_state_lock:
            _captcha_state = None

        if session_obj is not None:
            session_obj.result_url = final_url
            session_obj.done = True
            if final_url:
                _time.sleep(2.0)

        return final_url

    except Exception as e:
        from ..logger import get_logger
        get_logger(__name__).error(f"Fehler in solve_sto_modal: {e}", exc_info=True)
        with _captcha_state_lock:
            _captcha_state = None
        return None

    finally:
        if queue_id is not None:
            if _on_captcha_end is not None:
                try:
                    _on_captcha_end(queue_id)
                except Exception:
                    pass
            with _active_sessions_lock:
                _active_sessions.pop(queue_id, None)


if __name__ == "__main__":
    # Use test.py instead :)

    """
    import niquests

    from aniworld.config import Audio, Subtitles
    from aniworld.models import SerienstreamEpisode

    ep = SerienstreamEpisode("https://s.to/serie/mr-pickles/staffel-1/episode-1")

    language = (Audio.GERMAN, Subtitles.NONE)
    provider = "VOE"

    provider_link = ep.provider_link(language=language, provider=provider)

    print(f"Redirect Link: {provider_link}")

    final_url = niquests.get(provider_link)

    if "<title>Stream wird vorbereitet...</title>" in final_url.text:
        print("Captcha detected, solving with Playwright...")
        url = playwright_get_page_url(provider_link)
    else:
        url = final_url.url

    print(f"Final URL: {url}")
    """
