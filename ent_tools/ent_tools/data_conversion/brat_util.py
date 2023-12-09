from typing import Tuple

from logzero import logger

from ent_tools.util.constants import SENS, SEN_ID, TXT, MEN_IDS, MENS, SPAN, ENT_TYPE


def merge_clusters_until_convergence(
        clusters: list
) -> list:

    while True:
        idx_sets_to_be_merged = _get_idx_sets_to_be_merged(clusters)
        if not idx_sets_to_be_merged:
            break
        
        clusters = _merge_clusters(clusters, idx_sets_to_be_merged)

    return clusters


def _get_idx_sets_to_be_merged(
        clusters: list[list],
) -> list[set]:

    to_be_merged = []
    for i, cls1 in enumerate(clusters):
        for j, cls2 in enumerate(clusters):
            if i < j:
                if set(cls1) & set(cls2):
                    flag_add = False
                    for idx_set in to_be_merged:
                        if i in idx_set:
                            idx_set.add(j)
                            flag_add = True
                            break

                        elif j in idx_set:
                            idx_set.add(i)
                            flag_add = True
                            break

                    if not flag_add:
                        to_be_merged.append(set([i, j]))

    return to_be_merged


def _merge_clusters(
        clusters: list[list],
        idx_set_to_be_merged: list[set],
) -> list[list]:

    new_clusters = []
    idx_used = set()
    for idx_set in idx_set_to_be_merged:
        new_set = list(set(sum([clusters[idx] for idx in idx_set], [])))
        idx_used |= idx_set
        new_clusters.append(new_set)

    for idx, cls in enumerate(clusters):
        if not idx in idx_used:
            new_clusters.append(cls)

    return new_clusters


def get_subdoc_spans(
        input_txt: str,
) -> list:

    subdoc_spans = []
    in_subdoc = False
    dt_begin = sd_begin = sd_end = -1

    with open(input_txt) as f:
        logger.info(f'Read: {input_txt}')
        bol_idx = 0
        for line in f:
            eol_idx = bol_idx + len(line)

            if not in_subdoc and line.startswith('<title>'):
                dt_begin = bol_idx

            if line.startswith('<subdoc '): # page_begin=* or fulldoc='True'
                if dt_begin >= 0:
                    sd_begin = dt_begin
                    dt_begin = -1
                else:
                    sd_begin = bol_idx
                in_subdoc = True

            if line.startswith('</subdoc>'):
                sd_end = eol_idx
                in_subdoc = False
                subdoc_spans.append((sd_begin, sd_end))

            bol_idx = eol_idx

    return subdoc_spans


