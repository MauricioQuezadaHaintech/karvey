// Sponsor page template plugins/karvey/templates/sponsor.html (wave3-optimization E1.F4.T5; REQ-W3-024).
// Static checks with node:test only (no browser, no npm — D-09): no external request, a print style that keeps
// every section and hides only navigation, and CSS that cannot overflow a 360 px viewport. The rendered check on
// a real browser is the manual script tests/manual/sponsor-at-gate.md.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const TEMPLATE = path.resolve(HERE, '../../templates/sponsor.html');
const html = readFileSync(TEMPLATE, 'utf8');
const css = [...html.matchAll(/<style>([\s\S]*?)<\/style>/g)].map((m) => m[1]).join('\n');

function block(source, at) {
  // the body of the @media block that starts at `at`
  let i = source.indexOf('{', at) + 1;
  let depth = 1;
  const start = i;
  while (depth && i < source.length) {
    if (source[i] === '{') depth += 1;
    else if (source[i] === '}') depth -= 1;
    i += 1;
  }
  return source.slice(start, i - 1);
}

test('REQ-W3-024: no external request (src, link href, @import, url())', () => {
  assert.doesNotMatch(html, /\bsrc\s*=\s*["']?\s*(https?:)?\/\//i);
  assert.doesNotMatch(html, /<link\b[^>]*\bhref\s*=\s*["']?\s*(https?:)?\/\//i);
  assert.doesNotMatch(css, /@import/i);
  assert.doesNotMatch(css, /url\(\s*["']?\s*(https?:)?\/\//i);
  assert.doesNotMatch(html, /<script\b/i, 'the page needs no script');
  assert.match(html, /http-equiv="Content-Security-Policy" content="default-src 'none'/);
});

test('REQ-W3-024: light and dark schemes from prefers-color-scheme', () => {
  assert.match(css, /@media \(prefers-color-scheme: dark\)/);
  assert.match(css, /color-scheme:light dark/);
});

test('REQ-W3-024: the print style hides only navigation and opens every details', () => {
  const at = css.indexOf('@media print');
  assert.ok(at >= 0, 'a print style exists');
  const print = block(css, at);
  const hidden = [...print.matchAll(/([^{}]+)\{[^{}]*display:\s*none/g)].map((m) => m[1].trim());
  assert.deepEqual(hidden, ['nav.toc']);
  assert.match(print, /details>\*\{display:block!important\}/);
  for (const slot of ['section_waiting', 'section_scope', 'section_progress', 'section_cost', 'section_risks',
    'section_released', 'section_history']) {
    assert.ok(html.includes(`{{{${slot}}}}`), `slot ${slot} present`);
  }
});

test('REQ-W3-024: nothing is wider than a 360 px viewport', () => {
  assert.match(html, /<meta name="viewport" content="width=device-width,initial-scale=1">/);
  for (const m of css.matchAll(/(?<![-\w])(min-width|width)\s*:\s*(\d+)px/g)) {
    assert.ok(Number(m[2]) <= 360, `${m[1]}:${m[2]}px can overflow 360 px`);
  }
  // grids collapse to one column: every minmax is capped by 100%
  for (const m of css.matchAll(/minmax\(([^,]+),/g)) {
    assert.match(m[1], /min\(100%/, `minmax(${m[1]}, …) is not capped by 100%`);
  }
  assert.match(css, /\.table-scroll\{overflow-x:auto;max-width:100%\}/);
  assert.match(css, /body\{[^}]*overflow-wrap:anywhere/);
  assert.match(css, /\.sp\{max-width:880px/);
});
