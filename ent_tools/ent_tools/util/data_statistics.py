from collections import Counter

from ent_tools.util.constants import SENS, MENS, ENTS, ENT_TYPE


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

        ents = doc[ENTS]
        c_basic['n_entity'] += len(ents)

    return c_basic, c_cate
