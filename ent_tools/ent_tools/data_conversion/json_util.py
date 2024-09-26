import copy

import logzero
from logzero import logger

from sentence_segmenter import Segmenter


from ent_tools.util.constants import (
    SECS, SENS, MENS, ENTS, SEC_ID, SEN_ID, MEN_IDS, MEM_MEN_IDS, ENT_ID, TXT, SPAN, ENT_TYPE, COREF, COREF_ATTR, NOTES,
)


def check_attributes(
        doc: dict,
        doc_id: str = None,
) -> None:
    logzero.loglevel(20)

    sens = doc[SENS]

    has_secs = SECS in doc
    if has_secs:
        secs = doc[SECS]

    has_mens = MENS in doc
    if has_mens:
        mens = doc[MENS]

    has_ents = ENTS in doc
    if has_ents:
        ents = doc[ENTS]

    if has_secs:
        for sec_id, sec in secs.items():
            # sec's sens are associated with the sec
            for sen_id in sec[SEN_IDS]:
                assert sec_id == sens[sen_id][SEC_ID]

    for sen_id, sen in sens.items():
        if has_secs:
            # sen's sec has the sen
            sec_id = sen[SEC_ID]
            assert sen_id in secs[sec_id][SEN_IDS]

        if has_mens:
            # sen's mens are associated with the sen
            for men_id in sen[MEN_IDS]:
                assert sen_id == mens[men_id][SEN_ID]

    if has_mens:
        for men_id, men in mens.items():
            # men's sen has the men
            sen_id = men[SEN_ID]
            assert men_id in sens[sen_id][MEN_IDS]
     
            if has_ents:
                # men's ent has the men
                ent_id = men[ENT_ID]
                assert ent_id == None or ent_id in ents, ent_id

                if ent_id != None:
                    logger.debug(f'- M {men_id} {men[TXT]} - E {ent_id} -> {ent_id in ents}')
                    assert men_id in ents[ent_id][MEM_MEN_IDS], f'{men_id} {men[TXT]} - {ent_id} -> {ents[ent_id][MEM_MEN_IDS]}'

    if has_mens and has_ents:
        for ent_id, ent in ents.items():
            # ent's mens are associated with the ent
            for men_id in ent[MEM_MEN_IDS]:
                logger.debug(f'- E {ent_id} - M {men_id} -> {mens[men_id][ENT_ID]}')
                assert ent_id == mens[men_id][ENT_ID]


def segment_sentence_in_doc_dict(doc: dict) -> dict:
    debug = False

    segmenter = Segmenter()

    doc_new  = {SENS: {}, MENS: {}, ENTS: doc[ENTS]}
    secid_to_senids = {}

    senidold_to_secid_and_span = {}
    senidnew_to_secid_and_span = {}

    for sen_id, sen in doc[SENS].items():
        sec_id = sen[SEC_ID]
        if not sec_id in secid_to_senids:
            secid_to_senids[sec_id] = []
        secid_to_senids[sec_id].append(sen_id)

    for sec_id, sen_ids in secid_to_senids.items():
        texts = [doc[SENS][sen_id][TXT] for sen_id in sen_ids]
        full_text = ''.join(texts)

        texts_new = segmenter.sentencize(full_text)
        full_text_new = ''.join(texts_new)
        assert full_text == full_text_new

        # set senidold_to_secid_and_span
        begin_idx = 0
        for sen_id, text in zip(sen_ids, texts):
            end_idx = begin_idx + len(text)
            senidold_to_secid_and_span[sen_id] = (sec_id, begin_idx, end_idx)
            begin_idx = end_idx

        # set senidnew_to_secid_and_span
        begin_idx = 0
        for i, text_new in enumerate(texts_new):
            sen_id_new = f'{sec_id}-{i+1:02d}'
            doc_new[SENS][sen_id_new] = {
                SEC_ID: sec_id,
                TXT: text_new,
                MEN_IDS: [],
            }

            end_idx = begin_idx + len(text_new)
            senidnew_to_secid_and_span[sen_id_new] = (sec_id, begin_idx, end_idx)
            begin_idx = end_idx

        if debug:
            print(senidold_to_secid_and_span)
            print(senidnew_to_secid_and_span)
            print(doc_new[SENS][sen_id_new])

    for men_id, mention in doc[MENS].items():
        sen_id      = mention[SEN_ID]
        sen_span    = senidold_to_secid_and_span[sen_id][1:]
        sec_id      = doc[SENS][sen_id][SEC_ID]
        span        = mention[SPAN]
        text        = mention[TXT]
        span_global = (sen_span[0]+span[0], sen_span[0]+span[1])

        sen_id_new   = get_sentence_id_from_span(
            span_global[0], sec_id, senidnew_to_secid_and_span)
        sen_span_new = senidnew_to_secid_and_span[sen_id_new][1:]
        sen_new      = doc_new[SENS][sen_id_new]
        sen_text_new = sen_new[TXT]
        sec_id_new   = sen_new[SEC_ID]
        span_new     = [span_global[0]-sen_span_new[0], span_global[1]-sen_span_new[0]]
        text_new     = sen_text_new[span_new[0]:span_new[1]]

        if debug:
            print('sec_old', sec_id)
            print('sen_old', sen_id, sen_span)
            print('men_old', text, span, '->', span_global)
            print('sec_new', sec_id_new)
            print('sen_new', sen_id_new, sen_span_new)
            print('men_new', text_new, span_new)
            print()

        assert sec_id == sec_id_new
        assert sen_span_new[0] <= span_global[0] and span_global[1] <= sen_span_new[1]
        assert 0 <= span_new[0] and span_new[1] <= (sen_span_new[1]-sen_span_new[0])
        assert text_new == text

        mention_new = copy.deepcopy(mention)
        mention_new[SEN_ID] = sen_id_new
        mention_new[SPAN] = span_new
        sen_new[MEN_IDS].append(men_id)
        doc_new[MENS][men_id] = mention_new

    return doc_new


def get_sentence_id_from_span(
        span_begin: int,
        sec_id: str,
        senid_to_secid_and_span: dict[str, list[int, int, int]],
) -> str:

    for sen_id, (sec_id_now, sen_span_begin, sen_span_end) in senid_to_secid_and_span.items():
        if sec_id_now != sec_id:
            continue
        if span_begin < sen_span_end:
            return sen_id

    assert False
