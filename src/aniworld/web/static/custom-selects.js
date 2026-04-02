(() => {
  const registry = new Map();
  let openState = null;

  function closeState(state) {
    if (!state) return;
    state.shell.classList.remove("is-open");
    state.trigger.setAttribute("aria-expanded", "false");
    if (openState === state) openState = null;
  }

  function closeAll(exceptState) {
    registry.forEach((state) => {
      if (state !== exceptState) closeState(state);
    });
  }

  function syncShellState(select, state) {
    const isHidden = select.hidden || select.style.display === "none";
    state.shell.style.display = isHidden ? "none" : "";
    state.shell.classList.toggle("is-disabled", !!select.disabled);
    state.trigger.disabled = !!select.disabled;
  }

  function syncFromSelect(select) {
    const state = registry.get(select);
    if (!state) return;

    const selectedOption =
      select.options[select.selectedIndex] || select.options[0] || null;
    const selectedText = selectedOption ? selectedOption.textContent : "";

    state.label.textContent = selectedText;
    state.trigger.title = selectedText;
    state.trigger.setAttribute("aria-expanded", state.shell.classList.contains("is-open") ? "true" : "false");

    state.menu.querySelectorAll(".custom-select-option").forEach((button) => {
      const isSelected =
        Number(button.dataset.index) === Number(select.selectedIndex);
      button.classList.toggle("is-selected", isSelected);
      button.setAttribute("aria-selected", isSelected ? "true" : "false");
    });

    syncShellState(select, state);
    state.lastIndex = select.selectedIndex;
    state.lastDisabled = !!select.disabled;
    state.lastDisplay = select.style.display || "";
  }

  function buildOptionButton(select, option, optionIndex) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "custom-select-option";
    button.dataset.index = String(optionIndex);
    button.textContent = option.textContent;
    button.setAttribute("role", "option");
    button.setAttribute("aria-selected", "false");

    if (option.disabled) {
      button.disabled = true;
      button.classList.add("is-disabled");
    }

    button.addEventListener("click", () => {
      if (option.disabled) return;
      const changed = select.selectedIndex !== optionIndex;
      select.selectedIndex = optionIndex;
      syncFromSelect(select);
      closeState(registry.get(select));
      if (changed) {
        select.dispatchEvent(new Event("change", { bubbles: true }));
      }
      select.dispatchEvent(new Event("input", { bubbles: true }));
      stateFor(select).trigger.focus();
    });

    return button;
  }

  function rebuildMenu(select) {
    const state = registry.get(select);
    if (!state) return;

    const optionIndexMap = new Map(
      Array.from(select.options).map((option, index) => [option, index]),
    );
    state.menu.innerHTML = "";

    Array.from(select.children).forEach((child) => {
      if (child.tagName === "OPTGROUP") {
        const label = document.createElement("div");
        label.className = "custom-select-group-label";
        label.textContent = child.label || "";
        state.menu.appendChild(label);

        Array.from(child.children).forEach((option) => {
          if (option.hidden) return;
          state.menu.appendChild(
            buildOptionButton(select, option, optionIndexMap.get(option)),
          );
        });
        return;
      }

      if (child.tagName === "OPTION") {
        if (child.hidden) return;
        state.menu.appendChild(
          buildOptionButton(select, child, optionIndexMap.get(child)),
        );
      }
    });

    syncFromSelect(select);
  }

  function stateFor(select) {
    return registry.get(select);
  }

  function enhanceSelect(select) {
    if (
      !select ||
      registry.has(select) ||
      select.multiple ||
      Number(select.size || 0) > 1 ||
      select.dataset.nativeSelect === "true"
    ) {
      return;
    }

    const shell = document.createElement("div");
    shell.className = "custom-select-shell";
    if (select.className) {
      select.className
        .split(/\s+/)
        .filter(Boolean)
        .forEach((className) => shell.classList.add(className));
    }

    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "custom-select-trigger";
    trigger.setAttribute("aria-haspopup", "listbox");
    trigger.setAttribute("aria-expanded", "false");

    const label = document.createElement("span");
    label.className = "custom-select-label";
    trigger.appendChild(label);

    const menu = document.createElement("div");
    menu.className = "custom-select-menu";
    menu.setAttribute("role", "listbox");

    select.parentNode.insertBefore(shell, select);
    shell.appendChild(select);
    shell.appendChild(trigger);
    shell.appendChild(menu);
    select.classList.add("custom-select-native");
    select.tabIndex = -1;

    const state = {
      select,
      shell,
      trigger,
      label,
      menu,
      lastIndex: select.selectedIndex,
      lastDisabled: !!select.disabled,
      lastDisplay: select.style.display || "",
      observer: null,
    };

    trigger.addEventListener("click", () => {
      if (select.disabled) return;
      const isOpen = shell.classList.contains("is-open");
      closeAll();
      if (!isOpen) {
        shell.classList.add("is-open");
        trigger.setAttribute("aria-expanded", "true");
        openState = state;
      }
    });

    select.addEventListener("change", () => syncFromSelect(select));

    const observer = new MutationObserver(() => rebuildMenu(select));
    observer.observe(select, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["disabled", "style", "hidden", "label"],
    });
    state.observer = observer;

    registry.set(select, state);
    rebuildMenu(select);
  }

  function initCustomSelects(root = document) {
    const selects = [];
    if (root instanceof HTMLSelectElement) {
      selects.push(root);
    } else {
      if (root.querySelectorAll) {
        selects.push(...root.querySelectorAll("select"));
      }
      if (root.matches && root.matches("select")) {
        selects.push(root);
      }
    }
    selects.forEach(enhanceSelect);
  }

  document.addEventListener("pointerdown", (event) => {
    if (!openState) return;
    if (!openState.shell.contains(event.target)) {
      closeAll();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeAll();
  });

  const rootObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE) {
          initCustomSelects(node);
        }
      });
    });
  });

  window.initCustomSelects = initCustomSelects;
  window.refreshCustomSelect = function refreshCustomSelect(select) {
    if (!select) return;
    if (!registry.has(select)) {
      enhanceSelect(select);
      return;
    }
    rebuildMenu(select);
  };

  window.refreshCustomSelects = function refreshCustomSelects(root = document) {
    initCustomSelects(root);
    registry.forEach((state, select) => {
      if (!document.documentElement.contains(state.shell)) {
        if (state.observer) state.observer.disconnect();
        registry.delete(select);
        return;
      }
      if (root === document || root.contains(state.shell) || state.shell === root) {
        rebuildMenu(select);
      }
    });
  };

  setInterval(() => {
    registry.forEach((state, select) => {
      if (!document.documentElement.contains(state.shell)) {
        if (state.observer) state.observer.disconnect();
        registry.delete(select);
        return;
      }
      if (
        state.lastIndex !== select.selectedIndex ||
        state.lastDisabled !== !!select.disabled ||
        state.lastDisplay !== (select.style.display || "")
      ) {
        syncFromSelect(select);
      } else {
        syncShellState(select, state);
      }
    });
  }, 150);

  if (document.body) {
    initCustomSelects(document);
    rootObserver.observe(document.body, {
      childList: true,
      subtree: true,
    });
  } else {
    document.addEventListener(
      "DOMContentLoaded",
      () => {
        initCustomSelects(document);
        rootObserver.observe(document.body, {
          childList: true,
          subtree: true,
        });
      },
      { once: true },
    );
  }
})();
