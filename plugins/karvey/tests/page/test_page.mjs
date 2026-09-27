// Method page docs/karvey.html: the inline script's pure functions and init(window) against a stub
// window (E1.F11.T2; BUG-10..13, REQ-W1-102..105; nine languages: REQ-W3-066, 068). node:test only, no npm (Q-A7 / D-09).
// @req REQ-W3-066 REQ-W3-068 REQ-W3-069 REQ-ADP-031
// Run:
//   node --test plugins/karvey/tests/page/
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import vm from 'node:vm';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PAGE = path.resolve(HERE, '../../../../docs/karvey.html');
const html = readFileSync(PAGE, 'utf8');

function mainScript() {
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  const s = scripts.find((x) => x.includes('safeDecodeHash'));
  assert.ok(s, 'the main inline script defines safeDecodeHash');
  return s;
}

function load() {
  const sandbox = { module: { exports: {} }, URLSearchParams };
  vm.runInNewContext(mainScript(), sandbox, { filename: 'karvey.html#main' });
  return sandbox.module.exports;
}

const P = load();

// ---------------------------------------------------------------- a stub window
class El {
  constructor(attrs = {}, id = null) {
    this.attrs = { ...attrs };
    this.id = id;
    this.hidden = false;
    this.textContent = '';
    this.listeners = {};
    this.scrolled = 0;
    this.children = [];
    this.style = {};
    this.lang = '';
  }
  getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  removeAttribute(k) { delete this.attrs[k]; }
  addEventListener(ev, fn) { (this.listeners[ev] ||= []).push(fn); }
  querySelectorAll() { return []; }
  querySelector(sel) { return sel === 'main' ? (this.main ||= new El()) : null; }
  scrollIntoView() { this.scrolled += 1; }
}

function makeWindow({ search = '', hash = '', saved = null, languages = ['en'], ids = [], storageThrows = false } = {}) {
  const NINE = ['en', 'es', 'pt', 'de', 'zh', 'it', 'ja', 'fr', 'ko'];
  const blocks = NINE.map((l) => new El({ 'data-lang': l, lang: l === 'zh' ? 'zh-Hans' : l }));
  const links = NINE.map((l) => new El({ 'data-set-lang': l }));
  const byId = {};
  for (const id of ids) byId[id] = new El({}, id);
  const note = new El({}, 'lang-note');
  note.hidden = true;
  byId['lang-note'] = note;
  byId['lang-label'] = new El({}, 'lang-label');
  const nav = new El({ class: 'langs' });
  nav.hidden = true;
  const classes = new Set();
  const root = new El();
  root.classList = { add: (c) => classes.add(c), has: (c) => classes.has(c) };
  const store = {};
  if (saved !== null) store['karvey-lang'] = saved;
  const history = [];
  const listeners = {};
  const doc = {
    documentElement: root,
    title: '',
    querySelectorAll(sel) {
      if (sel === '.lang-block[data-lang]') return blocks;
      if (sel === '.langs a[data-set-lang]') return links;
      return [];
    },
    querySelector(sel) {
      if (sel === '.langs') return nav;
      if (sel === '.skip') return (this._skip ||= new El());
      if (sel === '.brand') return (this._brand ||= new El());
      return null;
    },
    getElementById: (id) => byId[id] || null,
  };
  const w = {
    document: doc,
    location: { pathname: '/karvey.html', search, hash },
    history: {
      replaceState(_s, _t, url) {
        history.push(url);
        const m = /^([^?#]*)(\?[^#]*)?(#.*)?$/.exec(url);
        w.location.search = m[2] || '';
        w.location.hash = m[3] || '';
      },
    },
    navigator: { languages, language: languages[0] },
    addEventListener(ev, fn) { (listeners[ev] ||= []).push(fn); },
    scrollY: 0,
  };
  Object.defineProperty(w, 'localStorage', {
    get() {
      if (storageThrows) throw new Error('SecurityError');
      return { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); } };
    },
  });
  return { w, root, classes, nav, note, links, byId, store, history, listeners };
}

function click(link) {
  const ev = { defaultPrevented: false, button: 0, preventDefault() { this.defaultPrevented = true; } };
  for (const fn of link.listeners.click || []) fn(ev);
  return ev;
}

// ---------------------------------------------------------------- safeDecodeHash (BUG-10)
test('safeDecodeHash decodes a valid hash', () => {
  assert.equal(P.safeDecodeHash('#en-phases'), 'en-phases');
  assert.equal(P.safeDecodeHash('#es-%C3%B1'), 'es-ñ');
});

