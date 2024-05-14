from typing import Tuple

from logzero import logger

from ent_tools.util.constants import (
    SENS, MENS, ENTS, SEC_ID, SEN_ID, MEN_IDS, MEM_MEN_IDS, ENT_ID, TXT, SPAN, ENT_TYPE, COREF, COREF_ATTR, DIR_MEN_PAIRS, NOTES,
)


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

            if (not in_subdoc) and line.startswith('<title>'):
                dt_begin = bol_idx

            if line.startswith('<subdoc'): # page_begin=* or fulldoc='True'
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
        coref_tag_name: str = None,
        directed_coref_tag_name: str = None,
) -> Tuple:

    if coref_tag_name == None:
        coref_tag_name = COREF
    if directed_coref_tag_name == None:
        directed_coref_tag_name = COREF_ATTR

    clusters = []
    mid2mention = {}  # mid (e.g. T1) -> men_txt, men_label, begin, end
    mid2notes = {}
    dict_mid2att = {}
    directed_rels = set()
    mid_exclude = set()

    with open(input_ann) as f:
        if subdoc_span:
            logger.info(f'Read: {input_ann} (for subdoc {subdoc_span})')
        else:
            logger.info(f'Read: {input_ann}')

        for line in f:
            line = line.strip('\n')
            if line.startswith('T'): # mention
                array = line.split('\t')
                men_id = array[0]
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

            elif line.startswith('A'): # attribute tag
                array = line.split('\t')
                att_info = array[1].split(' ')
                att_name = att_info[0]
                men_id = att_info[1]
                att_label = att_info[2] if len(att_info) > 2 else True

                if not att_name in dict_mid2att:
                    dict_mid2att[att_name] = {}
                mid2att = dict_mid2att[att_name]
                assert not men_id in mid2att
                mid2att[men_id] = att_label

            elif line.startswith('*'): # undirected relation
                array = line.split('\t')
                coref_info = array[1].split(' ')
                coref_name = coref_info[0]
                if coref_name != coref_tag_name:
                    continue

                mids = [e for e in coref_info[1:]]
                clusters.append(mids)
                cidx = len(clusters) - 1

            elif line.startswith('R'): # directed relation
                array    = line.split('\t')
                rel_info = array[1].split(' ')
                rel_name = rel_info[0]
                men_id1	 = rel_info[1].split(':')[1]
                men_id2	 = rel_info[2].split(':')[1]
                directed_rels.add((rel_name, men_id1, men_id2))

                if rel_name == directed_coref_tag_name:
                    clusters.append([men_id1, men_id2])

            elif line.startswith('#'): # AnnotatorNotes
                array = line.split('\t')
                assert len(array) == 3
                men_id = array[1].split(' ')[1]
                notes  = array[2]
                mid2notes[men_id] = notes

    # remove mid in mid_exclude
    for mid_ex in mid_exclude:
        for mid2att in dict_mid2att:
            if mid_ex in mid2att:
                del mid2att[mid_ex]

        for i, mids in enumerate(clusters):
            if mid_ex in mids:
                mids.remove(mid_ex)

    clusters_new = []
    for mids in clusters:
        if len(mids) > 0:
            clusters_new.append(mids)

    if keep_coref_relations:
        return clusters_new, mid2mention, None, None, dict_mid2att, mid2notes

    # merge clusters if there are clusters with common elements
    clusters_new = merge_clusters_until_convergence(clusters_new)

    # assign cidx to each singleton mention and add it to clusters_new
    mids_already_added = set(sum([cls for cls in clusters_new], []))
    for mid in mid2mention.keys():
        if (mid in mids_already_added
            or mid in mid_exclude
        ):
            continue
        cidx = len(clusters_new)
        clusters_new.append([mid])
    
    mid2cidx = {}
    for cidx, cls in enumerate(clusters_new):
        for mid in cls:
            mid2cidx[mid] = cidx

    # obtain elabel type of cluster
    # cidx2labelinfo = get_entity_info_from_mentions(clusters_new, mid2mention)

    return clusters_new, mid2mention, mid2cidx, directed_rels, dict_mid2att, mid2notes


