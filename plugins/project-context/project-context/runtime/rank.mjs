import { readFileSync } from 'node:fs';
import { extractKeywords, rankByRelevance } from '../vendor/dsh-knit/relevance.js';
import { buildContext } from '../vendor/dsh-knit/context.js';
import { buildRelationFacts } from '../vendor/dsh-knit/relations.js';
import { passageMatchesFor, passageTfOf } from '../vendor/dsh-knit/passage.js';

const request = JSON.parse(readFileSync(0, 'utf8'));
const keywords = extractKeywords([request.query]);
const ranked = rankByRelevance(request.docs, keywords, 0);
const candidates = ranked.docs.map(document => ({ ...document, passageTf: passageTfOf(document) }));
const facts = buildRelationFacts(candidates, { root: request.workspace_id });
const pack = buildContext({ ranked: candidates, relations: facts.incident, task: request.query,
  topic: ranked.label.join(' / '), total: candidates.length });
const byPath = new Map(candidates.map(document => [document.rel, document]));
for (const group of ['primary', 'supporting', 'related']) {
  for (const item of pack[group]) {
    item.passages = passageMatchesFor(byPath.get(item.rel), keywords, 0);
  }
}
process.stdout.write(JSON.stringify({ pack, keywords: keywords.map(keyword => keyword.term) }));
