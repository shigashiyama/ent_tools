from collections import Counter

from ent_tools.util.constants import (
    SENS, MENS, ENTS, SEN_ID, ENT_ID, MEM_MEN_IDS, TXT, SPAN, ENT_TYPE, DIR_MEN_PAIRS,
)

from logzero import logger


def convert_json_for_atd(
        doc: dict,
) -> dict:

    doc_new = {SENS: doc[SENS], MENS: {}, ENTS: {}}

    entids_to_ignore = set()
    entid_orig_to_new = {}

    # add mentions
    for men_id, men in doc[MENS].items():
        men_new = {}
        men_new.update(men)

        remove_ent = False

        if (men[ENT_TYPE].startswith('TRANS_')
            or men[ENT_TYPE].endswith('_ORG')
        ):
            remove_ent = True

        if 'CorefLabel' in men:
            del men_new['CorefLabel']

            if men['CorefLabel'] == 'GENERIC':
                men_new['generic'] = True
                remove_ent = True

            elif men['CorefLabel'] == 'SPEC_AMB':
                men_new['ref_spec_amb'] = True
                remove_ent = True

            elif men['CorefLabel'] == 'HIE_AMB':
                men_new['ref_hie_amb'] = True                

        if remove_ent:
            ent_id = men[ENT_ID]
            entids_to_ignore.add(ent_id)
            men_new[ENT_ID] = None

            ent = doc[ENTS][ent_id]
            # assert len(ent[MEM_MEN_IDS]) == 1, f'{ent[MEM_MEN_IDS]}'

        doc_new[MENS][men_id] = men_new

    # add entities
    for ent_id_orig, ent in doc[ENTS].items():
        if ent_id_orig in entids_to_ignore:
            continue 

        # re-assign ent_id
        ent_id_new = f'E{len(entid_orig_to_new)+1:03d}'
        entid_orig_to_new[ent_id_orig] = ent_id_new

        ent_new = {}
        ent_new.update(ent)

        # set has_name and entity_type_merged
        counter_etype = Counter()
        counter_ename = Counter()
        for men_id in ent[MEM_MEN_IDS]:
            men = doc_new[MENS][men_id]
            men[ENT_ID] = ent_id_new
            etype = men[ENT_TYPE]
            counter_ename[has_ent_name(etype)] += 1     
            counter_etype[get_ent_type(etype)] += 1
        cls_name  = True in counter_ename
        cls_etype = aggregate_ent_type(counter_etype.keys())
        ent_new['has_name'] = cls_name
        ent_new['entity_type_merged'] = cls_etype

        # set coref_attr
        if DIR_MEN_PAIRS in ent_new:
            ent_new['coref_attr_pairs'] = ent_new[DIR_MEN_PAIRS]
            del ent_new[DIR_MEN_PAIRS]

        doc_new[ENTS][ent_id_new] = ent_new

    return doc_new


def has_ent_name(elabel: str) -> bool:
    return elabel.endswith('NAME')


def get_ent_type(elabel: str) -> bool:
    if elabel.startswith('LOC_') and not elabel.startswith('LOC_OR_FAC'):
        return 'LOC'

    if elabel.startswith('FAC_'):
        return 'FAC'

    if elabel.startswith('LINE_'):
        return 'LINE'

    if elabel.startswith('TRANS_'):
        return 'TRANS'

    if elabel.endswith('_ORG'):
        return 'NON_GEO'

    return 'UNK' # LOC_OR_FAC, DEICTIC, OTHER


def aggregate_ent_type(etypes: set[str]) -> str:
    if len(etypes) == 1:
        return list(etypes)[0]

    etypes_tmp = [etype for etype in etypes if etype != 'UNK']
    if len(etypes_tmp) == 1:
        return list(etypes_tmp)[0]

    else:
        return 'MIX'
