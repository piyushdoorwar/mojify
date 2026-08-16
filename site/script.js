const emojiData = [
  {char: '😀', name: 'Grinning face', keywords: 'smile happy joy', category: 'smileys'},
  {char: '😃', name: 'Grinning face with big eyes', keywords: 'smile happy joy', category: 'smileys'},
  {char: '😄', name: 'Grinning face with smiling eyes', keywords: 'smile happy laugh', category: 'smileys'},
  {char: '😁', name: 'Beaming face', keywords: 'smile grin happy', category: 'smileys'},
  {char: '😆', name: 'Grinning squinting face', keywords: 'smile laugh happy', category: 'smileys'},
  {char: '🥹', name: 'Face holding back tears', keywords: 'smile touched grateful', category: 'smileys'},
  {char: '😊', name: 'Smiling face with smiling eyes', keywords: 'smile blush happy', category: 'smileys'},
  {char: '🙂', name: 'Slightly smiling face', keywords: 'smile happy', category: 'smileys'},
  {char: '🙃', name: 'Upside-down face', keywords: 'smile silly sarcasm', category: 'smileys'},
  {char: '😉', name: 'Winking face', keywords: 'smile wink playful', category: 'smileys'},
  {char: '😍', name: 'Smiling face with heart-eyes', keywords: 'smile love heart', category: 'smileys'},
  {char: '🥳', name: 'Partying face', keywords: 'party celebrate birthday', category: 'smileys'},
  {char: '😎', name: 'Smiling face with sunglasses', keywords: 'cool sun smile', category: 'smileys'},
  {char: '🤩', name: 'Star-struck', keywords: 'wow star smile', category: 'smileys'},
  {char: '🤗', name: 'Smiling face with open hands', keywords: 'hug smile', category: 'smileys'},
  {char: '🫡', name: 'Saluting face', keywords: 'respect yes salute', category: 'smileys'},
  {char: '👍', name: 'Thumbs up', keywords: 'yes good approve like', category: 'gestures'},
  {char: '👎', name: 'Thumbs down', keywords: 'no bad dislike', category: 'gestures'},
  {char: '👏', name: 'Clapping hands', keywords: 'applause celebrate bravo', category: 'gestures'},
  {char: '🙌', name: 'Raising hands', keywords: 'celebrate hooray praise', category: 'gestures'},
  {char: '🤝', name: 'Handshake', keywords: 'deal agree hello', category: 'gestures'},
  {char: '✌️', name: 'Victory hand', keywords: 'peace victory two', category: 'gestures'},
  {char: '🫶', name: 'Heart hands', keywords: 'love heart support', category: 'gestures'},
  {char: '👋', name: 'Waving hand', keywords: 'hello bye wave', category: 'gestures'},
  {char: '🐶', name: 'Dog face', keywords: 'pet animal puppy', category: 'animals'},
  {char: '🐱', name: 'Cat face', keywords: 'pet animal kitten', category: 'animals'},
  {char: '🦊', name: 'Fox', keywords: 'animal clever', category: 'animals'},
  {char: '🐼', name: 'Panda', keywords: 'animal bear', category: 'animals'},
  {char: '🦁', name: 'Lion', keywords: 'animal king', category: 'animals'},
  {char: '🐸', name: 'Frog', keywords: 'animal green', category: 'animals'},
  {char: '🍕', name: 'Pizza', keywords: 'food slice cheese', category: 'food'},
  {char: '🍔', name: 'Hamburger', keywords: 'food burger lunch', category: 'food'},
  {char: '🍜', name: 'Steaming bowl', keywords: 'food noodles soup', category: 'food'},
  {char: '☕', name: 'Hot beverage', keywords: 'coffee tea drink', category: 'food'},
  {char: '🍉', name: 'Watermelon', keywords: 'fruit food summer', category: 'food'},
  {char: '🎂', name: 'Birthday cake', keywords: 'food birthday party', category: 'food'},
  {char: '🚀', name: 'Rocket', keywords: 'space launch fast ship', category: 'travel'},
  {char: '✈️', name: 'Airplane', keywords: 'travel flight plane', category: 'travel'},
  {char: '🚗', name: 'Automobile', keywords: 'travel car drive', category: 'travel'},
  {char: '🚲', name: 'Bicycle', keywords: 'travel bike cycle', category: 'travel'},
  {char: '🏕️', name: 'Camping', keywords: 'travel tent outdoors', category: 'travel'},
  {char: '🗺️', name: 'World map', keywords: 'travel map world', category: 'travel'},
  {char: '🎉', name: 'Party popper', keywords: 'party celebrate tada', category: 'objects'},
  {char: '🔥', name: 'Fire', keywords: 'hot flame lit', category: 'objects'},
  {char: '💡', name: 'Light bulb', keywords: 'idea light smart', category: 'objects'},
  {char: '🎁', name: 'Wrapped gift', keywords: 'present birthday surprise', category: 'objects'},
  {char: '💻', name: 'Laptop', keywords: 'computer code work', category: 'objects'},
  {char: '🎧', name: 'Headphone', keywords: 'music audio listen', category: 'objects'},
  {char: '❤️', name: 'Red heart', keywords: 'love heart like', category: 'symbols'},
  {char: '✨', name: 'Sparkles', keywords: 'star shine magic', category: 'symbols'},
  {char: '✅', name: 'Check mark button', keywords: 'yes done success', category: 'symbols'},
  {char: '⭐', name: 'Star', keywords: 'favorite rating shine', category: 'symbols'},
  {char: '💚', name: 'Green heart', keywords: 'love heart mint', category: 'symbols'},
  {char: '⚡', name: 'High voltage', keywords: 'lightning fast energy', category: 'symbols'}
];

