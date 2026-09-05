"""Read-only R1 boundary comparison. Emits JSON; never writes corpus or results.

The chunk builders read frozen source/structure/config only. Manual enrichment is
loaded after both outputs exist and is used solely for post-hoc diagnostics.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / 'ai-core/experiments/chunking-r1/config-v0.1.json'
ENRICHMENT = ROOT / 'data/processed/voer-dsa-enrichment-v0.1/enrichment.json'
TOKENIZER_DEFAULT = ROOT / 'tmp/tokenizers/bge-m3-5617a9f61b028005a4858fdac845db406aefb181/tokenizer.json'
SERIALIZER_PATH = ROOT / 'ai-core/experiments/source-serialization/serialize_source.py'
ATOM_TAGS = {'p', 'li', 'tr', 'figure', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
RICH_TAGS = {'sub', 'sup', 'tr', 'figure', 'img'}


def digest(value):
    return hashlib.sha256(value.encode('utf-8') if isinstance(value, str) else value).hexdigest()


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def require(ok, code):
    if not ok:
        raise ValueError(code)


def load_serializer():
    spec = importlib.util.spec_from_file_location('r1_source_serializer', SERIALIZER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_catalog(config):
    all_docs = {}
    processed = ROOT / 'data/processed/voer-dsa-structure-v0.1/documents'
    manifest = json.loads((processed.parent / 'manifest.json').read_text(encoding='utf-8'))
    manifest_by_id = {item['document_id']: item for item in manifest['documents']}
    for path in processed.glob('*.json'):
        rep = json.loads(path.read_text(encoding='utf-8'))
        all_docs[rep['source']['document_id']] = (path, rep)
    records = []
    for document_id in config['scope']['document_ids']:
        path, rep = all_docs[document_id]
        src_path = ROOT / rep['source']['path']
        raw = src_path.read_bytes()
        require(digest(raw) == rep['source']['file_sha256'], 'source_hash_mismatch')
        require(digest(path.read_bytes()) == manifest_by_id[document_id]['artifact_file_sha256'], 'representation_hash_mismatch')
        source = json.loads(raw)['data']['text']
        require(digest(source) == rep['source']['html_sha256'], 'html_hash_mismatch')
        records.append({'document_id': document_id, 'source_path': rep['source']['path'],
                        'source_file_sha256': rep['source']['file_sha256'], 'source_version': rep['source']['source_version'],
                        'representation_path': path.relative_to(ROOT).as_posix(),
                        'representation_file_sha256': digest(path.read_bytes()), 'source': source, 'rep': rep})
    return records


def projection_document(record, serializer):
    source, rep = record['source'], record['rep']
    roots = [n for n in rep['nodes'] if n['parent'] is None]
    parts, node_ranges, projected_text_runs, projection_cursor = [], {}, [], 0
    for root_index, root in enumerate(roots):
        if root_index:
            parts.append('\n')
            projection_cursor += 1
        ref = {'document_id': record['document_id'], 'node_id': root['id'], 'tag': root['tag'],
               'raw_html_span': root['source_span'], 'raw_fragment_sha256': digest(source[slice(*root['source_span'])])}
        unit = serializer.serialize_unit(source, rep, ref)
        require(unit['status'] == 'serialized', 'root_not_serialized:' + root['id'])
        out = unit['review_projection']['text']
        event_spans = {}
        for piece in unit['review_projection']['alignment']:
            event_spans.setdefault(piece['event_index'], []).append(piece['output_span'])
        opened, closed = {}, {}
        for index, event in enumerate(unit['events']):
            spans = event_spans.get(index, [])
            if event['source_kind'] == 'start_tag':
                opened[event['node_id']] = min(s[0] for s in spans)
                node = next(n for n in unit['nodes'] if n['id'] == event['node_id'])
                if node['closure'] in {'void', 'self_closed'}:
                    closed[event['node_id']] = max(s[1] for s in spans)
            elif event['source_kind'] == 'end_tag':
                closed[event['node_id']] = max(s[1] for s in spans)
            elif event['source_kind'] in {'text', 'entity'} and spans:
                projected_text_runs.append({'raw_span': event['raw_span'],
                                            'projection_span': [projection_cursor + min(s[0] for s in spans),
                                                                projection_cursor + max(s[1] for s in spans)]})
        for node in unit['nodes']:
            require(node['id'] in opened and node['id'] in closed, 'node_projection_missing:' + node['id'])
            node_ranges[node['id']] = [projection_cursor + opened[node['id']], projection_cursor + closed[node['id']]]
        parts.append(out)
        projection_cursor += len(out)
    text = ''.join(parts)
    by_id = {n['id']: n for n in rep['nodes']}
    section_ids = {s['id'] for s in rep['sections']}
    atoms = []
    candidates = [n for n in rep['nodes'] if n['tag'] in ATOM_TAGS]
    candidate_ids = {n['id'] for n in candidates}
    for node in candidates:
        current, nested = node['parent'], False
        lineage = []
        while current:
            lineage.append(current)
            nested |= current in candidate_ids
            current = by_id[current]['parent']
        if nested:
            continue
        atoms.append({'node_id': node['id'], 'tag': node['tag'], 'projection_span': node_ranges[node['id']],
                      'raw_span': node['source_span'], 'section_id': next((x for x in lineage if x in section_ids), None)})
    atoms.sort(key=lambda x: x['projection_span'])
    require(all(atoms[i - 1]['projection_span'][1] <= atom['projection_span'][0] for i, atom in enumerate(atoms) if i),
            'overlapping_atoms')
    nonspace_runs = [r for r in rep['text_runs'] if r['text'].strip()]
    atom_raw = [a['raw_span'] for a in atoms]
    uncovered = [r for r in nonspace_runs if not any(a <= r['raw_span'][0] and r['raw_span'][1] <= b for a, b in atom_raw)]
    projection_by_raw = {tuple(r['raw_span']): r['projection_span'] for r in projected_text_runs}
    for run in uncovered:
        atoms.append({'node_id': f"orphan-text-{run['raw_span'][0]}-{run['raw_span'][1]}", 'tag': 'orphan_text',
                      'projection_span': projection_by_raw[tuple(run['raw_span'])], 'raw_span': run['raw_span'],
                      'section_id': next((s for s in rep['sections'] if s['id'] in {
                          n['id'] for n in rep['nodes'] if n['source_span'][0] <= run['raw_span'][0] and
                          run['raw_span'][1] <= n['source_span'][1]}), {'id': None})['id']})
    atoms.sort(key=lambda x: x['projection_span'])
    require(all(atoms[i - 1]['projection_span'][1] <= atom['projection_span'][0] for i, atom in enumerate(atoms) if i),
            'overlapping_atoms_after_orphan_fallback')
    return {'document_id': record['document_id'], 'text': text, 'input_sha256': digest(text),
            'node_ranges': node_ranges, 'node_tags': {n['id']: n['tag'] for n in rep['nodes']},
            'atoms': atoms, 'source_codepoints': len(source),
            'input_codepoints': len(text), 'root_count': len(roots)}


def token_count(tokenizer, text):
    return len(tokenizer.encode(text, add_special_tokens=True).ids)


def fixed_chunks(doc, tokenizer, cap):
    text, start, chunks = doc['text'], 0, []
    overhead = token_count(tokenizer, '')
    body_cap = cap - overhead
    while start < len(text):
        encoding = tokenizer.encode(text[start:], add_special_tokens=False)
        if len(encoding.ids) <= body_cap:
            end = len(text)
        else:
            end = start + encoding.offsets[body_cap - 1][1]
            require(end > start, 'tokenizer_no_progress')
            while end > start and token_count(tokenizer, text[start:end]) > cap:
                body_cap_index = max(i for i, (_, b) in enumerate(encoding.offsets) if start + b < end)
                end = start + encoding.offsets[body_cap_index][1]
        count = token_count(tokenizer, text[start:end])
        require(start < end and count <= cap, 'fixed_cap_violation')
        chunks.append({'projection_span': [start, end], 'tokens': count, 'eligible': True,
                       'disposition': 'within_cap', 'boundary_reason': 'hard_token_cap' if end < len(text) else 'document_end'})
        start = end
    return chunks


def structure_units(doc):
    text_len, atoms = len(doc['text']), doc['atoms']
    require(atoms, 'no_structure_atoms')
    starts = [0] + [a['projection_span'][0] for a in atoms[1:]]
    return [{'projection_span': [start, starts[i + 1] if i + 1 < len(starts) else text_len],
             'atom': atoms[i], 'section_id': atoms[i]['section_id']} for i, start in enumerate(starts)]


def structure_chunks(doc, tokenizer, cap):
    chunks, current = [], None
    for unit in structure_units(doc):
        a, b = unit['projection_span']
        if current is not None and unit['section_id'] != current['section_id']:
            current['boundary_reason'] = 'source_section_change'
            chunks.append(current)
            current = None
        candidate_start = a if current is None else current['projection_span'][0]
        count = token_count(tokenizer, doc['text'][candidate_start:b])
        if current is not None and count > cap:
            current['boundary_reason'] = 'next_atomic_unit_exceeds_cap'
            chunks.append(current)
            current = None
            count = token_count(tokenizer, doc['text'][a:b])
        if current is None:
            current = {'projection_span': [a, b], 'tokens': count, 'section_id': unit['section_id'],
                       'atom_node_ids': [unit['atom']['node_id']], 'eligible': count <= cap,
                       'disposition': 'within_cap' if count <= cap else 'oversize_atomic_needs_review'}
        else:
            current['projection_span'][1] = b
            current['tokens'] = count
            current['atom_node_ids'].append(unit['atom']['node_id'])
    current['boundary_reason'] = 'document_end'
    chunks.append(current)
    return chunks


def decorate_chunks(doc, chunks, variant):
    for chunk_index, chunk in enumerate(chunks):
        start, end = chunk['projection_span']
        chunk['chunk_id'] = f"{variant}:{doc['document_id']}:{chunk_index:03d}"
        chunk['input_sha256'] = digest(doc['text'][start:end])
        chunk['preview_before_boundary'] = doc['text'][max(start, end - 100):end].replace('\n', '\\n')
        chunk['preview_after_boundary'] = doc['text'][end:min(len(doc['text']), end + 100)].replace('\n', '\\n')
        chunk['semantic_atoms_cut'] = [a['node_id'] for a in doc['atoms'] if a['projection_span'][0] < end < a['projection_span'][1]] if end < len(doc['text']) else []
        chunk['rich_nodes_cut'] = [nid for nid, span in doc['node_ranges'].items()
                                   if span[0] < end < span[1] and doc['node_tags'].get(nid) in RICH_TAGS] if end < len(doc['text']) else []
        chunk['section_ids_touched'] = sorted({a['section_id'] for a in doc['atoms']
                                               if max(start, a['projection_span'][0]) < min(end, a['projection_span'][1]) and a['section_id']})
    return chunks


def chunks_containing(span, chunks):
    a, b = span
    return [c['chunk_id'] for c in chunks if c['eligible'] and c['projection_span'][0] <= a and b <= c['projection_span'][1]]


def evaluate(variant, documents, chunks_by_doc, enrichment):
    chunk_list = [c for chunks in chunks_by_doc.values() for c in chunks]
    atoms = [a for d in documents.values() for a in d['atoms']]
    atom_split = []
    for atom in atoms:
        containing = chunks_containing(atom['projection_span'], chunks_by_doc[atom['document_id']])
        if not containing:
            atom_split.append(atom)
    groups, group_index = [], {}
    refs = enrichment['refs']
    for group in enrichment['groups']:
        doc = documents[group['document_id']]
        chunks = chunks_by_doc[group['document_id']]
        member_rows = []
        for key in group['member_refs']:
            span = doc['node_ranges'][refs[key]['node_id']]
            member_rows.append({'source_ref': key, 'projection_span': span, 'containing_chunk_ids': chunks_containing(span, chunks)})
        common = set(member_rows[0]['containing_chunk_ids'])
        for row in member_rows[1:]:
            common &= set(row['containing_chunk_ids'])
        touched = [c['chunk_id'] for c in chunks if any(max(c['projection_span'][0], r['projection_span'][0]) <
                   min(c['projection_span'][1], r['projection_span'][1]) for r in member_rows)]
        row = {'group_id': group['id'], 'review_status': group['review']['status'], 'member_count': len(member_rows),
               'fully_contained_in_one_eligible_chunk': bool(common), 'common_chunk_ids': sorted(common),
               'chunks_touched': touched, 'members': member_rows}
        groups.append(row)
        group_index[group['id']] = row
    dependencies = []
    for edge in enrichment['dependencies']:
        left, right = group_index[edge['from_group']], group_index[edge['to_group']]
        shared = set(left['common_chunk_ids']) & set(right['common_chunk_ids'])
        dependencies.append({'dependency_id': edge['id'], 'status': edge['status'], 'from_group': edge['from_group'],
                             'to_group': edge['to_group'], 'co_located_in_one_eligible_chunk': bool(shared),
                             'shared_chunk_ids': sorted(shared), 'automatically_followed': False})
    return {'variant': variant, 'summary': {'chunks': len(chunk_list), 'eligible_chunks': sum(c['eligible'] for c in chunk_list),
              'oversize_chunks': sum(not c['eligible'] for c in chunk_list), 'min_tokens': min(c['tokens'] for c in chunk_list),
              'median_tokens': statistics.median(c['tokens'] for c in chunk_list), 'mean_tokens': round(statistics.mean(c['tokens'] for c in chunk_list), 2),
              'max_tokens': max(c['tokens'] for c in chunk_list), 'semantic_atoms': len(atoms),
              'semantic_atoms_not_wholly_in_one_eligible_chunk': len(atom_split),
              'boundaries_cutting_semantic_atoms': sum(bool(c['semantic_atoms_cut']) for c in chunk_list),
              'boundaries_cutting_rich_nodes': sum(bool(c['rich_nodes_cut']) for c in chunk_list),
              'chunks_crossing_source_sections': sum(len(c['section_ids_touched']) > 1 for c in chunk_list),
              'manual_groups_wholly_in_one_eligible_chunk': sum(g['fully_contained_in_one_eligible_chunk'] for g in groups),
              'manual_groups_total': len(groups), 'dependencies_co_located': sum(d['co_located_in_one_eligible_chunk'] for d in dependencies),
              'dependencies_total': len(dependencies)}, 'groups': groups, 'dependencies': dependencies,
            'atoms_not_wholly_contained': atom_split}


def build_boundaries(tokenizer_path):
    from tokenizers import Tokenizer, __version__ as tokenizers_version
    config_bytes = CONFIG.read_bytes()
    config = json.loads(config_bytes)
    require(tokenizers_version == config['tokenizer']['library_version'], 'tokenizers_version_mismatch')
    require(digest(tokenizer_path.read_bytes()) == config['tokenizer']['file_sha256'], 'tokenizer_hash_mismatch')
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    require(token_count(tokenizer, '') == config['budget']['special_token_overhead'], 'special_token_overhead_mismatch')
    serializer = load_serializer()
    records = source_catalog(config)
    documents = {}
    for record in records:
        doc = projection_document(record, serializer)
        for atom in doc['atoms']:
            atom['document_id'] = doc['document_id']
        documents[doc['document_id']] = doc
    outputs = {}
    cap = config['budget']['hard_cap_tokens_including_special_tokens']
    for variant in config['variants']:
        chunks_by_doc = {}
        for doc in documents.values():
            chunks = fixed_chunks(doc, tokenizer, cap) if variant['id'].startswith('fixed') else structure_chunks(doc, tokenizer, cap)
            chunks_by_doc[doc['document_id']] = decorate_chunks(doc, chunks, variant['id'])
        outputs[variant['id']] = {'chunks_by_document': chunks_by_doc}
    return config_bytes, config, documents, outputs


def build(tokenizer_path):
    config_bytes, config, documents, outputs = build_boundaries(tokenizer_path)
    enrichment = json.loads(ENRICHMENT.read_text(encoding='utf-8'))
    for variant_id, output in outputs.items():
        output['evaluation'] = evaluate(variant_id, documents, output['chunks_by_document'], enrichment)
    public_docs = {key: {k: v for k, v in doc.items() if k != 'text'} for key, doc in documents.items()}
    return {'run_id': config['experiment_id'] + '-run-001', 'status': 'completed_boundary_only',
            'config': config, 'config_sha256': digest(config_bytes),
            'implementation_sha256': digest(Path(__file__).read_bytes()),
            'serializer_implementation_sha256': digest(SERIALIZER_PATH.read_bytes()),
            'tokenizer_file_sha256': digest(tokenizer_path.read_bytes()),
            'input_documents': public_docs, 'variants': outputs,
            'limitations': ['manual enrichment is used only after chunk construction for post-hoc diagnostics',
                            'source serialization/group annotations are assistant-silver dev data',
                            'no retrieval, index, model generation, academic correctness or hallucination test was run']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tokenizer', type=Path, default=TOKENIZER_DEFAULT)
    parser.add_argument('--summary', action='store_true')
    parser.add_argument('--offset', type=int)
    parser.add_argument('--limit', type=int, default=50000)
    args = parser.parse_args()
    result = build(args.tokenizer.resolve())
    if args.summary:
        result = {k: v['evaluation']['summary'] for k, v in result['variants'].items()}
    serialized = compact(result)
    if args.offset is not None:
        result = {'offset': args.offset, 'total': len(serialized), 'sha256': digest(serialized),
                  'text': serialized[args.offset:args.offset + args.limit]}
        serialized = compact(result)
    print(serialized)


if __name__ == '__main__':
    main()
