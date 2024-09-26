import argparse
from collections import Counter
from typing import Tuple

import logzero
from logzero import logger
from sklearn.metrics import cohen_kappa_score

from ent_tools.util.constants import (
    MENS, ENTS, SEN_ID, ENT_ID, MEM_MEN_IDS, ENT_TYPE, ENT_TYPE_MRG, TXT, SPAN, 
    HAS_REF, REF_URL, REF_TYPE, NIL
)
from ent_tools.util.data_io import load_json, write_as_json
from ent_tools.evaluate.util import GOLD, PRED, CORRECT
from ent_tools.evaluate.util import get_PRF_scores, get_PRF_scores_str, get_simple_scores_str


ALL   = 'ALL'
InKB  = 'InKB'
OOKB  = 'OutOfKB'
NONEX = 'NONEX'                 # nonexist mention


class CountForED:
    def __init__(self):
        self.counter = Counter()


    def update(self, gold_ref: str, pred_ref: str) -> None:
        if gold_ref != NIL:
            self.counter[(InKB, GOLD)] += 1
        else:
            self.counter[(OOKB, GOLD)] += 1

        if pred_ref != NIL:
            self.counter[(InKB, PRED)] += 1
        else:
            self.counter[(OOKB, PRED)] += 1

        if gold_ref == pred_ref:
            if gold_ref != NIL:
                self.counter[(InKB, CORRECT)] += 1
            else:
                self.counter[(OOKB, CORRECT)] += 1


def get_men_span_and_ref(
        mention: dict,
        entities: dict,
        target_url_prefix: str = None,
        discard_ref_type: bool = False,
) -> Tuple[Tuple[str, int, int], str]:

    sen_id = mention[SEN_ID]
    span   = mention[SPAN]
    if mention[HAS_REF]:
        ent_id   = mention[ENT_ID]
        ref_url  = entities[ent_id][REF_URL]
        ref_type = entities[ent_id][REF_TYPE]

        if ref_type:
            if discard_ref_type:
                ref = NIL
            else:
                ref = f'{ref_type}#{ref_url}'
        else:
            ref = ref_url

        if target_url_prefix and not ref_url.startswith(target_url_prefix):
            ref = NIL

    else:
        ref = NIL

    return ((sen_id, *span), ref)
    