test('safeDecodeHash returns null for a malformed or empty hash, never throws (BUG-10)', () => {
  assert.equal(P.safeDecodeHash('#%E0%A4%A'), null);
  assert.equal(P.safeDecodeHash('#'), null);
  assert.equal(P.safeDecodeHash(''), null);
  assert.equal(P.safeDecodeHash(undefined), null);
});

// ---------------------------------------------------------------- langOf / pickLang (BUG-11)
test('langOf reads xx and xx-YY by the first two letters, only for the nine languages', () => {
  assert.equal(P.langOf('de'), 'de');
  assert.equal(P.langOf('ES-cl'), 'es');
  assert.equal(P.langOf('zh-TW'), 'zh');
  assert.equal(P.langOf('pt_BR'), 'pt');
  assert.equal(P.langOf('xx'), null);
  assert.equal(P.langOf('fr-FR'), 'fr');
  assert.equal(P.langOf('ko-KR'), 'ko');
  assert.equal(P.langOf('ja'), 'ja');
  assert.equal(P.langOf('it_IT'), 'it');
  assert.equal(P.langOf('nl'), null);
  assert.equal(P.langOf('english'), null);
  assert.equal(P.langOf(null), null);
});

test('pickLang: a ?lang= link is one-off when a choice was saved (BUG-11, REQ-W1-103)', () => {
  const r = P.pickLang('?lang=es', 'de', ['en-US']);
  assert.equal(r.lang, 'es');
  assert.equal(r.source, 'url');
  assert.equal(r.remember, false);
});

test('pickLang: a valid ?lang= is remembered when nothing was saved', () => {
  const r = P.pickLang('?foo=1&lang=pt-BR', null, ['en']);
  assert.equal(r.lang, 'pt');
  assert.equal(r.remember, true);
});

test('pickLang: an invalid ?lang= is ignored and nothing is saved; the browser rule applies', () => {
  const r = P.pickLang('?lang=xx', null, ['es-CL']);
  assert.equal(r.lang, 'es');
  assert.equal(r.source, 'browser');
  assert.equal(r.remember, false);
});

test('pickLang: saved choice, then browser, then en', () => {
  assert.equal(P.pickLang('', 'de', ['es']).lang, 'de');
  assert.equal(P.pickLang('', 'garbage', ['nl-NL']).lang, 'en');
  assert.equal(P.pickLang('', 'garbage', ['fr-FR']).lang, 'fr');
  assert.equal(P.pickLang('', null, []).source, 'default');
});

test('pickLang: zh-TW and zh-HK resolve to the Chinese block, flagged as Traditional', () => {
  for (const tag of ['zh-TW', 'zh-HK', 'zh-Hant']) {
    const r = P.pickLang('?lang=' + tag, null, ['en']);
    assert.equal(r.lang, 'zh', tag);
    assert.equal(r.traditional, true, tag);
  }
  assert.equal(P.pickLang('?lang=zh-CN', null, ['en']).traditional, false);
  assert.equal(P.pickLang('', null, ['zh-TW']).traditional, true);
});

// ---------------------------------------------------------------- withLang (BUG-12)
test('withLang changes only lang and keeps the other parameters (BUG-12, REQ-W1-104)', () => {
  assert.equal(P.withLang('?foo=1&lang=es', 'de'), '?foo=1&lang=de');
  assert.equal(P.withLang('?lang=es&foo=1&bar=x', 'de'), '?lang=de&foo=1&bar=x');
  assert.equal(P.withLang('?foo=1', 'zh'), '?foo=1&lang=zh');
});

test('withLang with no query gives ?lang=xx and no empty parameter', () => {
  assert.equal(P.withLang('', 'de'), '?lang=de');
  assert.equal(P.withLang('?', 'de'), '?lang=de');
});

// ---------------------------------------------------------------- hashToBlock
test('hashToBlock maps a hash onto the shown block', () => {
  assert.equal(P.hashToBlock('#en-pipeline', 'es'), 'es-pipeline');
  assert.equal(P.hashToBlock('#pipeline', 'de'), 'de-pipeline');
  assert.equal(P.hashToBlock('#%E0%A4%A', 'de'), null);
  assert.equal(P.hashToBlock('', 'de'), null);
});

