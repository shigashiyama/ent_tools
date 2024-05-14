import copy

from ent_tools.util.constants import (
    SENS, MENS, ENTS, SEN_ID, ENT_ID, MEM_MEN_IDS, TXT, SPAN, ENT_TYPE, ENT_TYPE_MRG,
    DIR_MEN_PAIRS, NOTES, HAS_REF, REF_URL, REF_URLS,
)

from logzero import logger


WIKIDATA_URL_PREFIX = 'https://www.wikidata.org'
JAWIKI_URL_PREFIX   = 'https://ja.wikipedia.org'
OSM_URL_PREFIX      = 'https://www.openstreetmap.org'
WIKIDATA            = 'wikidata'
JAWIKI              = 'ja.wikipedia'
OTHER               = 'other'
NIL                 = 'NIL'

LINK_TYPE        = 'LinkType'
LINK_TYPE_SHARE0 = 'OVERLAP'
LINK_TYPE_SHARE  = 'SHARE'

METONYMY0 = 'Metonymy'
METONYMY  = 'metonymic_entity_type'
REF_TYPE  = 'ref_type'
REF_SITE  = 'ref_site'
FEATURE0  = 'Feature'
FEATURE   = 'feature'
VAGUE     = 'VAGUE'
HAS_VAGUE_REF = 'has_vague_ref'

NOMINAL = 'NOMINAL'
MIX     = 'MIX'


def get_ref_site(
        ref_url: str,
) -> str:

    if ref_url.startswith(WIKIDATA_URL_PREFIX):
        ref_site = WIKIDATA
    elif ref_url.startswith(JAWIKI_URL_PREFIX):
        ref_site = JAWIKI
    else:
        ref_site = OTHER

    return ref_site
    

def merge_entity_type(
        ent_type_set: set[str],
) -> str:

    ent_type_list = list(ent_type_set)

    if len(ent_type_list) == 1:
        return ent_type_list[0]

    elif len(ent_type_list) == 2:
       if NOMINAL in ent_type_list:
           nom_idx = ent_type_list.index(NOMINAL)
           oth_idx = 1 - nom_idx # nom_idx=0 ->1; nom_idx=1 ->0
           return ent_type_list[oth_idx]

       else:
           return MIX

    else:
        return MIX


