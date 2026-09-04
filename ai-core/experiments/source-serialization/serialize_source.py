"""Read-only, source-preserving serialization of frozen manual research groups.

No qrels/probe labels, tokenizer, chunker, model, HTML execution or file writes.
The typed event tape is canonical; the escaped markup view is for text review.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import html
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
ENRICHMENT = ROOT / 'data/processed/voer-dsa-enrichment-v0.1/enrichment.json'
ENRICHMENT_SHA = 'c63b23ad9abd88bd2a8deabd8bbda25d6c412f10c010480107b66bdfefc1b693'
PROFILE = 'source-event-tape-v0.1'
ALLOWED_TAGS = set('p span em strong b i u sub sup table tbody thead tfoot tr td th div ul ol li h1 h2 h3 h4 h5 h6 br code pre figure figcaption img a'.split())
BLOCK_TAGS = set('p table tr div ul ol li h1 h2 h3 h4 h5 h6 pre figure figcaption'.split())
RESTRICTIONS = {'usage': 'local_research_reference', 'serving_authorized': False,
                'external_processing_authorized': False, 'training_authorized': False}


def digest(value):
    return hashlib.sha256(value.encode('utf-8') if isinstance(value, str) else value).hexdigest()


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def require(ok, code):
    if not ok:
        raise ValueError(code)


def local_path(relative, scope):
    path = (ROOT / relative).resolve()
    require(path.is_relative_to((ROOT / scope).resolve()), 'path_outside_scope')
    return path


def load_inputs():
    raw = ENRICHMENT.read_bytes()
    require(digest(raw) == ENRICHMENT_SHA, 'enrichment_hash_mismatch')
    enrichment = json.loads(raw)
    require(enrichment['restrictions'] == RESTRICTIONS, 'restrictions_mismatch')
    documents = {}
    for item in enrichment['source_catalog']:
        src = local_path(item['source_path'], 'data/raw/voer').read_bytes()
        rep_bytes = local_path(item['representation_path'], 'data/processed/voer-dsa-structure-v0.1').read_bytes()
        require(digest(src) == item['source_file_sha256'], 'source_hash_mismatch')
        require(digest(rep_bytes) == item['representation_file_sha256'], 'representation_hash_mismatch')
        data, rep = json.loads(src)['data'], json.loads(rep_bytes)
        require(data['version'] == item['source_version'] == rep['source']['source_version'], 'source_version_mismatch')
        require(rep['source']['document_id'] == item['document_id'] and
                rep['source']['file_sha256'] == digest(src) and rep['source']['html_sha256'] == digest(data['text']), 'source_identity_mismatch')
        require(rep['restrictions'] == RESTRICTIONS, 'representation_restrictions')
        documents[item['document_id']] = (data['text'], rep)
    return enrichment, documents


def asset_state(image):
    """Check only the local pinned asset; never resolve a URL or infer its content."""
    result = deepcopy(image)
    asset = result.get('asset')
    state = 'missing_or_unresolved'
    if asset:
        path = local_path(asset['local_path'], 'data/raw/voer')
        state = 'missing' if not path.is_file() else 'local_hash_verified' if digest(path.read_bytes()) == asset['sha256'] else 'hash_mismatch'
    result.update(availability_checked_this_run=state, semantic_transcription=None,
                  visual_semantics_ready=False, alt_promoted_to_caption=False)
    return result


def serialize_unit(source, rep, ref, asset_checker=asset_state):
    """Serialize exactly one reviewed source node, with no adjacent-source expansion."""
    a, b = ref['raw_html_span']
    require(0 <= a < b <= len(source), 'ref_span_bounds')
    require(digest(source[a:b]) == ref['raw_fragment_sha256'], 'ref_fragment_hash')
    by_id = {n['id']: n for n in rep['nodes']}
    root = by_id.get(ref['node_id'])
    require(root is not None and root['source_span'] == [a, b] and root['tag'] == ref['tag'], 'ref_node_mismatch')
    require(ref['document_id'] == rep['source']['document_id'], 'ref_document_mismatch')
    nodes = [deepcopy(n) for n in rep['nodes'] if a <= n['source_span'][0] < n['source_span'][1] <= b]
    reasons = sorted({('unsupported_tag:' + n['tag']) for n in nodes if n['tag'] not in ALLOWED_TAGS} |
                     {('non_explicit_closure:' + n['id']) for n in nodes if n['closure'] not in {'explicit', 'void', 'self_closed'}})
    result = {'source_ref': deepcopy(ref), 'status': 'blocked' if reasons else 'serialized',
              'blocking_reasons': reasons, 'nodes': nodes, 'events': [], 'tables': [], 'images': [],
              'review_projection': {'format': 'escaped_source_markup_for_text_review_not_safe_html_or_model_prompt',
                                    'text': '', 'alignment': []}}
    if reasons:
        return result  # Explicitly refuse the whole unit, not a silently truncated suffix.
    tokens = [t for t in rep['source_tokens'] if a <= t['span'][0] and t['span'][1] <= b]
    cursor = a
    for token in tokens:
        require(token['span'][0] == cursor and token['span'][1] > cursor, 'non_partitioned_source_tokens')
        cursor = token['span'][1]
    require(cursor == b, 'source_token_coverage')
    opens = {tuple(n['open_span']): n for n in nodes}
    closes = {tuple(n['close_span']): n for n in nodes if n['close_span']}
    runs = {tuple(r['raw_span']): r for r in rep['text_runs']}
    output, alignment, output_size = [], [], 0

    def emit(value, event_index, origin, mapping, span):
        nonlocal output_size
        if not value:
            return
        output.append(value)
        alignment.append({'output_span': [output_size, output_size + len(value)], 'event_index': event_index,
                          'origin': origin, 'mapping': mapping, 'raw_span': span,
                          'citable_as_source_text': origin == 'source_text'})
        output_size += len(value)

    for token in tokens:
        start, end = token['span']
        raw, kind = source[start:end], token['kind']
        event = {'raw_span': [start, end], 'source_kind': kind}
        index = len(result['events'])
        if kind in {'text', 'entity'}:
            run = runs.get((start, end))
            require(run is not None and run['kind'] == kind, 'missing_text_run')
            expected = raw if kind == 'text' else html.unescape(raw)
            require(run['text'] == expected, 'decoded_text_mismatch')
            event.update(parent_node_id=run['parent'], decoded_text=run['text'], disposition='projected_source_text')
            if kind == 'entity':
                emit(html.escape(expected, quote=False), index, 'source_text', 'entity_envelope', [start, end])
            else:
                # Only &, < and > are escaped. No whitespace/Unicode/source correction.
                segment = 0
                for offset, character in enumerate(expected):
                    if character not in '&<>':
                        continue
                    emit(expected[segment:offset], index, 'source_text', 'linear', [start + segment, start + offset])
                    emit(html.escape(character, quote=False), index, 'source_text', 'escaped_character', [start + offset, start + offset + 1])
                    segment = offset + 1
                emit(expected[segment:], index, 'source_text', 'linear', [start + segment, end])
        elif kind in {'start_tag', 'end_tag'}:
            node = (opens if kind == 'start_tag' else closes).get((start, end))
            require(node is not None, 'unmatched_tag_event')
            event.update(node_id=node['id'], disposition='generated_structure_marker')
            if kind == 'start_tag':
                marker = '<img ref="' + node['id'] + '" />' if node['tag'] == 'img' else '<' + node['tag'] + (' />' if node['closure'] in {'void', 'self_closed'} else '>')
                if node['tag'] == 'br':
                    marker += '\n'
            else:
                marker = '</' + node['tag'] + '>' + ('\n' if node['tag'] in BLOCK_TAGS else '')
            emit(marker, index, 'structure_marker', 'generated_not_evidence', [start, end])
        else:
            # Comments/declarations are traceable but not content or instructions.
            event.update(disposition='not_projected_noncontent', raw_sha256=digest(raw))
        result['events'].append(event)
    ids = {n['id'] for n in nodes}
    for table in rep['tables']:
        cells = [deepcopy(c) for c in table['cells'] if c['node_id'] in ids]
        rows = [r for r in table['row_node_ids'] if r in ids]
        if table['node_id'] in ids or rows or cells:
            result['tables'].append({'source_table_node_id': table['node_id'],
                                     'whole_table_selected': table['node_id'] in ids,
                                     'selected_row_node_ids': rows, 'cells': cells,
                                     'grid_expansion': 'not_computed', 'blank_semantics': 'unknown_not_zero_or_carry_forward',
                                     'header_semantics': 'raw_th_only_no_td_promotion'})
    result['images'] = [asset_checker(i) for i in rep['images'] if i['node_id'] in ids]
    result['review_projection'].update(text=''.join(output), alignment=alignment)
    return result


def build():
    enrichment, documents = load_inputs()
    groups = deepcopy(enrichment['groups'])
    selected = list(dict.fromkeys(r for g in groups for r in g['member_refs']))
    units = {key: serialize_unit(*documents[enrichment['refs'][key]['document_id']], enrichment['refs'][key]) for key in selected}
    for group in groups:
        previous_end = -1
        for key in group['member_refs']:
            ref = enrichment['refs'][key]
            require(ref['document_id'] == group['document_id'], 'cross_document_group')
            require(ref['raw_html_span'][0] >= previous_end, 'overlapping_or_unordered_group_members')
            previous_end = ref['raw_html_span'][1]
        group['serialization_status'] = 'serialized' if all(units[k]['status'] == 'serialized' for k in group['member_refs']) else 'blocked_member'
        group['dependency_ids_not_expanded'] = [d['id'] for d in enrichment['dependencies'] if d['from_group'] == group['id']]
        group['overlapping_group_ids_not_duplicate_chunks'] = []
        for other in groups:
            if other['id'] == group['id'] or other['document_id'] != group['document_id']:
                continue
            if any(max(enrichment['refs'][x]['raw_html_span'][0], enrichment['refs'][y]['raw_html_span'][0]) <
                   min(enrichment['refs'][x]['raw_html_span'][1], enrichment['refs'][y]['raw_html_span'][1])
                   for x in group['member_refs'] for y in other['member_refs']):
                group['overlapping_group_ids_not_duplicate_chunks'].append(other['id'])
    return {'serialization_id': PROFILE, 'corpus_snapshot': enrichment['corpus_snapshot'],
            'split': 'dev', 'source_catalog': enrichment['source_catalog'],
            'profile': {'implementation_sha256': digest(Path(__file__).read_bytes()), 'python_version': sys.version.split()[0],
                        'enrichment_path': ENRICHMENT.relative_to(ROOT).as_posix(), 'enrichment_sha256': ENRICHMENT_SHA,
                        'coordinate_system': 'unicode_codepoint_half_open_in_decoded_json_data_text',
                        'output_coordinates': 'unicode_codepoint_half_open_per_unit_review_projection',
                        'source_nodes_attributes': 'inert_untrusted_metadata_not_executed',
                        'source_selection': 'manual_enrichment_members_only_not_envelope',
                        'unit_overlap': 'pooled_by_ref_but_ancestor_descendant_overlap_still_present_not_an_index',
                        'whitespace': 'source_text_unchanged_structural_newlines_generated',
                        'semantic_correctness': 'not_evaluated', 'tokenizer': None, 'chunking': 'not_run',
                        'retrieval': 'not_run', 'generation': 'not_run', 'serving_ready': False},
            'restrictions': deepcopy(RESTRICTIONS), 'units': units, 'groups': groups,
            'dependencies_not_expanded': deepcopy(enrichment['dependencies']),
            'reference_only_not_selected': sorted(set(enrichment['refs']) - set(selected)),
            'summary': summarize(units, groups)}


def summarize(units, groups):
    unique_nodes = {(u['source_ref']['document_id'], n['id']): n for u in units.values() for n in u['nodes']}
    tags = Counter(n['tag'] for n in unique_nodes.values())
    images = {(u['source_ref']['document_id'], i['node_id']): i for u in units.values() for i in u['images']}
    cells = {(u['source_ref']['document_id'], c['node_id']): c for u in units.values() for t in u['tables'] for c in t['cells']}
    runs = {(u['source_ref']['document_id'], *e['raw_span']): e for u in units.values() for e in u['events'] if 'decoded_text' in e}
    return {'groups': len(groups), 'member_references_including_repeats': sum(len(g['member_refs']) for g in groups),
            'unique_selected_roots': len(units), 'unit_statuses': dict(Counter(u['status'] for u in units.values())),
            'group_statuses': dict(Counter(g['serialization_status'] for g in groups)),
            'unique_selected_nodes': len(unique_nodes), 'unique_source_text_runs': len(runs),
            'unique_source_text_codepoints': sum(len(e['decoded_text']) for e in runs.values()),
            'unique_tag_counts': dict(tags), 'unique_table_cells': len(cells),
            'unique_blank_cells': sum(c['is_blank'] for c in cells.values()), 'unique_images': len(images),
            'image_asset_states': dict(Counter(i['availability_checked_this_run'] for i in images.values())),
            'review_statuses': dict(Counter(g['review']['status'] for g in groups))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', action='store_true')
    parser.add_argument('--group')
    parser.add_argument('--offset', type=int)
    parser.add_argument('--limit', type=int, default=50000)
    args = parser.parse_args()
    result = build()
    if args.summary:
        result = result['summary']
    elif args.group:
        group = next((g for g in result['groups'] if g['id'] == args.group), None)
        if group is None:
            parser.error('Unknown group')
        result = {'group': group, 'units': {k: result['units'][k] for k in group['member_refs']}}
    serialized = compact(result)
    if args.offset is not None:
        if args.offset < 0 or args.limit <= 0:
            parser.error('Invalid JSON transport page (not a semantic chunk)')
        result = {'offset': args.offset, 'total': len(serialized), 'sha256': digest(serialized),
                  'text': serialized[args.offset:args.offset + args.limit]}
        serialized = compact(result)
    print(serialized)


if __name__ == '__main__':
    main()