def evaluate(
        gold_data: dict,
        pred_data: dict,
        target_url_prefix: str = None,
        ignore_labels: set[str] = None,
        discard_ref_type: bool = False,
        urlmap: dict = {},
) -> Tuple[list, list]:

    # TODO debug mode
    
    count = CountForED()        # for F1
    gold_ref_seq = []           # for kappa
    pred_ref_seq = []           # for kappa
    ent_types_appeared = set()

    for docid, gold_doc in gold_data.items():
        if not docid in pred_data:
            continue
        pred_doc = pred_data[docid]

        # set gold_men_span_to_ref
        gold_men_span_to_ref = {}
        gold_men_span_to_mid_tmp = {}
        for men_id, men in gold_doc[MENS].items():
            ent_type = men[ENT_TYPE]
            if (ignore_labels is not None
                and len(ignore_labels) > 0
                and ent_type in ignore_labels
            ):
                continue
            ent_types_appeared.add(ent_type)

            span, ref = get_men_span_and_ref(
                men, gold_doc[ENTS],
                target_url_prefix=target_url_prefix,
                discard_ref_type=discard_ref_type
            )
            gold_men_span_to_ref[span] = ref
            gold_men_span_to_mid_tmp[span] = men_id

        # set pred_men_span_to_ref
        pred_men_span_to_ref = {}
        pred_men_span_to_mid_tmp = {}
        for men_id, men in pred_doc[MENS].items():
            span, ref = get_men_span_and_ref(
                men, pred_doc[ENTS],
                target_url_prefix=target_url_prefix,
                discard_ref_type=discard_ref_type,
            )
            pred_men_span_to_ref[span] = ref
            pred_men_span_to_mid_tmp[span] = men_id

        # compare results
        for span in set(gold_men_span_to_ref.keys()) | set(pred_men_span_to_ref.keys()):
            if span in gold_men_span_to_ref:
                gold_ref = gold_men_span_to_ref[span]
            else:
                gold_ref = NONEX

            if span in pred_men_span_to_ref:
                pred_ref = pred_men_span_to_ref[span]
            else:
                pred_ref = NONEX

            if gold_ref != NONEX and pred_ref != NONEX:
                # gold_men_id = gold_men_span_to_mid_tmp[span]
                # gold_men_tmp = gold_doc[MENS][gold_men_id]
                # pred_men_id = gold_men_span_to_mid_tmp[span]
                # pred_men_tmp = gold_doc[MENS][gold_men_id]
                # print(f'GOLD\t{docid}\t{gold_men_id}\t{gold_men_tmp}')
                # print(f'PRED\t{docid}\t{pred_men_id}\t{pred_men_tmp}')

                # for F1
                count.update(gold_ref, pred_ref)

                # for kappa
                gold_ref_seq.append(gold_ref)
                pred_ref_seq.append(pred_ref)

    # calc F1
    scores = get_PRF_scores(count.counter, label_display_order=[InKB, OOKB])

    # calc kappa
    if ignore_labels is None or len(ignore_labels) == 0:
        k_score = cohen_kappa_score(gold_ref_seq, pred_ref_seq)
        n_match = sum([1 if g == p else 0 for g, p in zip(gold_ref_seq, pred_ref_seq)])
        n_g_ex  = sum([1 if g != NONEX else 0 for g in zip(gold_ref_seq)])
        n_p_ex  = sum([1 if p != NONEX else 0 for p in zip(pred_ref_seq)])
        scores['kappa'] = {
            'n_merged_ins': len(gold_ref_seq),
            'n_gold_ins': n_g_ex,
            'n_pred_ins': n_p_ex,
            'n_match': n_match,
            'kappa': float(k_score),
        }

    logger.info(f'Appeared entity types: {sorted(ent_types_appeared)}')

    return scores


if __name__ == '__main__':
    logzero.loglevel(20)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--gold_path', '-g',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--pred_path', '-p',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--target_docids', '-t',
        type=str,
    )
    parser.add_argument(
        '--target_url_prefix',
        type=str,
    )
    parser.add_argument(
        '--urlmap_path', '-u',
        type=str,
    )
    parser.add_argument(
        '--discard_instance_with_ref_type',
        action='store_true',
    )
    parser.add_argument(
        '--ignore_labels',
        type=str,
    )
    parser.add_argument(
        '--output_score_path', '-o',
        type=str,
        default=None,
    )
    args = parser.parse_args()

    urlmap = load_urlmap(args.urlmap_path) if args.urlmap_path else {}

    target_docids = set()
    if args.target_docids:
        target_docids = set(args.target_docids.split(','))

    ignore_labels = set()
    if args.ignore_labels:
        ignore_labels = set(args.ignore_labels.split(','))

    # TODO use target_docids
    gold_data = load_json(args.gold_path)
    pred_data = load_json(args.pred_path)

    scores = evaluate(
        gold_data, pred_data, 
        target_url_prefix=args.target_url_prefix,
        ignore_labels=ignore_labels,
        discard_ref_type=args.discard_instance_with_ref_type,
        urlmap=urlmap,
    )
    f_res = get_PRF_scores_str(scores)
    print(f'discard_ref_type={args.discard_instance_with_ref_type}; Ignore: {args.ignore_labels}')
    print(f_res)
    if 'kappa' in scores:
        k_res = get_simple_scores_str(scores['kappa'])
        print(k_res)

    if args.output_score_path:
        write_as_json(scores, args.output_score_path)