const recentChars = ['😄', '🚀', '✨', '🔥', '👍', '❤️', '🎉', '💡', '😂', '✅', '🙏', '👀', '💚', '🥳'];
const extraRecent = [
  {char: '😂', name: 'Face with tears of joy', keywords: 'laugh cry funny', category: 'smileys'},
  {char: '🙏', name: 'Folded hands', keywords: 'please thanks pray', category: 'gestures'},
  {char: '👀', name: 'Eyes', keywords: 'look watch see', category: 'gestures'}
];

const allEmoji = [...emojiData, ...extraRecent];
const grid = document.querySelector('#emojiGrid');
const searchInput = document.querySelector('#emojiSearch');
const emojiName = document.querySelector('#emojiName');
const tabs = [...document.querySelectorAll('.category-tab')];
const toast = document.querySelector('#copiedToast');
const toastEmoji = document.querySelector('#toastEmoji');
let activeCategory = 'recent';
let selectedIndex = 0;
let visibleEmoji = [];
let toastTimer;

function getVisibleEmoji() {
  const query = searchInput.value.trim().toLowerCase();

  if (query) {
    return allEmoji.filter((emoji) =>
      `${emoji.name} ${emoji.keywords}`.toLowerCase().includes(query)
    ).slice(0, 21);
  }

  if (activeCategory === 'recent') {
    return recentChars
      .map((char) => allEmoji.find((emoji) => emoji.char === char))
      .filter(Boolean);
  }

  return emojiData.filter((emoji) => emoji.category === activeCategory);
}

function setSelected(index) {
  if (!visibleEmoji.length) return;
  selectedIndex = Math.max(0, Math.min(index, visibleEmoji.length - 1));
  const buttons = [...grid.querySelectorAll('.emoji-button')];

  buttons.forEach((button, buttonIndex) => {
    button.classList.toggle('is-selected', buttonIndex === selectedIndex);
  });

  emojiName.textContent = visibleEmoji[selectedIndex].name;
}

