from collections import Counter

import spacy
from spacy import Language
from spacy.tokens import DocBin

from ent_tools.util.constants import DOC_ID, SENS, SEN_ID, MENS, ENT_TYPE


def get_stats_from_dict(
        data: dict,
) -> Counter:

    c_basic = Counter()
    c_cate  = Counter()

    c_basic['n_document'] = len(data)

    for docid, doc in data.items():
        sens = doc[SENS]
        c_basic['n_sentence'] += len(sens)

        mens = doc[MENS]
        c_basic['n_mention'] += len(mens)

        for men_id, men in mens.items():
            etype = men[ENT_TYPE]
            c_cate[etype] += 1

    return c_basic, c_cate
