/*
 * Mojify site behaviour: mobile menu, copy buttons, scroll reveal,
 * the interactive picker preview and the typing demo.
 */
(function () {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---- Mobile navigation ------------------------------------------------
  const topbar = document.querySelector(".topbar");
  const toggle = document.querySelector(".nav-toggle");
  if (topbar && toggle) {
    const setOpen = (open) => {
      topbar.classList.toggle("open", open);
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    };
    toggle.addEventListener("click", () => setOpen(!topbar.classList.contains("open")));
    topbar.querySelectorAll(".nav a").forEach((a) => a.addEventListener("click", () => setOpen(false)));
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") setOpen(false);
    });
  }

  // ---- Clipboard --------------------------------------------------------
  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      let ok = false;
      try {
        ok = document.execCommand("copy");
      } catch {
        ok = false;
      }
      ta.remove();
      return ok;
    }
  }

  // ---- Copy buttons -----------------------------------------------------
  document.addEventListener("click", async (event) => {
    const btn = event.target.closest(".copy-btn");
    if (!btn) return;
    const text = btn.dataset.copy ?? btn.closest(".cmd")?.querySelector("code")?.innerText ?? "";
    const ok = await copyText(text);
    const label = btn.querySelector("span");
    btn.classList.toggle("done", ok);
    if (label) label.textContent = ok ? "Copied" : "Press Ctrl+C";
    clearTimeout(btn._timer);
    btn._timer = setTimeout(() => {
      btn.classList.remove("done");
      if (label) label.textContent = "Copy";
    }, 1800);
  });

  // ---- Scroll reveal ----------------------------------------------------
  const revealEls = document.querySelectorAll("[data-reveal]");
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          // Elements above the viewport (after an anchor jump or reload) are shown as well.
          if (entry.isIntersecting || entry.boundingClientRect.top < 0) {
            entry.target.classList.add("in");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.08, rootMargin: "0px 0px -40px 0px" }
    );
    revealEls.forEach((el) => observer.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("in"));
  }

  // ---- Picker preview ---------------------------------------------------
  // A small sample of the bundled set: [emoji, name, keywords, category].
  const EMOJI = [
    ["😀", "Grinning face", "smile happy joy", "smileys"],
    ["😃", "Grinning face with big eyes", "smile happy joy", "smileys"],
    ["😄", "Grinning face with smiling eyes", "smile happy laugh", "smileys"],
    ["😁", "Beaming face with smiling eyes", "smile grin happy", "smileys"],
    ["😆", "Grinning squinting face", "smile laugh happy", "smileys"],
    ["😂", "Face with tears of joy", "laugh cry funny", "smileys"],
    ["🥹", "Face holding back tears", "smile touched grateful", "smileys"],
    ["😊", "Smiling face with smiling eyes", "smile blush happy", "smileys"],
    ["🙂", "Slightly smiling face", "smile happy", "smileys"],
    ["🙃", "Upside-down face", "smile silly sarcasm", "smileys"],
    ["😉", "Winking face", "smile wink playful", "smileys"],
    ["😍", "Smiling face with heart-eyes", "smile love heart", "smileys"],
    ["🥳", "Partying face", "party celebrate birthday", "smileys"],
    ["😎", "Smiling face with sunglasses", "cool sun smile", "smileys"],
    ["🤩", "Star-struck", "wow star smile", "smileys"],
    ["🤗", "Smiling face with open hands", "hug smile", "smileys"],
    ["🫡", "Saluting face", "respect yes salute", "smileys"],
    ["🤔", "Thinking face", "hmm think wonder", "smileys"],
    ["😴", "Sleeping face", "tired sleep zzz", "smileys"],
    ["👍", "Thumbs up", "yes good approve like", "gestures"],
    ["👎", "Thumbs down", "no bad dislike", "gestures"],
    ["👏", "Clapping hands", "applause celebrate bravo", "gestures"],
    ["🙌", "Raising hands", "celebrate hooray praise", "gestures"],
    ["🤝", "Handshake", "deal agree hello", "gestures"],
    ["✌️", "Victory hand", "peace victory two", "gestures"],
    ["🫶", "Heart hands", "love heart support", "gestures"],
    ["👋", "Waving hand", "hello bye wave", "gestures"],
    ["🙏", "Folded hands", "please thanks pray", "gestures"],
    ["👀", "Eyes", "look watch see", "gestures"],
    ["🧑‍💻", "Technologist", "developer coder computer", "people"],
    ["🧑‍🍳", "Cook", "chef kitchen food", "people"],
    ["🧑‍🎨", "Artist", "painter art", "people"],
    ["🧑‍🚀", "Astronaut", "space rocket", "people"],
    ["🧙", "Mage", "wizard magic", "people"],
    ["🥷", "Ninja", "stealth fighter", "people"],
    ["🐶", "Dog face", "pet animal puppy", "animals"],
    ["🐱", "Cat face", "pet animal kitten", "animals"],
    ["🦊", "Fox", "animal clever", "animals"],
    ["🐼", "Panda", "animal bear", "animals"],
    ["🦁", "Lion", "animal king", "animals"],
    ["🐸", "Frog", "animal green", "animals"],
    ["🦉", "Owl", "bird night wise", "animals"],
    ["🐢", "Turtle", "slow animal", "animals"],
    ["🍕", "Pizza", "food slice cheese", "food"],
    ["🍔", "Hamburger", "food burger lunch", "food"],
    ["🍜", "Steaming bowl", "food noodles soup ramen", "food"],
    ["☕", "Hot beverage", "coffee tea drink", "food"],
    ["🍉", "Watermelon", "fruit food summer", "food"],
    ["🎂", "Birthday cake", "food birthday party", "food"],
    ["🥑", "Avocado", "fruit food green", "food"],
    ["🚀", "Rocket", "space launch fast ship", "travel"],
    ["✈️", "Airplane", "travel flight plane", "travel"],
    ["🚗", "Automobile", "travel car drive", "travel"],
    ["🚲", "Bicycle", "travel bike cycle", "travel"],
    ["🏕️", "Camping", "travel tent outdoors", "travel"],
    ["🗺️", "World map", "travel map world", "travel"],
    ["⚽", "Soccer ball", "football sport game", "activities"],
    ["🏀", "Basketball", "sport game hoop", "activities"],
    ["🎮", "Video game", "controller play gaming", "activities"],
    ["🎯", "Bullseye", "target goal dart", "activities"],
    ["🎸", "Guitar", "music rock", "activities"],
    ["🏆", "Trophy", "win award prize", "activities"],
    ["🎉", "Party popper", "party celebrate tada", "objects"],
    ["🔥", "Fire", "hot flame lit", "objects"],
    ["💡", "Light bulb", "idea light smart", "objects"],
    ["🎁", "Wrapped gift", "present birthday surprise", "objects"],
    ["💻", "Laptop", "computer code work", "objects"],
    ["🎧", "Headphone", "music audio listen", "objects"],
    ["📌", "Pushpin", "pin location note", "objects"],
    ["❤️", "Red heart", "love heart like", "symbols"],
    ["💚", "Green heart", "love heart mint", "symbols"],
    ["✨", "Sparkles", "star shine magic", "symbols"],
    ["✅", "Check mark button", "yes done success", "symbols"],
    ["⭐", "Star", "favorite rating shine", "symbols"],
    ["⚡", "High voltage", "lightning fast energy", "symbols"],
    ["💯", "Hundred points", "perfect score full", "symbols"],
    ["➡️", "Right arrow", "next direction", "arrows"],
    ["⬅️", "Left arrow", "back previous direction", "arrows"],
    ["⬆️", "Up arrow", "top direction", "arrows"],
    ["⬇️", "Down arrow", "bottom direction", "arrows"],
    ["🔄", "Counterclockwise arrows", "refresh repeat sync", "arrows"],
    ["↩️", "Right arrow curving left", "return undo reply", "arrows"],
    ["🏁", "Chequered flag", "finish race", "flags"],
    ["🚩", "Triangular flag", "warning red flag", "flags"],
    ["🏳️", "White flag", "surrender peace", "flags"],
    ["🏴", "Black flag", "pirate flag", "flags"],
    ["🏳️‍🌈", "Rainbow flag", "pride rainbow", "flags"],
  ].map(([char, name, keywords, category]) => ({ char, name, keywords, category }));

  const RECENT = ["😄", "🚀", "✨", "🔥", "👍", "❤️", "🎉", "💡", "😂", "✅", "🙏", "👀", "💚", "🥳"];
  const COLUMNS = 7;

  const picker = document.getElementById("picker");
  const grid = document.getElementById("pkGrid");
  const search = document.getElementById("pkSearch");
  const nameEl = document.getElementById("pkName");
  const toast = document.getElementById("toast");
  const toastEmoji = document.getElementById("toastEmoji");

  if (picker && grid && search && nameEl) {
    const tabs = Array.from(picker.querySelectorAll(".pk-tab"));
    let category = "recent";
    let visible = [];
    let selected = 0;
    let toastTimer;

    const byChar = (c) => EMOJI.find((e) => e.char === c);

    const currentList = () => {
      const q = search.value.trim().toLowerCase();
      if (q) {
        // Like the app: match the start of any word in the name or keywords.
        return EMOJI.filter((e) =>
          `${e.name} ${e.keywords}`.toLowerCase().split(/[\s-]+/).some((w) => w.startsWith(q))
        );
      }
      if (category === "recent") return RECENT.map(byChar).filter(Boolean);
      return EMOJI.filter((e) => e.category === category);
    };

    const select = (index, scroll) => {
      if (!visible.length) return;
      selected = Math.max(0, Math.min(index, visible.length - 1));
      grid.querySelectorAll(".pk-cell").forEach((cell, i) => cell.classList.toggle("sel", i === selected));
      nameEl.textContent = visible[selected].name;
      if (scroll) {
        const cell = grid.children[selected];
        const top = cell.offsetTop - grid.offsetTop;
        if (top < grid.scrollTop) grid.scrollTop = top - 4;
        else if (top + cell.offsetHeight > grid.scrollTop + grid.clientHeight) grid.scrollTop = top + cell.offsetHeight - grid.clientHeight + 4;
      }
    };

    const syncTabs = () => {
      const searching = Boolean(search.value.trim());
      tabs.forEach((tab) => {
        const on = !searching && tab.dataset.category === category;
        tab.classList.toggle("on", on);
        tab.setAttribute("aria-selected", String(on));
      });
    };

    const render = () => {
      visible = currentList();
      grid.replaceChildren();
      grid.scrollTop = 0;
      if (!visible.length) {
        const empty = document.createElement("p");
        empty.className = "pk-empty";
        empty.textContent = "No emoji found. Try another word.";
        grid.append(empty);
        nameEl.textContent = "No results";
        return;
      }
      const frag = document.createDocumentFragment();
      visible.forEach((e, i) => {
        const cell = document.createElement("button");
        cell.type = "button";
        cell.className = "pk-cell emoji";
        cell.textContent = e.char;
        cell.title = e.name;
        cell.setAttribute("aria-label", `Copy ${e.name}`);
        cell.addEventListener("mouseenter", () => select(i));
        cell.addEventListener("focus", () => select(i));
        cell.addEventListener("click", () => pick(e));
        frag.append(cell);
      });
      grid.append(frag);
      select(0);
    };

    const pick = async (e) => {
      await copyText(e.char).catch(() => false);
      if (!toast || !toastEmoji) return;
      toastEmoji.textContent = e.char;
      toast.classList.add("show");
      clearTimeout(toastTimer);
      toastTimer = setTimeout(() => toast.classList.remove("show"), 1800);
    };

    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        category = tab.dataset.category;
        search.value = "";
        syncTabs();
        render();
      });
    });

    search.addEventListener("input", () => {
      syncTabs();
      render();
    });

    search.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        search.value = "";
        syncTabs();
        render();
        return;
      }
      if (!visible.length) return;
      const moves = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: COLUMNS, ArrowUp: -COLUMNS };
      if (e.key in moves) {
        e.preventDefault();
        select(selected + moves[e.key], true);
      } else if (e.key === "Enter") {
        e.preventDefault();
        pick(visible[selected]);
      }
    });

    render();
  }

  // ---- Typing demo ------------------------------------------------------
  const typing = document.getElementById("typingDemo");
  if (typing && !reduceMotion) {
    const words = ["rocket", "party", "heart", "coffee"];
    let w = 0;
    const type = () => {
      const word = words[w % words.length];
      let n = 0;
      typing.textContent = "";
      const timer = setInterval(() => {
        n += 1;
        typing.textContent = word.slice(0, n);
        if (n === word.length) {
          clearInterval(timer);
          w += 1;
          setTimeout(type, 1700);
        }
      }, 95);
    };
    setTimeout(type, 900);
  }
})();