function renderEmoji() {
  visibleEmoji = getVisibleEmoji();
  selectedIndex = 0;
  grid.replaceChildren();

  if (!visibleEmoji.length) {
    const empty = document.createElement('p');
    empty.className = 'empty-results';
    empty.textContent = 'No emoji found. Try another word.';
    grid.append(empty);
    emojiName.textContent = 'No results';
    return;
  }

  const fragment = document.createDocumentFragment();
  visibleEmoji.forEach((emoji, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'emoji-button';
    button.textContent = emoji.char;
    button.title = emoji.name;
    button.setAttribute('aria-label', `Copy ${emoji.name}`);
    button.addEventListener('mouseenter', () => {
      selectedIndex = index;
      emojiName.textContent = emoji.name;
      grid.querySelectorAll('.emoji-button').forEach((item, itemIndex) => {
        item.classList.toggle('is-selected', itemIndex === index);
      });
    });
    button.addEventListener('focus', () => setSelected(index));
    button.addEventListener('click', () => copyEmoji(emoji));
    fragment.append(button);
  });

  grid.append(fragment);
  setSelected(0);
}

async function writeClipboard(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return true;
  }

  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.append(textarea);
  textarea.select();
  const copied = document.execCommand('copy');
  textarea.remove();
  return copied;
}

async function copyEmoji(emoji) {
  try {
    await writeClipboard(emoji.char);
  } catch {
    // The interactive notification remains useful when browser clipboard
    // permission is unavailable (for example, inside a local preview iframe).
  }

  toastEmoji.textContent = emoji.char;
  toast.classList.add('is-visible');
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.classList.remove('is-visible'), 1800);
}

tabs.forEach((tab) => {
  tab.addEventListener('click', () => {
    activeCategory = tab.dataset.category;
    searchInput.value = '';
    tabs.forEach((item) => {
      const active = item === tab;
      item.classList.toggle('is-active', active);
      item.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    renderEmoji();
    searchInput.focus();
  });
});

searchInput.addEventListener('input', () => {
  const searching = Boolean(searchInput.value.trim());
  tabs.forEach((tab) => {
    tab.classList.toggle('is-active', !searching && tab.dataset.category === activeCategory);
    tab.setAttribute('aria-selected', !searching && tab.dataset.category === activeCategory ? 'true' : 'false');
  });
  renderEmoji();
});

searchInput.addEventListener('keydown', (event) => {
  if (!visibleEmoji.length) return;
  const columns = window.matchMedia('(max-width: 540px)').matches ? 5 : 7;

  if (event.key === 'ArrowRight') {
    event.preventDefault();
    setSelected((selectedIndex + 1) % visibleEmoji.length);
  } else if (event.key === 'ArrowLeft') {
    event.preventDefault();
    setSelected((selectedIndex - 1 + visibleEmoji.length) % visibleEmoji.length);
  } else if (event.key === 'ArrowDown') {
    event.preventDefault();
    setSelected(Math.min(selectedIndex + columns, visibleEmoji.length - 1));
  } else if (event.key === 'ArrowUp') {
    event.preventDefault();
    setSelected(Math.max(selectedIndex - columns, 0));
  } else if (event.key === 'Enter') {
    event.preventDefault();
    copyEmoji(visibleEmoji[selectedIndex]);
  } else if (event.key === 'Escape') {
    searchInput.value = '';
    searchInput.dispatchEvent(new Event('input'));
  }
});

document.querySelectorAll('.copy-button').forEach((button) => {
  button.addEventListener('click', async () => {
    const label = button.querySelector('span');
    const original = label.textContent;
    try {
      const copied = await writeClipboard(button.dataset.copy);
      label.textContent = copied ? 'Copied' : 'Select';
    } catch {
      label.textContent = 'Select';
    }
    window.setTimeout(() => { label.textContent = original; }, 1500);
  });
});

const typingDemo = document.querySelector('#typingDemo');
const typingWords = ['rocket', 'party', 'heart', 'coffee'];
let typingWordIndex = 0;

function animateTypingWord() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const nextWord = typingWords[typingWordIndex % typingWords.length];
  let length = 0;
  typingDemo.textContent = '';

  const timer = window.setInterval(() => {
    length += 1;
    typingDemo.textContent = nextWord.slice(0, length);
    if (length === nextWord.length) {
      window.clearInterval(timer);
      typingWordIndex += 1;
      window.setTimeout(animateTypingWord, 1700);
    }
  }, 95);
}

renderEmoji();
window.setTimeout(animateTypingWord, 900);
