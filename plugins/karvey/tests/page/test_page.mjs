// Method page docs/karvey.html: the inline script's pure functions and init(window) against a stub
// window (E1.F11.T2; BUG-10..13, REQ-W1-102..105). node:test only, no npm (Q-A7 / D-09):
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
  const blocks = ['en', 'es', 'pt', 'de', 'zh'].map((l) => new El({ 'data-lang': l, lang: l === 'zh' ? 'zh-Hans' : l }));
  const links = ['en', 'es', 'pt', 'de', 'zh'].map((l) => new El({ 'data-set-lang': l }));
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
test('langOf reads xx and xx-YY by the first two letters, only for the five languages', () => {
  assert.equal(P.langOf('de'), 'de');
  assert.equal(P.langOf('ES-cl'), 'es');
  assert.equal(P.langOf('zh-TW'), 'zh');
  assert.equal(P.langOf('pt_BR'), 'pt');
  assert.equal(P.langOf('xx'), null);
  assert.equal(P.langOf('fr'), null);
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
  assert.equal(P.pickLang('', 'garbage', ['fr-FR']).lang, 'en');
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

test('every UI string exists in the five languages', () => {
  const keys = Object.keys(P.UI.en).sort();
  for (const l of P.LANGS) assert.deepEqual(Object.keys(P.UI[l]).sort(), keys, l);
});

test('the early head script follows the same language rule', () => {
  const head = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1])[0];
  const cases = [
    [{ search: '?lang=es-CL', saved: 'de', nav: ['en'] }, 'es'],
    [{ search: '?lang=xx', saved: null, nav: ['pt-BR'] }, 'pt'],
    [{ search: '', saved: 'zh', nav: ['en'] }, 'zh'],
    [{ search: '?lang=%E0%A4%A', saved: null, nav: ['fr'] }, 'en'],
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
