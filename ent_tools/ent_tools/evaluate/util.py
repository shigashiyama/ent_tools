from collections import Counter
from typing import Tuple


GOLD    = 'G'
PRED    = 'P'
CORRECT = 'C'


def is_overlap(
        begin1: int,
        end1: int,
        begin2: int,
        end2: int
) -> bool:

    return not (end1 <= begin2 or end2 <= begin1)
    

def merge_sets(
        X: list[set], # list of set of elemens
        y: set, # set of elements
):
    if y in X:
        return X

    X = [x for x in X]
    intersecting_sets = [x for x in X if x & y]
    merged_set = set().union(*intersecting_sets, y)

    X_new = [x for x in X if x not in intersecting_sets]
    X_new.append(merged_set)

    return X_new


def calc_PRF(
        n_gold: int,
        n_pred: int,
        n_corr: int,
) -> Tuple[float, float, float]:

    pre = n_corr / n_pred if n_pred > 0 else 0 
    rec = n_corr / n_gold if n_gold > 0 else 0 
    f1 = 2 * pre * rec / (pre + rec) if pre + rec > 0 else 0
    return pre, rec, f1


def get_PRF_scores(
        counter: dict,
        label_display_order: list = [],
) -> str:
    
    scores = {'Overall': None, 'each_label': {}}

    # Adjust label display order
    labels = list(set([label for label, _ in counter.keys()]))
    if label_display_order:
        labels_diff = set(labels) - set(label_display_order)
        label_display_order.extend(list(labels_diff))
        labels = label_display_order

    # Prepare to calculate overall scores
    label_overall = '<OVERALL>'
    while label_overall in counter.keys():
        label_overall += '_'
    t_counter = Counter()
    for (label, vtype), value in counter.items():
        t_counter[(label_overall, vtype)] += value

    # Calculate scores
    def _get_scores(label, counter):
        g = counter[(label, GOLD)]
        p = counter[(label, PRED)]
        c = counter[(label, CORRECT)]
        pre, rec, f1 = calc_PRF(g, p, c)
        scores_label = {
            'n_gold': g,
            'n_prediction': p,
            'n_correct': c,
            'precision': pre,
            'recall': rec,
            'f1': f1,
        }
        return scores_label        

    scores['Overall'] = _get_scores(label_overall, t_counter)
    for label in labels:
        scores['each_label'][label] = _get_scores(label, counter)

    return scores


def get_PRF_scores_str(scores):
    res  = '--------------------------------------------------\n'
    res += 'label\tn_gold\tn_pred\tn_corr\tP\tR\tF\n'
    res += '--------------------------------------------------\n'

    s = scores['Overall']
    res += f'Overall\t{s["n_gold"]}\t{s["n_prediction"]}\t{s["n_correct"]}\t{s["precision"]:.3f}\t{s["recall"]:.3f}\t{s["f1"]:.3f}\n'

    for label, s in scores['each_label'].items():
        res += f'{label}\t{s["n_gold"]}\t{s["n_prediction"]}\t{s["n_correct"]}\t{s["precision"]:.3f}\t{s["recall"]:.3f}\t{s["f1"]:.3f}\n'

    res = res.strip('\n')

    return res


def get_coref_scores_str(scores: dict) -> str:
    res = ''

    if 'stats' in scores:
        met2vals = scores['stats']
        res += '--------------------------------------------------\n'
        res += '\t'.join([key for key in met2vals.keys()]) + '\n'
        res += '--------------------------------------------------\n'
        res += '\t'.join([str(value) for value in met2vals.values()]) + '\n'
        
    res += '--------------------------------------------------\n'
    res += 'metric\tn_gold\tn_pred\tn_corr\tP\tR\tF\n'
    res += '--------------------------------------------------\n'

    for name, met2vals in scores.items():
        if 'f1' in met2vals:
            n_gold = met2vals['n_gold'] if 'n_gold' in met2vals else '-'
            n_pred = met2vals['n_pred'] if 'n_pred' in met2vals else '-'
            n_corr = met2vals['n_corr'] if 'n_corr' in met2vals else '-'
            res += f'{name}\t{n_gold}\t{n_pred}\t{n_corr}'

            if 'precision' in met2vals:
                p = met2vals['precision']
                res += f'\t{p:.3f}'
            else:
                res += '\t-'

            if 'recall' in met2vals:
                r = met2vals['recall'] 
                res += f'\t{r:.3f}'
            else:
                res += '\t-'

            f = met2vals['f1']
            res += f'\t{f:.3f}\n'

    res = res.strip('\n')

    return res


def get_simple_scores_str(scores: dict) -> str:
    res = '----------' * len(scores) + '\n'
    res += '\t'.join([str(key) for key in scores.keys()]) + '\n'
    res += '----------' * len(scores) + '\n'
    res += '\t'.join([f'{value:.3f}' if type(value) == float else str(value)
                      for value in scores.values()])
    return res