def load_ann(
        input_ann: str,
        subdoc_span: Tuple[int] = None,
        keep_coref_relations: bool = False,
        ignore_span_with_newline: bool = True,
) -> Tuple:

    mid2mention = {}  # mid (e.g. T1) -> men_txt, men_label, begin, end
    mid2cidx = {}
    dict_mid2att = {}
    clusters = []

    mid_exclude = set()

    with open(input_ann) as f:
        if subdoc_span:
            logger.info(f'Read: {input_ann} (for subdoc {subdoc_span})')
        else:
            logger.info(f'Read: {input_ann}')

        for line in f:
            line = line.strip('\n')
            if line.startswith('T'):
                array = line.split('\t')
                men_id = array[0]  # entity MENTION id
                array2 = array[1].split(' ')
                men_label = array2[0]
                men_begin = int(array2[1])
                if ignore_span_with_newline:
                    if ';' in array[1]:
                        logger.warning(f'Skip a mention including newline char: {line}' )
                        continue

                men_end = int(array2[-1])
                men_txt = array[2]

                if (subdoc_span
                    and (men_begin < subdoc_span[0] or subdoc_span[1] < men_end)
                ):
                    mid_exclude.add(men_id)
                else:
                    mid2mention[men_id] = (men_txt, men_label, men_begin, men_end)

            elif line.startswith('A'):
                array = line.split('\t')
                att_info = array[1].split(' ')
                att_name = att_info[0]
                men_id = att_info[1]
                att_label = att_info[2] if len(att_info) > 2 else True

                if not att_name in dict_mid2att:
                    dict_mid2att[att_name] = {}
                mid2att = dict_mid2att[att_name]
                mid2att[men_id] = att_label

            elif line.startswith('*'):
                array = line.split('\t')
                coref_info = array[1].split(' ')
                coref_name = coref_info[0]
                if coref_name != COREF:
                    continue

                mids = [e for e in coref_info[1:]]
                clusters.append(mids)
                cidx = len(clusters) - 1
                for men_id in mids:
                    mid2cidx[men_id] = cidx

            elif line.startswith('#'):
                array = line.split('\t')
                assert len(array) == 3
                men_id = array[1].split(' ')[1]

    # remove mid in mid_exclude
    for mid_ex in mid_exclude:
        for mid2att in dict_mid2att:
            if mid_ex in mid2att:
                del mid2att[mid_ex]

        for mids in clusters:
            if mid_ex in mids:
                mids.remove(mid_ex)
                if len(mids) == 0:
                    clusters.remove(mids)

    if keep_coref_relations:
        return clusters, mid2mention, None, dict_mid2att

    # merge clusters if there are clusters with common elements
    clusters_new = merge_clusters_until_convergence(clusters)

    # assign cidx to each singleton mention and add it to clusters_new
    mids_already_added = set(sum([cls for cls in clusters_new], []))
    for mid in mid2mention.keys():
        if mid in mids_already_added:
            continue
        cidx = len(clusters_new)
        mid2cidx[mid] = cidx
        clusters_new.append([mid])
    
    mid2cidx_new = {}
    for cidx, cls in enumerate(clusters_new):
        # print('N', cidx, cls)
        for mid in cls:
            mid2cidx_new[mid] = cidx

    # obtain elabel type of cluster
    # cidx2labelinfo = get_entity_info_from_mentions(clusters_new, mid2mention)

    return clusters_new, mid2mention, mid2cidx_new, dict_mid2att


def gen_doc_dict(
        input_txt: str,
        input_ann: str,
        att_keys: list = None,
        subdoc_span: Tuple[int] = None,
) -> dict:

    doc_dict  = {SENS: {}, MENS: {}}

    cluster_list, mid2mention, mid2clsidx, dict_mid2att = load_ann(
        input_ann, subdoc_span=subdoc_span,
        keep_coref_relations=True,
        ignore_span_with_newline=True)

    # generate output tsv rows
    span_list = sorted(
        mid2mention.items(), key=lambda x: (x[1][2], x[1][3])
    )  # mention: (mid, (men_txt, men_label, men_begin, men_end))

    clsidx2rows = {}

    with open(input_txt) as f:
        if subdoc_span:
            logger.info(f'Read: {input_txt} (for subdoc {subdoc_span})')
        else:
            logger.info(f'Read: {input_txt}')

        span_list_idx = 0
        sen_id_num = 0
        bol_idx = 0
        for line in f:
            eol_idx = bol_idx + len(line)

            sen_txt = line.strip('\n')
            if not sen_txt:
                bol_idx = eol_idx
                continue

            sen_id_num += 1
            sen_id = f'{sen_id_num:03d}'
            sen_dict = {TXT: sen_txt, MEN_IDS: []}
            doc_dict[SENS][sen_id] = sen_dict

            while span_list_idx < len(span_list):
                men_id, mention = span_list[span_list_idx]
                men_txt = mention[0]
                etype   = mention[1]
                begin   = mention[2]
                end     = mention[3]

                if bol_idx <= begin < eol_idx:
                    span_begin = begin - bol_idx
                    span_end = end - bol_idx

                    men_dict = {SEN_ID: sen_id,
                                SPAN: (span_begin, span_end),
                                ENT_TYPE: etype,
                                TXT: men_txt,}
                    doc_dict[MENS][men_id] = men_dict
                    sen_dict[MEN_IDS].append(men_id)

                    span_list_idx += 1

                else:
                    break

            bol_idx = eol_idx

    return doc_dict