// ---------------------------------------------------------------- init(window)
test('init with a malformed hash still binds the switch; DE changes language with no reload (BUG-10, REQ-W1-102)', () => {
  const s = makeWindow({ search: '?lang=es', hash: '#%E0%A4%A' });
  let api;
  assert.doesNotThrow(() => { api = P.init(s.w); });
  assert.equal(api.current(), 'es');
  for (const a of s.links) assert.equal((a.listeners.click || []).length, 1);
  const ev = click(s.links[3]);
  assert.equal(ev.defaultPrevented, true, 'the click is handled in page, not by a reload');
  assert.equal(api.current(), 'de');
  assert.equal(s.root.getAttribute('data-lang'), 'de');
});

test('init: a shared ?lang= link does not overwrite the saved choice; a click does', () => {
  const s = makeWindow({ search: '?lang=es', saved: 'de' });
  const api = P.init(s.w);
  assert.equal(api.current(), 'es');
  assert.equal(s.store['karvey-lang'], 'de');
  click(s.links[2]);
  assert.equal(s.store['karvey-lang'], 'pt');
});

test('init: ?lang=xx saves nothing (BUG-11)', () => {
  const s = makeWindow({ search: '?lang=xx', languages: ['es-CL'] });
  const api = P.init(s.w);
  assert.equal(api.current(), 'es');
  assert.equal('karvey-lang' in s.store, false);
});

test('init: switching keeps the other query parameters (BUG-12)', () => {
  const s = makeWindow({ search: '?foo=1&lang=es' });
  P.init(s.w);
  click(s.links[3]);
  assert.equal(s.history.at(-1), '/karvey.html?foo=1&lang=de');
});

test('init binds hashchange and jumps to the shown block (BUG-13, REQ-W1-105)', () => {
  const s = makeWindow({ search: '?lang=es', ids: ['es-foo', 'en-foo'] });
  P.init(s.w);
  assert.equal((s.listeners.hashchange || []).length, 1, 'a hashchange listener is bound');
  s.w.location.hash = '#en-foo';
  s.listeners.hashchange[0]();
  assert.equal(s.byId['es-foo'].scrolled, 1);
  assert.equal(s.history.at(-1), '/karvey.html?lang=es#es-foo');
});

test('hashchange to a hash with no equivalent stays put without error', () => {
  const s = makeWindow({ search: '?lang=es', ids: ['en-only'] });
  P.init(s.w);
  s.w.location.hash = '#en-only';
  assert.doesNotThrow(() => s.listeners.hashchange[0]());
  assert.equal(s.history.length, 0);
  s.w.location.hash = '#%E0%A4%A';
  assert.doesNotThrow(() => s.listeners.hashchange[0]());
});

test('init shows the switch (hidden without JS, BUG-14) and marks html.js', () => {
  const s = makeWindow();
  P.init(s.w);
  assert.equal(s.nav.hidden, false);
  assert.equal(s.classes.has('js'), true);
});

test('init: Traditional-Chinese visitors are told the page is Simplified', () => {
  const s = makeWindow({ search: '?lang=zh-TW' });
  P.init(s.w);
  assert.equal(s.note.hidden, false);
  assert.equal(s.note.textContent, P.UI.zh.simplified);
  click(s.links[4]);
  assert.equal(s.note.hidden, true, 'an explicit choice of zh hides the note');
});

test('init survives a localStorage that throws', () => {
  const s = makeWindow({ search: '?lang=de', storageThrows: true });
  assert.doesNotThrow(() => P.init(s.w));
});

test('every UI string exists in the nine languages', () => {
  assert.deepEqual([...P.LANGS], ['en', 'es', 'pt', 'de', 'zh', 'it', 'ja', 'fr', 'ko']);
  const keys = Object.keys(P.UI.en).sort();
  for (const l of P.LANGS) assert.deepEqual(Object.keys(P.UI[l]).sort(), keys, l);
});

test('the early head script follows the same language rule', () => {
  const head = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1])[0];
  const cases = [
    [{ search: '?lang=es-CL', saved: 'de', nav: ['en'] }, 'es'],
    [{ search: '?lang=xx', saved: null, nav: ['pt-BR'] }, 'pt'],
    [{ search: '', saved: 'zh', nav: ['en'] }, 'zh'],
    [{ search: '?lang=%E0%A4%A', saved: null, nav: ['nl'] }, 'en'],
    [{ search: '', saved: null, nav: ['ko-KR'] }, 'ko'],
    [{ search: '?lang=ja', saved: 'de', nav: ['en'] }, 'ja'],
  ];
  for (const [c, want] of cases) {
    const attrs = {};
    const doc = { documentElement: { className: '', setAttribute: (k, v) => { attrs[k] = v; } } };
    const sandbox = {
      document: doc, location: { search: c.search },
      localStorage: { getItem: () => c.saved }, navigator: { languages: c.nav, language: c.nav[0] },
    };
    vm.runInNewContext(head, sandbox);
    assert.equal(attrs['data-lang'], want, JSON.stringify(c));
    assert.match(doc.documentElement.className, /\bjs\b/);
    assert.equal(P.pickLang(c.search, c.saved, c.nav).lang, want, 'pickLang agrees: ' + JSON.stringify(c));
  }
});