def convert_json_for_jel(
        doc: dict,
        docid: str = None,
        kb_data: dict = None,
) -> dict:

    doc_new = {SENS: doc[SENS], MENS: {}, ENTS: {}}

    # add mentions
    for men_id, men_orig in doc[MENS].items():
        men_new = {}
        men_new.update(men_orig)
        men_new[ENT_ID] = f'{men_orig[ENT_ID]}_'

        # HAS_REF, REF_URL, REF_TYPE は最終的には mention から削除
        men_new[HAS_REF]  = False
        if NOTES in men_new:
            notes = men_new[NOTES]
            del men_new[NOTES]

            if notes != NIL:
                men_new[HAS_REF]  = True
                men_new[REF_URL]  = notes

                if LINK_TYPE in men_new:
                    if men_new[LINK_TYPE] == LINK_TYPE_SHARE0:
                        men_new[REF_TYPE] = LINK_TYPE_SHARE
                    else:
                        men_new[REF_TYPE] = men_new[LINK_TYPE]
                    del men_new[LINK_TYPE]
                else:
                    men_new[REF_TYPE] = None
        
        if LINK_TYPE in men_new:
            logger.warning(f'{men_id} does not have URL but has LINK_TYPE: {men_new}')
            del men_new[LINK_TYPE]

        if METONYMY0 in men_new:
            men_new[METONYMY] = men_new[METONYMY0]
            del men_new[METONYMY0]

        if FEATURE0 in men_new:
            men_new[FEATURE] = men_new[FEATURE0]
            del men_new[FEATURE0]

        doc_new[MENS][men_id] = men_new

    refinfo_to_entids = {}

    # add entities
    for ent_id, ent in doc[ENTS].items():
        ent_id_tmp = f'{ent_id}_'
        ent_new = {}
        ent_new.update(ent)
        
        # delete DIR_MEN_PAIRS because Coref is acutually indirected relation in JEL ann data
        if DIR_MEN_PAIRS in ent_new:
            del ent_new[DIR_MEN_PAIRS]
        # if DIR_MEN_PAIRS in ent_new:
        #     dir_men_pairs = ent_new[DIR_MEN_PAIRS]
        #     ent_new[DIR_MEN_PAIRS] = [pair.split('-') for pair in dir_men_pairs.split(';')]

        url_list = []
        ltype_list = []
        for men_id in ent[MEM_MEN_IDS]:
            assert men_id in doc_new[MENS], f'Document does not contain {men_id} for {ent_id} (entity={ent})'                    

            men_new = doc_new[MENS][men_id]
            if men_new[HAS_REF]:
                url_list.append(men_new[REF_URL])

                if (REF_TYPE in men_new
                    and men_new[REF_TYPE] != 'VAGUE' # remove VAGUE at entity level
                ):
                    ltype_list.append(men_new[REF_TYPE])

        urls = set(url_list)
        ltypes = set(ltype_list)
        if len(urls) > 1 or len(ltypes) > 1:
            # check
            logger.warning(f'Multi URLs or LinkTypes for an entity:')
            for men_id, url, ltype in zip(ent[MEM_MEN_IDS], url_list, ltype_list):
                men_new  = doc[MENS][men_id]
                men_text = men_new[TXT]
                span     = men_new[SPAN]
                sen      = doc[SENS][men_new[SEN_ID]]
                sen_text = sen[TXT]
                l_cont   = sen_text[:span[0]]
                r_cont   = sen_text[span[1]:]
                logger.warning(f'- {docid}\t{ent_id}\tT{men_id[1:]}\t{l_cont}\t{men_text}\t{r_cont}\t{url}\t{ltype}')

        if len(urls) == 0:
            ent_new[HAS_REF] = False
            refinfo_to_entids[(ent_id_tmp, None)] = set({ent_id_tmp})
        else:
            url = url_list[0]
            ent_new[HAS_REF]  = True
            # ent_new[REF_SITE] = get_ref_site(url)

            if len(ltypes) == 0:
                ent_new[REF_TYPE] = None
            elif len(ltypes) == 1:
                ent_new[REF_TYPE] = ltype_list[0]
            else:
                ent_new[REF_TYPE] = ltype_list[0]
                logger.info(f'Multi_LTypes: {ltypes}')

            if url.startswith(WIKIDATA_URL_PREFIX):
                qid = url.split('/')[-1]
                ent_new[REF_URLS] = {'wikidata': url}

                if kb_data and qid in kb_data:
                    kb_ins = kb_data[qid][0]
                    if 'jawiki' in kb_ins:
                        ent_new[REF_URLS].update(
                            {'ja.wikipedia': kb_ins['jawiki']['value']}
                        )

                    if 'osm_rel_id' in kb_ins:
                        osm_rel_id = kb_ins['osm_rel_id']['value']
                        ent_new[REF_URLS].update(
                            {'openstreetmap': f'{OSM_URL_PREFIX}/relation/{osm_rel_id}'}
                        )
                    elif 'osm_way_id' in kb_ins:
                        osm_way_id = kb_ins['osm_way_id']['value']
                        ent_new[REF_URLS].update(
                            {'openstreetmap': f'{OSM_URL_PREFIX}/way/{osm_way_id}'}
                        )
                    elif 'osm_node_id' in kb_ins:
                        osm_node_id = kb_ins['osm_node_id']['value']
                        ent_new[REF_URLS].update(
                            {'openstreetmap': f'{OSM_URL_PREFIX}/node/{osm_node_id}'}
                        )

                    if 'country' in kb_ins:
                        wd_country = kb_ins['country']['value']
                        ent_new[REF_URLS].update(
                            {'wikidata_country': wd_country}
                        )

                    if 'coordinate' in kb_ins:
                        coordinate  = kb_ins['coordinate']['value'].replace('Point(', '').replace(')', '')
                        coordinate  = coordinate.split(' ')
                        ent_new['coordinate'] = [coordinate[1], coordinate[0]]

            elif url.startswith(JAWIKI_URL_PREFIX):
                ent_new[REF_URLS] = {'ja.wikipedia': url}

            else:
                ent_new[REF_URLS] = {'other': url}

            key = (url, ent_new[REF_TYPE])
            if not key in refinfo_to_entids:
                refinfo_to_entids[key] = set()
            refinfo_to_entids[key].add(ent_id_tmp)

        doc_new[ENTS][ent_id_tmp] = ent_new

    # merge entities with the same URL and ref_type = None/VAGUE
    ent_id_num = 1
    old_to_new_entid = {}
    for key, ent_ids in refinfo_to_entids.items(): # TODO sort by ent_id
        new_entid = f'E{ent_id_num:03d}'
        for ent_id in sorted(ent_ids):
            old_to_new_entid[ent_id] = new_entid
        ent_id_num += 1

    # refrect merged entities and their IDs, and set ENT_TYPE_MRG
    doc_new2 = {SENS: doc_new[SENS], MENS: {}, ENTS: {}}

    for men_id, men_new in doc_new[MENS].items():
        men_new2 = {}
        men_new2.update(men_new)

        if men_new2[HAS_REF]:
            if men_new2[REF_TYPE] == VAGUE:
                men_new2[HAS_VAGUE_REF] = True
            del men_new2[REF_TYPE]
            del men_new2[REF_URL]

        old_ent_id = men_new[ENT_ID]
        men_new2[ENT_ID] = old_to_new_entid[old_ent_id]
        
        doc_new2[MENS][men_id] = men_new2

    for old_ent_id in sorted(doc_new[ENTS].keys()):
        new_ent_id = old_to_new_entid[old_ent_id]
        ent_orig = doc_new[ENTS][old_ent_id]

        if not new_ent_id in doc_new2[ENTS]:
            doc_new2[ENTS][new_ent_id] = copy.deepcopy(ent_orig)
        else:
            ent_current = doc_new2[ENTS][new_ent_id]
            ent_current[MEM_MEN_IDS].extend(ent_orig[MEM_MEN_IDS])

            # if DIR_MEN_PAIRS in ent_current or DIR_MEN_PAIRS in ent_orig:
            #     if not DIR_MEN_PAIRS in ent_current:
            #         ent_current[DIR_MEN_PAIRS] = copy.deepcopy(ent_orig[MEM_MEN_IDS])
            #     elif not DIR_MEN_PAIRS in ent_orig:
            #         pass
            #     else:
            #         ent_current[DIR_MEN_PAIRS].extend(ent_orig[DIR_MEN_PAIRS])

            assert ent_current[HAS_REF]  == ent_orig[HAS_REF]
            # assert ent_current[REF_URL]  == ent_orig[REF_URL]
            # assert ent_current[REF_SITE] == ent_orig[REF_SITE]
            assert ent_current[REF_TYPE] == ent_orig[REF_TYPE] 

    # add ENT_TYPE_MRG and sort MEM_MEN_IDS
    for ent_id, ent in doc_new2[ENTS].items():
        ent[MEM_MEN_IDS] = sorted(ent[MEM_MEN_IDS])

        ent_type_set = set(
            [doc_new2[MENS][men_id][ENT_TYPE] for men_id in ent[MEM_MEN_IDS]]
        )
        ent[ENT_TYPE_MRG] = merge_entity_type(ent_type_set)

    return doc_new2
