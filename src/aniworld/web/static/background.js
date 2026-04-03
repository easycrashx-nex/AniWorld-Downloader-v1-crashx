(function initParticleNetwork() {
  if (window.__aniworldParticleNetworkInitialized) return;
  window.__aniworldParticleNetworkInitialized = true;

  const canvas = document.getElementById("networkCanvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const prefersReducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;

  let width = 0;
  let height = 0;
  let points = [];
  let animationFrame = null;
  let deviceScale = 1;
  let pointerX = null;
  let pointerY = null;

  function getBackgroundMode() {
    const mode = document.body?.dataset?.uiBackground || "dynamic";
    return mode === "subtle" || mode === "off" ? mode : "dynamic";
  }

  function getMotionFactor() {
    const mode = getBackgroundMode();
    if (prefersReducedMotion || mode === "off") return 0;
    return mode === "subtle" ? 0.07 : 0.18;
  }

  function pointCountForViewport() {
    const mode = getBackgroundMode();
    const areaFactor = mode === "subtle" ? 34000 : 26000;
    const minPoints = mode === "subtle" ? 20 : 36;
    const maxPoints = mode === "subtle" ? 54 : 96;
    return Math.max(
      minPoints,
      Math.min(maxPoints, Math.round((width * height) / areaFactor)),
    );
  }

  function createPoint() {
    const speedFactor = getMotionFactor();
    return {
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * speedFactor,
      vy: (Math.random() - 0.5) * speedFactor,
    };
  }

  function resizeCanvas() {
    width = window.innerWidth;
    height = window.innerHeight;
    deviceScale = Math.min(window.devicePixelRatio || 1, 2);

    canvas.width = Math.floor(width * deviceScale);
    canvas.height = Math.floor(height * deviceScale);
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
    ctx.setTransform(deviceScale, 0, 0, deviceScale, 0, 0);

    const targetCount = pointCountForViewport();
    points = Array.from({ length: targetCount }, createPoint);

    drawFrame();
  }

  function updatePoints() {
    const mode = getBackgroundMode();
    if (prefersReducedMotion || mode === "off") return;

    for (const point of points) {
      point.x += point.vx;
      point.y += point.vy;

      if (point.x <= 0 || point.x >= width) point.vx *= -1;
      if (point.y <= 0 || point.y >= height) point.vy *= -1;

      point.x = Math.max(0, Math.min(width, point.x));
      point.y = Math.max(0, Math.min(height, point.y));

      if (pointerX === null || pointerY === null) continue;

      const dx = point.x - pointerX;
      const dy = point.y - pointerY;
      const distSq = dx * dx + dy * dy;
      if (distSq > 0 && distSq < 110 * 110) {
        const force = (110 * 110 - distSq) / (110 * 110);
        point.x += (dx / Math.sqrt(distSq)) * force * 0.8;
        point.y += (dy / Math.sqrt(distSq)) * force * 0.8;
      }
    }
  }

  function nearestConnections(index) {
    const current = points[index];
    const mode = getBackgroundMode();
    const maxDistance = mode === "subtle" ? 138 : 165;
    const neighbors = [];

    for (let otherIndex = 0; otherIndex < points.length; otherIndex += 1) {
      if (otherIndex === index) continue;
      const other = points[otherIndex];
      const dx = other.x - current.x;
      const dy = other.y - current.y;
      const distance = Math.hypot(dx, dy);
      if (distance <= maxDistance) {
        neighbors.push({ index: otherIndex, distance });
      }
    }

    neighbors.sort((a, b) => a.distance - b.distance);
    return neighbors.slice(0, 4);
  }

  function drawFrame() {
    const mode = getBackgroundMode();
    canvas.style.opacity = mode === "off" ? "0" : mode === "subtle" ? "0.46" : "0.85";
    ctx.clearRect(0, 0, width, height);
    if (mode === "off") return;

    const renderedEdges = new Set();

    for (let index = 0; index < points.length; index += 1) {
      const point = points[index];
      const neighbors = nearestConnections(index);

      for (const neighbor of neighbors) {
        const edgeKey =
          index < neighbor.index
            ? `${index}:${neighbor.index}`
            : `${neighbor.index}:${index}`;

        if (renderedEdges.has(edgeKey)) continue;
        renderedEdges.add(edgeKey);

        const target = points[neighbor.index];
        const alphaBase = mode === "subtle" ? 0.22 : 0.42;
        const alpha = Math.max(0.04, 1 - neighbor.distance / 165) * alphaBase;

        ctx.beginPath();
        ctx.moveTo(point.x, point.y);
        ctx.lineTo(target.x, target.y);
        ctx.strokeStyle = `rgba(130, 205, 255, ${alpha})`;
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    }

    for (const point of points) {
      const highlight =
        pointerX !== null &&
        pointerY !== null &&
        Math.hypot(point.x - pointerX, point.y - pointerY) < 120;

      ctx.beginPath();
      ctx.arc(point.x, point.y, highlight ? 2.2 : mode === "subtle" ? 1.4 : 1.8, 0, Math.PI * 2);
      ctx.fillStyle = highlight
        ? "rgba(120, 235, 220, 0.95)"
        : mode === "subtle"
          ? "rgba(166, 223, 255, 0.62)"
          : "rgba(166, 223, 255, 0.9)";
      ctx.fill();
    }
  }

  function tick() {
    updatePoints();
    drawFrame();
    if (!prefersReducedMotion && getBackgroundMode() !== "off") {
      animationFrame = window.requestAnimationFrame(tick);
    } else {
      animationFrame = null;
    }
  }

  function refreshBackgroundMode() {
    resizeCanvas();
    if (animationFrame) {
      window.cancelAnimationFrame(animationFrame);
      animationFrame = null;
    }
    if (!prefersReducedMotion && getBackgroundMode() !== "off") {
      animationFrame = window.requestAnimationFrame(tick);
    } else {
      drawFrame();
    }
  }

  window.addEventListener("resize", resizeCanvas, { passive: true });
  window.addEventListener(
    "mousemove",
    (event) => {
      pointerX = event.clientX;
      pointerY = event.clientY;
    },
    { passive: true },
  );
  window.addEventListener(
    "mouseleave",
    () => {
      pointerX = null;
      pointerY = null;
    },
    { passive: true },
  );
  document.addEventListener(
    "visibilitychange",
    () => {
      if (document.hidden) {
        if (animationFrame) {
          window.cancelAnimationFrame(animationFrame);
          animationFrame = null;
        }
      } else if (!prefersReducedMotion && !animationFrame) {
        animationFrame = window.requestAnimationFrame(tick);
      } else {
        drawFrame();
      }
    },
    { passive: true },
  );
  document.addEventListener("aniworld:ui-background", refreshBackgroundMode, {
    passive: true,
  });

  resizeCanvas();

  if (!prefersReducedMotion && getBackgroundMode() !== "off") {
    animationFrame = window.requestAnimationFrame(tick);
  } else {
    drawFrame();
  }
})();