// ---------------------------------------------------------------- nine languages (REQ-W3-066, 068)
test('REQ-W3-066: a Korean browser gets the Korean block and the tab title follows', () => {
  const s = makeWindow({ languages: ['ko-KR', 'en'] });
  const api = P.init(s.w);
  assert.equal(api.current(), 'ko');
  assert.equal(s.w.document.title, P.UI.ko.title);
  assert.equal(s.root.lang, 'ko');
});

test('REQ-W3-066: ?lang=xx renders English and saves nothing', () => {
  const s = makeWindow({ search: '?lang=xx', languages: ['nl-NL'] });
  const api = P.init(s.w);
  assert.equal(api.current(), 'en');
  assert.equal('karvey-lang' in s.store, false);
});

test('REQ-W3-068: ?lang=ja sets the document language to ja; zh keeps zh-Hans', () => {
  const s = makeWindow({ search: '?lang=ja' });
  const api = P.init(s.w);
  assert.equal(s.root.lang, 'ja');
  api.apply('zh');
  assert.equal(s.root.lang, 'zh-Hans');
});

test('REQ-W3-066: the four new links switch in page like the others', () => {
  const s = makeWindow();
  const api = P.init(s.w);
  for (const [i, l] of [[5, 'it'], [6, 'ja'], [7, 'fr'], [8, 'ko']]) {
    click(s.links[i]);
    assert.equal(api.current(), l);
    assert.equal(s.store['karvey-lang'], l);
  }
});

test('REQ-W3-068: the page fetches nothing and CJK uses system fonts only', () => {
  assert.doesNotMatch(html, /<link[^>]+href=|<script[^>]+src=|@import|@font-face|url\(\s*['"]?(https?:)?\/\//);
  assert.match(html, /--font-cjk:/);
  assert.match(html, /\.lang-block:lang\(ja\),\.lang-block:lang\(ko\)\{font-family:var\(--sans\),var\(--font-cjk\)/);
  assert.match(html, /@media \(max-width:720px\)\{\.langs ul\{display:none\}\.lang-select\{display:block\}\}/);
});

// ---------------------------------------------------------------- anchor aliases (REQ-W3-069)
test('REQ-W3-069: hashToBlock resolves an anchor renamed after 3.10.0', () => {
  assert.equal(P.hashToBlock('#reglas', 'en'), 'en-rules');
  assert.equal(P.hashToBlock('#capa-equipo', 'ko'), 'ko-agent-team');
  assert.equal(P.hashToBlock('#t-como', 'ja'), 'ja-t-principles');
  assert.equal(P.hashToBlock('#pipeline', 'fr'), 'fr-pipeline');
  assert.equal(P.hashToBlock('#constructor', 'en'), 'en-constructor', 'only own keys are aliases');
});

for (const lang of ['en', 'ko']) {
  test('REQ-W3-069: an old anchor scrolls to its renamed section (' + lang + ')', () => {
    const s = makeWindow({ search: '?lang=' + lang, hash: '#versiones', ids: [lang + '-versions'] });
    P.init(s.w);
    assert.equal(s.byId[lang + '-versions'].scrolled, 1);
    assert.equal(s.history.at(-1), '/karvey.html?lang=' + lang + '#' + lang + '-versions');
  });
}

test('REQ-W3-069: every alias target is a section of the English block', () => {
  for (const target of Object.values(P.ANCHOR_ALIASES)) assert.match(html, new RegExp('id="en-' + target + '"'), target);
});

test('BUG-88: the phone language select meets the 44 px touch target', () => {
  const m = html.match(/\.lang-select\{[^}]*min-height:(\d+)px/);
  assert.ok(m, '.lang-select declares a min-height');
  assert.ok(Number(m[1]) >= 44, `.lang-select min-height ${m[1]}px is below 44 px`);
});
