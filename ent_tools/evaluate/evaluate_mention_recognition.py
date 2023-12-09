import argparse
from collections import Counter
from typing import Tuple

from logzero import logger

from ent_tools.util.constants import DOC_ID, SENS, SEN_ID, TXT, MEN_IDS, MENS, SPAN, ENT_TYPE
from ent_tools.util.data_io import load_json, write_as_json
from ent_tools.evaluate.util import GOLD, PRED, CORRECT
from ent_tools.evaluate.util import get_PRF_scores, get_PRF_scores_str


class CountForMR:
    def __init__(self, 
                 labelmap: dict = None,
    ):
        self.counter = Counter()
        self.labelmap = labelmap


    def update_for_dataset(
            self,
            gold_data: dict,
            pred_data: dict,
    ) -> None:

        for doc_id, gold_doc in gold_data.items():
            logger.info(f'Count spans for {doc_id}.')

            sen_ids = gold_doc[SENS].keys()
            sen_id2gold_spans = {sen_id: [] for sen_id in sen_ids}
            sen_id2pred_spans = {sen_id: [] for sen_id in sen_ids}

            for men_id, men in gold_doc[MENS].items():
                sen_id2gold_spans[men[SEN_ID]].append(
                    (men[SPAN][0], men[SPAN][1], men[ENT_TYPE]))

            if doc_id in pred_data:
                pred_doc = pred_data[doc_id]
                for men_id, men in pred_doc[MENS].items():
                    sen_id2pred_spans[men[SEN_ID]].append(
                        (men[SPAN][0], men[SPAN][1], men[ENT_TYPE]))

            else:
                logger.warning(f'Prediction for {doc_id} is not available.')

            for sen_id in sen_ids:
                self.update(sen_id2gold_spans[sen_id], sen_id2pred_spans[sen_id])


    def update(self, gold_spans, pred_spans):
        if self.labelmap:
            pred_spans = [(pb, pe, self.labelmap[plabel])
                          for pb, pe, plabel in pred_spans if plabel in self.labelmap]

        for gspan in gold_spans:
            gb, ge, glabel = gspan
            self.counter[(glabel, GOLD)] += 1

            if gspan in pred_spans:
                self.counter[(glabel, CORRECT)] += 1

        for pspan in pred_spans:
            pb, pe, plabel = pspan
            self.counter[(plabel, PRED)] += 1


def split_multi_label_spans(
        spans: list[Tuple],
) -> list[Tuple]:

    new_spans = []
    for span in spans:
        begin, end, labels = span
        for label in labels.split(','):
            new_spans.append((begin, end, label))
    return new_spans


# def get_summary(counter):
#     ALL = '<ALL>'

#     t_counter = Counter()
#     for (label, vtype), value in counter.items():
#         t_counter[(ALL, vtype)] += value

#     return t_counter


def main():
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
        '--label_conversion_map_path', '-l',
        type=str,
        default=None,
    )
    parser.add_argument(
        '--output_score_path', '-s',
        type=str,
        default=None,
    )
    parser.add_argument(
        '--label_display_order',
        type=str,
        default=None,
    )
    args = parser.parse_args()

    labelmap = None
    if args.label_conversion_map_path:
        labelmap = load_json(args.label_conversion_map_path)

    count = CountForMR(labelmap=labelmap)

    label_display_order = []
    if args.label_display_order:
        for label in args.label_display_order.split(','):
            label_display_order.append(label)

    gold_data = load_json(args.gold_path)
    pred_data = load_json(args.pred_path)
    count.update_for_dataset(gold_data, pred_data)

    scores = get_PRF_scores(count.counter, label_display_order=label_display_order)
    if args.output_score_path:
        write_as_json(scores, args.output_score_path)

    res = get_PRF_scores_str(scores)
    print(res)


if __name__ == '__main__':
    main()
