"""Independent integrity checks for the stored R1 boundary-only run."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN_PATH = ROOT / 'data/processed/voer-dsa-chunking-r1-v0.1/run.json'
TOKENIZER_PATH = ROOT / 'tmp/tokenizers/bge-m3-5617a9f61b028005a4858fdac845db406aefb181/tokenizer.json'

spec = importlib.util.spec_from_file_location('r1_runner', HERE / 'run_boundary_comparison.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def digest(value):
    return hashlib.sha256(value.encode('utf-8') if isinstance(value, str) else value).hexdigest()


def audit(stored, config, documents, tokenizer):
    checks, errors = 0, []

    def check(ok, code, label):
        nonlocal checks
        checks += 1
        if not ok:
            errors.append({'code': code, 'label': label})

    check(stored['status'] == 'completed_boundary_only', 'execution_status', 'run status')
    check(stored['config'] == config and stored['config_sha256'] == digest(runner.CONFIG.read_bytes()), 'config_pin', 'config')
    check(stored['tokenizer_file_sha256'] == digest(TOKENIZER_PATH.read_bytes()) == config['tokenizer']['file_sha256'],
          'tokenizer_pin', 'tokenizer')
    check(config['budget'] == {'hard_cap_tokens_including_special_tokens': 512, 'target': 'greedy_up_to_hard_cap',
          'special_token_overhead': 2, 'body_budget_tokens': 510, 'overlap_tokens': 0, 'header_tokens': 0},
          'budget_changed', 'same budget')
    check(stored['implementation_sha256'] == digest(Path(runner.__file__).read_bytes()), 'implementation_pin', 'runner')
    check(set(stored['input_documents']) == set(documents) == set(config['scope']['document_ids']), 'scope_changed', 'documents')
    for document_id, doc in documents.items():
        public = {k: v for k, v in doc.items() if k != 'text'}
        check(stored['input_documents'].get(document_id) == public, 'input_changed', document_id)
        check(doc['input_sha256'] == digest(doc['text']), 'input_hash', document_id)
        check(all(0 <= a['projection_span'][0] < a['projection_span'][1] <= len(doc['text']) for a in doc['atoms']),
              'atom_span', document_id)
        check(all(doc['atoms'][i - 1]['projection_span'][1] <= atom['projection_span'][0]
                  for i, atom in enumerate(doc['atoms']) if i), 'atom_overlap', document_id)
    for variant_id, output in stored['variants'].items():
        all_chunks = []
        for document_id, chunks in output['chunks_by_document'].items():
            doc = documents[document_id]
            cursor = 0
            for index, chunk in enumerate(chunks):
                a, b = chunk['projection_span']
                check(a == cursor and a < b <= len(doc['text']), 'chunk_partition', chunk['chunk_id'])
                cursor = b
                check(chunk['chunk_id'] == f'{variant_id}:{document_id}:{index:03d}', 'chunk_identity', chunk['chunk_id'])
                check(chunk['input_sha256'] == digest(doc['text'][a:b]), 'chunk_hash', chunk['chunk_id'])
                count = len(tokenizer.encode(doc['text'][a:b], add_special_tokens=True).ids)
                check(chunk['tokens'] == count, 'token_count', chunk['chunk_id'])
                check(chunk['eligible'] == (count <= 512), 'eligibility', chunk['chunk_id'])
                if chunk['eligible']:
                    check(count <= 512, 'cap_violation', chunk['chunk_id'])
                expected_atoms = [atom['node_id'] for atom in doc['atoms'] if atom['projection_span'][0] < b < atom['projection_span'][1]] if b < len(doc['text']) else []
                expected_rich = [nid for nid, span in doc['node_ranges'].items()
                                 if span[0] < b < span[1] and doc['node_tags'][nid] in runner.RICH_TAGS] if b < len(doc['text']) else []
                check(chunk['semantic_atoms_cut'] == expected_atoms, 'atom_cut_trace', chunk['chunk_id'])
                check(chunk['rich_nodes_cut'] == expected_rich, 'rich_cut_trace', chunk['chunk_id'])
                touched = sorted({atom['section_id'] for atom in doc['atoms'] if atom['section_id'] and
                                  max(a, atom['projection_span'][0]) < min(b, atom['projection_span'][1])})
                check(chunk['section_ids_touched'] == touched, 'section_trace', chunk['chunk_id'])
                all_chunks.append(chunk)
            check(cursor == len(doc['text']), 'chunk_partition', variant_id + ':' + document_id + ':end')
        summary = output['evaluation']['summary']
        check(summary['chunks'] == len(all_chunks) and summary['eligible_chunks'] == sum(c['eligible'] for c in all_chunks),
              'summary_changed', variant_id)
        check(summary['boundaries_cutting_semantic_atoms'] == sum(bool(c['semantic_atoms_cut']) for c in all_chunks),
              'summary_changed', variant_id + ':atoms')
        check(summary['boundaries_cutting_rich_nodes'] == sum(bool(c['rich_nodes_cut']) for c in all_chunks),
              'summary_changed', variant_id + ':rich')
        check(summary['chunks_crossing_source_sections'] == sum(len(c['section_ids_touched']) > 1 for c in all_chunks),
              'summary_changed', variant_id + ':sections')
        if variant_id.startswith('structure'):
            check(not any(c['semantic_atoms_cut'] for c in all_chunks), 'structure_atom_break', variant_id)
        groups = {g['group_id']: g for g in output['evaluation']['groups']}
        check(set(groups) == {g['id'] for g in json.loads(runner.ENRICHMENT.read_text(encoding='utf-8'))['groups']},
              'group_inventory', variant_id)
        for group in groups.values():
            common = None
            for member in group['members']:
                actual = runner.chunks_containing(member['projection_span'], output['chunks_by_document'][
                    next(r['document_id'] for r in json.loads(runner.ENRICHMENT.read_text(encoding='utf-8'))['refs'].values()
                         if r['node_id'] == member['source_ref'].split(':', 1)[1])])
                check(member['containing_chunk_ids'] == actual, 'group_mapping', variant_id + ':' + member['source_ref'])
                common = set(actual) if common is None else common & set(actual)
            check(group['fully_contained_in_one_eligible_chunk'] == bool(common), 'group_containment', variant_id + ':' + group['group_id'])
    return {'checks': checks, 'errors': errors}


def main():
    from tokenizers import Tokenizer
    tokenizer = Tokenizer.from_file(str(TOKENIZER_PATH))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    config_bytes, config, documents, boundaries = runner.build_boundaries(TOKENIZER_PATH)
    stored = json.loads(RUN_PATH.read_text(encoding='utf-8'))
    baseline = audit(stored, config, documents, tokenizer)
    mutations = []

    def mutation(name, expected, change):
        value = deepcopy(stored)
        change(value)
        codes = sorted({x['code'] for x in audit(value, config, documents, tokenizer)['errors']})
        mutations.append({'id': name, 'expected_error': expected, 'detected': expected in codes, 'observed_errors': codes})

    first_variant = next(iter(stored['variants']))
    first_doc = next(iter(stored['variants'][first_variant]['chunks_by_document']))
    first_chunk = stored['variants'][first_variant]['chunks_by_document'][first_doc][0]
    mutation('wrong_tokenizer_hash', 'tokenizer_pin', lambda x: x.update(tokenizer_file_sha256='0' * 64))
    mutation('change_budget', 'config_pin', lambda x: x['config']['budget'].update(hard_cap_tokens_including_special_tokens=1024))
    mutation('input_document_removed', 'scope_changed', lambda x: x['input_documents'].pop(first_doc))
    mutation('chunk_gap', 'chunk_partition', lambda x: x['variants'][first_variant]['chunks_by_document'][first_doc][0].update(projection_span=[1, first_chunk['projection_span'][1]]))
    mutation('wrong_chunk_hash', 'chunk_hash', lambda x: x['variants'][first_variant]['chunks_by_document'][first_doc][0].update(input_sha256='0' * 64))
    mutation('token_count_relabelled', 'token_count', lambda x: x['variants'][first_variant]['chunks_by_document'][first_doc][0].update(tokens=1))
    mutation('atom_cut_hidden', 'atom_cut_trace', lambda x: next(c for cs in x['variants']['fixed-512-o0']['chunks_by_document'].values() for c in cs if c['semantic_atoms_cut']).update(semantic_atoms_cut=[]))
    mutation('section_crossing_hidden', 'section_trace', lambda x: next(c for cs in x['variants']['fixed-512-o0']['chunks_by_document'].values() for c in cs if len(c['section_ids_touched']) > 1).update(section_ids_touched=[]))
    mutation('group_claim_flipped', 'group_containment', lambda x: x['variants'][first_variant]['evaluation']['groups'][0].update(fully_contained_in_one_eligible_chunk=not x['variants'][first_variant]['evaluation']['groups'][0]['fully_contained_in_one_eligible_chunk']))
    original_read = Path.read_text
    def guarded_read(path, *args, **kwargs):
        if path.resolve() == runner.ENRICHMENT.resolve():
            raise AssertionError('Evaluator label file was read during boundary construction')
        return original_read(path, *args, **kwargs)
    try:
        with patch.object(Path, 'read_text', guarded_read):
            _, _, no_label_docs, no_label_boundaries = runner.build_boundaries(TOKENIZER_PATH)
        no_label_build = set(no_label_docs) == set(documents) and {
            k: {d: [(c['projection_span'], c['tokens']) for c in cs] for d, cs in v['chunks_by_document'].items()}
            for k, v in no_label_boundaries.items()} == {
            k: {d: [(c['projection_span'], c['tokens']) for c in cs] for d, cs in v['chunks_by_document'].items()}
            for k, v in boundaries.items()}
    except AssertionError:
        no_label_build = False
    rebuilt = runner.build(TOKENIZER_PATH)
    deterministic = stored == rebuilt == runner.build(TOKENIZER_PATH)
    fixed = stored['variants']['fixed-512-o0']['evaluation']['summary']
    structure = stored['variants']['structure-512-o0']['evaluation']['summary']
    expected_observations = (fixed['boundaries_cutting_semantic_atoms'] == 52 and
                             structure['boundaries_cutting_semantic_atoms'] == 0 and
                             fixed['chunks_crossing_source_sections'] == 19 and
                             structure['chunks_crossing_source_sections'] == 0)
    passed = not baseline['errors'] and all(m['detected'] for m in mutations) and no_label_build and deterministic and expected_observations
    result = {'audit_id': 'voer-dsa-chunking-boundary-r1-audit-v0.1',
              'status': 'boundary_integrity_passed' if passed else 'failed',
              'scope': 'Boundary construction/token counts/post-hoc group mapping only; no retrieval, answer, or academic quality.',
              'run_sha256': digest(RUN_PATH.read_bytes()), 'config_sha256': digest(runner.CONFIG.read_bytes()),
              'tokenizer_sha256': digest(TOKENIZER_PATH.read_bytes()), 'runner_sha256': digest(Path(runner.__file__).read_bytes()),
              'auditor_sha256': digest(Path(__file__).read_bytes()), 'baseline': baseline,
              'additional_checks': {'boundary_build_does_not_read_enrichment': no_label_build,
                                    'two_rebuilds_match_saved_run': deterministic,
                                    'pinned_observations_match': expected_observations},
              'mutations': mutations, 'variant_summaries': {k: v['evaluation']['summary'] for k, v in stored['variants'].items()}}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