def gen_doc_dict(
        input_txt: str,
        input_ann: str,
        att_keys: list = None,
        subdoc_span: Tuple[int] = None,
        coref_tag_name: str = None,
        directed_coref_tag_name: str = None,
        assign_section_id: bool = False,
) -> dict:

    doc_dict  = {SENS: {}, MENS: {}, ENTS: {}}

    cluster_list, mid2mention, mid2clsidx, directed_rels, dict_mid2att, mid2notes = load_ann(
        input_ann, subdoc_span=subdoc_span,
        ignore_span_with_newline=True,
        coref_tag_name=coref_tag_name,
        directed_coref_tag_name=directed_coref_tag_name,
    )

    use_coref = len(cluster_list) > 0

    # generate output tsv rows
    span_list = sorted(
        mid2mention.items(), key=lambda x: (x[1][2], x[1][3])
    )  # mention: (mid, (men_txt, men_label, men_begin, men_end))

    clsidx2rows = {}
    clsidx2entid = {}
    menid_old2new = {}

    with open(input_txt) as f:
        if subdoc_span:
            logger.info(f'Read: {input_txt} (for subdoc {subdoc_span})')
        else:
            logger.info(f'Read: {input_txt}')

        span_list_idx = 0
        sec_id_num = 1
        sen_id_num = 0
        ent_id_num = 1
        flag_cont_empty = False
        bol_idx = 0

        for line in f:
            eol_idx = bol_idx + len(line)

            if (subdoc_span
                and (bol_idx < subdoc_span[0]
                     or eol_idx > subdoc_span[1]
                )
            ):
                bol_idx = eol_idx
                continue

            sen_txt = line.strip('\n')
            if not sen_txt:
                bol_idx = eol_idx

                if (assign_section_id
                    and sen_id_num > 0
                    and not flag_cont_empty
                ):
                    sec_id_num += 1

                flag_cont_empty = True
                continue

            flag_cont_empty = False

            sen_id_num += 1
            sen_id = f'{sen_id_num:03d}'
            if assign_section_id:
                sec_id = f'{sec_id_num:03d}'
                sen_dict = {SEC_ID: sec_id, TXT: sen_txt, MEN_IDS: []}
            else:
                sen_dict = {TXT: sen_txt, MEN_IDS: []}

            men_ids_new = []
            doc_dict[SENS][sen_id] = sen_dict

            while span_list_idx < len(span_list):
                men_id_old, mention = span_list[span_list_idx]
                men_id_new = f'M{span_list_idx+1:03d}'
                menid_old2new[men_id_old] = men_id_new
                men_txt = mention[0]
                etype   = mention[1]
                begin   = mention[2]
                end     = mention[3]

                if bol_idx <= begin < eol_idx:
                    span_begin = begin - bol_idx
                    span_end = end - bol_idx

                    men_dict = {SEN_ID: sen_id,
                                SPAN: (span_begin, span_end),
                                TXT: men_txt,
                                ENT_TYPE: etype,
                    }

                    for key, mid2att in dict_mid2att.items():
                        if men_id_old in mid2att:
                            men_dict[key] = mid2att[men_id_old]

                    if men_id_old in mid2notes:
                        notes = mid2notes[men_id_old]
                        men_dict[NOTES] = notes

                    if men_id_old in mid2clsidx:
                        clsidx = mid2clsidx[men_id_old]
                        # ent_id = f'E{clsidx+1:03d}'
                        if clsidx in clsidx2entid:
                            ent_id = clsidx2entid[clsidx]
                        else:
                            ent_id = f'E{ent_id_num:03d}'
                            clsidx2entid[clsidx] = ent_id
                            ent_id_num += 1

                        men_dict[ENT_ID] = ent_id

                    doc_dict[MENS][men_id_new] = men_dict
                    men_ids_new.append(men_id_new)

                    span_list_idx += 1

                else:
                    break

            bol_idx = eol_idx
            sen_dict[MEN_IDS] = men_ids_new

    men1_to_dir_pair_str = {}
    if directed_rels:
        for rel_name, men_id_old1, men_id_old2 in directed_rels:
            if men_id_old1 in menid_old2new and men_id_old2 in menid_old2new:
                men_id_new1 = menid_old2new[men_id_old1]
                men_id_new2 = menid_old2new[men_id_old2]
                men1_to_dir_pair_str[men_id_new1] = f'{men_id_new1}-{men_id_new2}'

    # fix order of dict registration
    for ent_id_num_i in range(1, ent_id_num):
        ent_id = f'E{ent_id_num_i:03d}'
        doc_dict[ENTS][ent_id] = None

    for clsidx, cluster in enumerate(cluster_list):
        # ent_id = f'E{clsidx+1:03d}'
        ent_id = clsidx2entid[clsidx]
        ent_dict = {
            MEM_MEN_IDS: sorted([menid_old2new[men_id_old] for men_id_old in cluster]),
        }

        directed_men_pairs = []
        for men_id_new in ent_dict[MEM_MEN_IDS]:
            if men_id_new in men1_to_dir_pair_str:
                directed_men_pairs.append(men1_to_dir_pair_str[men_id_new])
        if directed_men_pairs:
            ent_dict[DIR_MEN_PAIRS] = ';'.join(sorted(directed_men_pairs))

        doc_dict[ENTS][ent_id] = ent_dict

    return doc_dict
