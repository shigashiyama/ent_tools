"""
This code is a slightly modified verson of the following codes:
https://github.com/ns-moosavi/coval/blob/master/coval/eval/eval.py
https://github.com/ns-moosavi/coval/blob/master/coval/conll/reader.py#L454
"""
from collections import Counter

import numpy as np
from scipy.optimize import linear_sum_assignment


def get_mention_assignments(inp_clusters, out_clusters):
    mention_cluster_ids = {}
    out_dic = {}
    for i, c in enumerate(out_clusters):
        for m in c:
            out_dic[m] = i

    for ic in inp_clusters:
        for im in ic:
            if im in out_dic:
                mention_cluster_ids[im] = out_dic[im]

    return mention_cluster_ids


class Evaluator:
    def __init__(self, metric, beta=1):
        self.p_num = 0          # numerator for precision
        self.p_den = 0          # denominator for precision
        self.r_num = 0          # numerator for recall
        self.r_den = 0          # denominator for recall
        self.metric = metric
        self.beta = beta


    def update(self, coref_info):
        (key_clusters, sys_clusters, key_mention_sys_cluster,
                sys_mention_key_cluster) = coref_info

        if self.metric == ceafe or self.metric == ceafm:
            pn, pd, rn, rd = self.metric(sys_clusters, key_clusters)
        elif self.metric == lea:
            pn, pd = self.metric(sys_clusters, key_clusters,
                    sys_mention_key_cluster)
            rn, rd = self.metric(key_clusters, sys_clusters,
                    key_mention_sys_cluster)
        else:
            pn, pd = self.metric(sys_clusters, sys_mention_key_cluster)
            rn, rd = self.metric(key_clusters, key_mention_sys_cluster)
        self.p_num += pn
        self.p_den += pd
        self.r_num += rn
        self.r_den += rd


    def get_counts(self):
        return self.p_num, self.p_den, self.r_num, self.r_den


    def get_PRF(self):
        beta = self.beta
        p = 0 if self.p_den == 0 else self.p_num / float(self.p_den)
        r = 0 if self.r_den == 0 else self.r_num / float(self.r_den)
        f = (0 if p + r == 0
             else (1 + beta * beta) * p * r / (beta * beta * p + r))
        return p, r, f


def mentions(clusters, mention_to_gold):
    setofmentions = set(mention for cluster in clusters for mention in cluster)
    correct = setofmentions & set(mention_to_gold.keys())
    return len(correct), len(setofmentions)


def b_cubed(clusters, mention_to_gold):
    num, den = 0, 0

    for c in clusters:
        gold_counts = Counter()
        correct = 0
        for m in c:
            if m in mention_to_gold:
                gold_counts[mention_to_gold[m]] += 1
        for c2 in gold_counts:
            correct += gold_counts[c2] * gold_counts[c2]

        num += correct / float(len(c))
        den += len(c)

    return num, den


def muc(clusters, mention_to_gold):
    tp, p = 0, 0
    for c in clusters:
        p += len(c) - 1
        tp += len(c)
        linked = set()
        for m in c:
            if m in mention_to_gold:
                linked.add(mention_to_gold[m])
            else:
                tp -= 1
        tp -= len(linked)
    return tp, p


def phi4(c1, c2):
    return 2 * len([m for m in c1 if m in c2]) / float(len(c1) + len(c2))


def phi3(c1, c2):
    return len([m for m in c1 if m in c2])


def ceafe(clusters, gold_clusters):
    clusters = [c for c in clusters]
    scores = np.zeros((len(gold_clusters), len(clusters)))
    for i in range(len(gold_clusters)):
        for j in range(len(clusters)):
            scores[i, j] = phi4(gold_clusters[i], clusters[j])
    row_ind, col_ind = linear_sum_assignment(-scores)
    similarity = scores[row_ind, col_ind].sum()
    return similarity, len(clusters), similarity, len(gold_clusters)


def ceafm(clusters, gold_clusters):
    clusters = [c for c in clusters]
    scores = np.zeros((len(gold_clusters), len(clusters)))
    for i in range(len(gold_clusters)):
        for j in range(len(clusters)):
            scores[i, j] = phi3(gold_clusters[i], clusters[j])
    row_ind, col_ind = linear_sum_assignment(-scores)
    similarity = scores[row_ind, col_ind].sum()
    return similarity, len(clusters), similarity, len(gold_clusters)


def lea(input_clusters, output_clusters, mention_to_gold):
    num, den = 0, 0

    for c in input_clusters:
        if len(c) == 1:
            all_links = 1
            if c[0] in mention_to_gold and len(
                    output_clusters[mention_to_gold[c[0]]]) == 1:
                common_links = 1
            else:
                common_links = 0
        else:
            common_links = 0
            all_links = len(c) * (len(c) - 1) / 2.0
            for i, m in enumerate(c):
                if m in mention_to_gold:
                    for m2 in c[i + 1:]:
                        if m2 in mention_to_gold and mention_to_gold[
                                m] == mention_to_gold[m2]:
                            common_links += 1

        num += len(c) * common_links / float(all_links)
        den += len(c)

    return num, den
