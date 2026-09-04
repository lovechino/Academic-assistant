"""Read-only integrity audit of manual context annotations; not a chunker benchmark."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import html
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
ENRICHMENT = ROOT / 'data/processed/voer-dsa-enrichment-v0.1/enrichment.json'
PACK = ROOT / 'data/evaluation/silver/voer-dsa-context-probes-v0.1/probes.json'


def digest(value):
    return hashlib.sha256(value.encode('utf-8') if isinstance(value, str) else value).hexdigest()


def audit(enrichment, pack):
    checks, errors = 0, []

    def check(ok, code, label):
        nonlocal checks
        checks += 1
        if not ok:
            errors.append({'code': code, 'label': label})

    documents = {}
    for catalog in enrichment['source_catalog']:
        source_path = (ROOT / catalog['source_path']).resolve()
        representation_path = (ROOT / catalog['representation_path']).resolve()
        check(source_path.is_relative_to(ROOT / 'data/raw/voer') and representation_path.is_relative_to(ROOT / 'data/processed/voer-dsa-structure-v0.1'),
              'path_scope', catalog['document_id'])
        if not source_path.is_relative_to(ROOT / 'data/raw/voer') or not representation_path.is_relative_to(ROOT / 'data/processed/voer-dsa-structure-v0.1'):
            continue
        raw = source_path.read_bytes()
        rep_bytes = representation_path.read_bytes()
        source = json.loads(raw)['data']
        representation = json.loads(rep_bytes)
        check(digest(raw) == catalog['source_file_sha256'] and digest(rep_bytes) == catalog['representation_file_sha256'],
              'source_hash', catalog['document_id'])
        check(source['version'] == catalog['source_version'] == representation['source']['source_version'],
              'source_version', catalog['document_id'])
        check(representation['source']['document_id'] == catalog['document_id'], 'source_identity', catalog['document_id'])
        documents[catalog['document_id']] = {'text': source['text'], 'rep': representation,
                                           'nodes': {n['id']: n for n in representation['nodes']}}
    check(pack['source_catalog'] == enrichment['source_catalog'], 'catalog_separation_integrity', 'same pinned source')
    check(pack['enrichment_sha256'] == digest(ENRICHMENT.read_bytes()), 'enrichment_hash', 'sidecar pin')
    check(enrichment['restrictions'] == {'usage': 'local_research_reference', 'serving_authorized': False,
                                       'external_processing_authorized': False, 'training_authorized': False},
          'research_boundary', 'source restrictions')
    check(not enrichment['runtime_ready'] and not enrichment['chunking_run'], 'runtime_overclaim', 'research only')
    check(not pack['human_reviewed'] and pack['label_level'] == 'assistant_silver', 'gold_overclaim', 'pack review')
    check(pack['restrictions'] == {'evaluator_only': True, 'allowed_as_model_input': False, 'allowed_as_chunker_rules': False},
          'label_leakage', 'evaluator boundary')
    check('probes' not in enrichment and 'expected' not in enrichment, 'label_leakage', 'source sidecar')

    for name, bundle in [('enrichment', enrichment), ('probes', pack)]:
        for key, ref in bundle['refs'].items():
            doc = documents.get(ref['document_id'])
            node = None if doc is None else doc['nodes'].get(ref['node_id'])
            check(node is not None, 'unknown_source_ref', key)
            if node is None:
                continue
            a, b = ref['raw_html_span']
            check([a, b] == node['source_span'] and 0 <= a < b <= len(doc['text']), 'source_span', name + ':' + key)
            check(ref['tag'] == node['tag'] and digest(doc['text'][a:b]) == ref['raw_fragment_sha256'],
                  'fragment_integrity', name + ':' + key)
            check(key == ref['document_id'].removeprefix('voer-module-') + ':' + ref['node_id'], 'ref_identity', key)

    groups = {g['id']: g for g in enrichment['groups']}
    check(len(groups) == len(enrichment['groups']), 'duplicate_group', 'groups')
    for group in groups.values():
        check(bool(group['member_refs']) and len(set(group['member_refs'])) == len(group['member_refs']), 'group_membership', group['id'])
        for key in group['member_refs']:
            ref = enrichment['refs'].get(key)
            check(ref is not None, 'unknown_member', group['id'])
            if ref:
                check(ref['document_id'] == group['document_id'], 'cross_document_group', group['id'])
        check(group['review']['reviewer'] == 'assistant' and not group['review']['independent_review']
              and group['review']['academic_review'] == 'pending', 'gold_overclaim', group['id'])
        check(group['review']['status'] in {'assistant_source_checked', 'assistant_visual_checked', 'proposed', 'source_uncertain'},
              'review_status', group['id'])
    dependencies = {d['id']: d for d in enrichment['dependencies']}
    check(len(dependencies) == len(enrichment['dependencies']), 'duplicate_dependency', 'dependencies')
    graph = {g: [] for g in groups}
    for dep in dependencies.values():
        valid = dep['from_group'] in groups and dep['to_group'] in groups
        check(valid, 'orphan_dependency', dep['id'])
        check(not dep['automatically_follow'], 'unreviewed_expansion', dep['id'])
        if valid:
            graph[dep['from_group']].append(dep['to_group'])
            check(groups[dep['from_group']]['document_id'] == groups[dep['to_group']]['document_id'],
                  'cross_document_dependency', dep['id'])
    visiting, visited = set(), set()

    def cyclic(key):
        if key in visiting:
            return True
        if key in visited:
            return False
        visiting.add(key)
        if any(cyclic(child) for child in graph[key]):
            return True
        visiting.remove(key)
        visited.add(key)
        return False

    check(not any(cyclic(g) for g in graph), 'dependency_cycle', 'dependency graph')
    for review in enrichment['visual_reviews']:
        ref = enrichment['refs'][review['image_ref']]
        doc = documents[ref['document_id']]
        image = next(i for i in doc['rep']['images'] if i['node_id'] == ref['node_id'])
        path = (ROOT / image['asset']['local_path']).resolve()
        check(path.is_relative_to(ROOT / 'data/raw/voer') and path.is_file(), 'asset_path', review['image_ref'])
        check(review['asset_path'] == image['asset']['local_path'] and digest(path.read_bytes()) == review['asset_sha256'],
              'asset_hash', review['image_ref'])
        check(not review['explicit_caption'] and not review['transcription_gold'] and not image['explicit_caption_node_ids'],
              'caption_overclaim', review['image_ref'])
        check(review['linked_group'] in groups and review['academic_review'] == 'pending', 'visual_review_boundary', review['image_ref'])

    ids = [p['id'] for p in pack['probes']]
    check(ids == [f'CP-{i:02d}' for i in range(1, 31)] and pack['probe_count'] == 30, 'probe_inventory', '30 IDs')
    check(sum(len(p['variants']) for p in pack['probes']) == pack['variant_count'] == 31, 'variant_inventory', '31 variants')
    probe_rows = []
    for probe in pack['probes']:
        error_start = len(errors)
        check(not probe['human_reviewed'] and probe['academic_review'] == 'pending', 'gold_overclaim', probe['id'])
        check(probe['execution_status'] == 'not_run' and all(v['execution_status'] == 'not_run' for v in probe['variants']),
              'execution_overclaim', probe['id'])
        check(bool(probe['observation']) and bool(probe['expected']['action']), 'missing_annotation', probe['id'])
        check(all(r in pack['refs'] for r in probe['source_refs']), 'unknown_probe_ref', probe['id'])
        check(all(g in groups for g in probe['group_refs']), 'unknown_probe_group', probe['id'])
        check(all(r in pack['refs'] for r in probe['expected'].get('must_keep_refs', [])), 'unknown_expected_ref', probe['id'])
        check(all(d in dependencies for d in probe['expected'].get('required_dependency_ids', [])), 'unknown_expected_dependency', probe['id'])
        check(all(g in groups for g in probe['expected'].get('forbidden_merge_groups', [])), 'unknown_forbidden_group', probe['id'])
        if probe['origin'] == 'real_source':
            check(bool(probe['source_refs']) and probe['fixture'] is None, 'real_source_provenance', probe['id'])
        elif probe['origin'] == 'controlled_fixture':
            check(bool(probe['source_refs']) and isinstance(probe['fixture'], dict), 'fixture_provenance', probe['id'])
        else:
            check(probe['origin'] == 'synthetic' and not probe['source_refs'] and isinstance(probe['fixture'], dict),
                  'synthetic_provenance', probe['id'])
        for key in probe['expected'].get('blank_ref_ids', []):
            ref = pack['refs'][key]
            doc = documents[ref['document_id']]
            a, b = ref['raw_html_span']
            import re
            text = html.unescape(re.sub('<[^>]+>', '', doc['text'][a:b]))
            check(not text.strip(), 'blank_content', probe['id'])
        probe_rows.append({'probe_id': probe['id'], 'origin': probe['origin'], 'variants': len(probe['variants']),
                           'annotation_status': probe['annotation_status'], 'reference_annotation_checks_passed': len(errors) == error_start,
                           'system_execution': 'not_run'})

    by_id = {p['id']: p for p in pack['probes']}
    p = by_id['CP-08']
    ref = pack['refs'][p['source_refs'][0]]
    element = next(e for e in documents[ref['document_id']]['rep']['elements'] if e['id'] == ref['node_id'])
    check(p['expected']['expected_existing_quality_flag'] in element['quality_flags'], 'code_flag_regression', 'CP-08')
    found_tags = set()
    for key in by_id['CP-10']['source_refs']:
        ref = pack['refs'][key]
        a, b = ref['raw_html_span']
        found_tags.update(n['tag'] for n in documents[ref['document_id']]['nodes'].values() if a <= n['source_span'][0] < n['source_span'][1] <= b)
    check(set(by_id['CP-10']['expected']['required_tags']) <= found_tags, 'inline_role_regression', 'CP-10')
    stack = documents['voer-module-a208ce0f']['rep']
    table = stack['tables'][0]
    check([c['text'] for c in table['cells'] if c['source_row_index'] == 0] == by_id['CP-14']['expected']['expected_header_texts']
          and not any(c['explicit_header'] for c in table['cells']), 'table_header_regression', 'CP-14')
    fixture = by_id['CP-21']['fixture']
    check(fixture['unit'] == 'fixture_units_not_tokens' and sum(p['cost'] for p in fixture['parts']) == by_id['CP-21']['expected']['expected_total_units'] > fixture['capacity'],
          'budget_fixture', 'CP-21 symbolic units only')
    for pid, should_complete in [('CP-22', True), ('CP-24', False)]:
        p = by_id[pid]
        available = set(p['fixture']['initial_refs'] + p['fixture']['available_extra_refs'])
        check(set(p['expected']['must_keep_refs']).issubset(available) == should_complete, 'availability_fixture', pid)
    p = by_id['CP-23']
    check([set(p['expected']['must_keep_refs']).issubset(v['available_refs']) for v in p['variants']] == [True, False],
          'comparison_fixture', 'CP-23')
    check(by_id['CP-27']['fixture']['claimed_version'] != next(c['source_version'] for c in pack['source_catalog'] if c['document_id'] == 'voer-module-a208ce0f'),
          'version_fixture', 'CP-27')
    fixture = by_id['CP-30']['fixture']
    expected = by_id['CP-30']['expected']
    a, b = expected['emoji_codepoint_span']
    check(fixture['raw_html'][a:b] == '😀' and len('😀'.encode('utf-16-le')) // 2 == expected['emoji_utf16_length']
          and html.unescape('&amp;') == expected['ampersand_decoded'], 'unicode_fixture', 'CP-30')
    return {'checks': checks, 'errors': errors, 'probe_annotation_checks': probe_rows}


def main():
    enrichment = json.loads(ENRICHMENT.read_text(encoding='utf-8'))
    pack = json.loads(PACK.read_text(encoding='utf-8'))
    baseline = audit(enrichment, pack)
    mutations = []

    def mutation(name, expected, change):
        e, p = deepcopy(enrichment), deepcopy(pack)
        change(e, p)
        result = audit(e, p)
        codes = sorted({x['code'] for x in result['errors']})
        mutations.append({'id': name, 'expected_error': expected, 'detected': expected in codes, 'observed_errors': codes})

    mutation('wrong_source_hash', 'source_hash', lambda e, p: e['source_catalog'][0].update(source_file_sha256='0'*64))
    mutation('wrong_raw_span', 'source_span', lambda e, p: next(iter(e['refs'].values())).update(raw_html_span=[0, 1]))
    mutation('missing_group_member', 'unknown_member', lambda e, p: e['groups'][0]['member_refs'].append('unknown'))
    queue_ref = next(k for k, r in enrichment['refs'].items() if r['document_id'] == 'voer-module-387652b5')
    mutation('cross_document_group', 'cross_document_group', lambda e, p: e['groups'][0]['member_refs'].append(queue_ref))
    mutation('orphan_dependency', 'orphan_dependency', lambda e, p: e['dependencies'][0].update(to_group='missing'))
    mutation('dependency_cycle', 'dependency_cycle', lambda e, p: e['dependencies'].append(dict(e['dependencies'][0], id='cycle', from_group='stack-array-declaration', to_group='stack-array-push')))
    mutation('invent_caption', 'caption_overclaim', lambda e, p: e['visual_reviews'][0].update(explicit_caption=True))
    mutation('authorize_serving', 'research_boundary', lambda e, p: e['restrictions'].update(serving_authorized=True))
    mutation('claim_gold', 'gold_overclaim', lambda e, p: p.update(human_reviewed=True))
    mutation('call_fixture_units_tokens', 'budget_fixture', lambda e, p: p['probes'][20]['fixture'].update(unit='tokens'))
    mutation('synthetic_as_real', 'real_source_provenance', lambda e, p: p['probes'][28].update(origin='real_source'))
    mutation('claim_probe_executed', 'execution_overclaim', lambda e, p: p['probes'][0].update(execution_status='passed'))
    passed = not baseline['errors'] and all(m['detected'] for m in mutations)
    result = {'audit_id': 'context-review-audit-v0.1', 'status': 'integrity_passed' if passed else 'failed',
              'scope': 'Manual annotation/source consistency only; no chunker/retriever/generator execution.',
              'auditor_sha256': digest(Path(__file__).read_bytes()), 'enrichment_sha256': digest(ENRICHMENT.read_bytes()),
              'probes_sha256': digest(PACK.read_bytes()), 'counts': {'groups': len(enrichment['groups']),
              'dependencies': len(enrichment['dependencies']), 'images_visually_inspected_by_assistant': len(enrichment['visual_reviews']),
              'probes': len(pack['probes']), 'variants': sum(len(p['variants']) for p in pack['probes']),
              'origins': dict(Counter(p['origin'] for p in pack['probes'])), 'system_executions': 0},
              'baseline': baseline, 'mutations': mutations}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
