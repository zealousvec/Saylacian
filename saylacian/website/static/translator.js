// SPDX-License-Identifier: AGPL-3.0-or-later
/* Local website helpers. Input is submitted only by the Convert action. */
"use strict";
(() => {
  const form = document.querySelector("#translator");
  const input = document.querySelector("#input");
  const output = document.querySelector("#output");
  const source = document.querySelector("#source");
  const target = document.querySelector("#target");
  const mode = document.querySelector("#mode");
  const status = document.querySelector("#status");
  const submit = document.querySelector("#convert");
  let request = null;
  let generation = 0;
  let resultSelection = output.value ? [source.value, target.value, mode.value] : null;

  function invalidate() {
    generation += 1;
    if (request) request.abort();
    request = null;
    submit.disabled = false;
    output.value = "";
    resultSelection = null;
  }
  function changed() {
    invalidate();
    status.textContent = "Text or selection changed. Choose Convert for a new result.";
  }
  input.addEventListener("input", changed);
  for (const control of [source, target, mode]) control.addEventListener("change", changed);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    invalidate();
    const current = generation;
    request = new AbortController();
    submit.disabled = true;
    status.textContent = "Processing on this server...";
    try {
      const response = await fetch(form.action, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({text: input.value, source: source.value, target: target.value, mode: mode.value}),
        signal: request.signal
      });
      const result = await response.json();
      if (current !== generation) return;
      if (!response.ok) throw new Error(result.error || "Conversion failed.");
      output.value = result.text;
      resultSelection = [source.value, target.value, mode.value];
      status.textContent = "Alpha testing. " + (result.warnings.join(" ") || "Conversion completed.");
    } catch (error) {
      if (current !== generation || error.name === "AbortError") return;
      output.value = "";
      status.textContent = error.message || "Could not reach this server. Input is preserved.";
    } finally {
      if (current === generation) {
        submit.disabled = false;
        request = null;
      }
    }
  });

  document.querySelector("#swap").addEventListener("click", () => {
    if (source.value === "Detect language/script") {
      status.textContent = "Select an explicit source before swapping.";
      return;
    }
    const previous = source.value;
    const result = resultSelection ? output.value : "";
    source.value = target.value;
    target.value = previous;
    if (result) input.value = result;
    changed();
  });
  document.querySelector("#clear").addEventListener("click", () => {
    input.value = "";
    invalidate();
    status.textContent = "Cleared.";
    input.focus();
  });
  document.querySelector("#copy").addEventListener("click", async () => {
    if (!output.value) { status.textContent = "No result to copy."; return; }
    try {
      await navigator.clipboard.writeText(output.value);
      status.textContent = "Result copied.";
    } catch {
      output.focus();
      output.select();
      status.textContent = "Clipboard access unavailable. Result selected for manual copy.";
    }
  });
  document.querySelector("#paste").addEventListener("click", async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text.length > 4000) { status.textContent = "Clipboard exceeds 4,000 characters. Input preserved."; return; }
      input.value = text;
      changed();
    } catch {
      status.textContent = "Clipboard access unavailable. Paste directly into the input field.";
      input.focus();
    }
  });
  for (const button of document.querySelectorAll("[data-glyph]")) {
    button.addEventListener("click", () => {
      if (source.value !== "Osmanya") { status.textContent = "Choose Osmanya as source before inserting letters."; return; }
      const start = input.selectionStart;
      const end = input.selectionEnd;
      const value = input.value.slice(0, start) + button.dataset.glyph + input.value.slice(end);
      if (value.length > 4000) { status.textContent = "Maximum 4,000 characters."; return; }
      input.value = value;
      input.setSelectionRange(start + button.dataset.glyph.length, start + button.dataset.glyph.length);
      changed();
    });
  }
})();
