import argparse
from collections import Counter
import json
import os

from logzero import logger

from ent_tools.util.constants import SENS, MENS, ENTS, MEM_MEN_IDS, TXT, ENT_TYPE, MEN_TYPE, HAS_REF, REF_URL
from ent_tools.util.data_io import load_json, write_as_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input_dirs', '-i',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--output_path', '-o',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--target_ids_path', '-t',
        type=str,
    )
    args = parser.parse_args()

    if args.target_ids_path:
        target_ids = set()
        with open(args.target_ids_path) as f:
            for line in f:
                target_ids.add(line.strip('\n'))
        logger.info(f'Target ids: {target_ids}')
    else:
        target_ids = None

    data = {}
    for input_dir in args.input_dirs.split(','):
        for file_name in os.listdir(input_dir):
            if not file_name.endswith('.json'):
                continue

            doc_id = file_name.split('.')[0]
            if target_ids and not doc_id in target_ids:
                continue                    

            input_path = os.path.join(input_dir, file_name)
            data_orig = load_json(input_path)
            for doc_id, doc in data_orig.items():
                if len(doc[SENS]) == 0:
                    logger.info(f'Skip document with no sentences: {doc_id}')
                    continue

                data[doc_id] = data_orig[doc_id]

    if data:
        write_as_json(data, args.output_path)

        # show statistics
        counter = Counter()
        key2sets = {'num_mens': set()}

        for doc_id, doc in data.items():
            counter['num_docs'] += 1
            if SENS in doc:
                counter['num_sens'] += len(doc[SENS])

            if MENS in doc:
                counter['num_mens'] += len(doc[MENS])

                for men_id, men in doc[MENS].items():
                    key2sets['num_mens'].add(men[TXT])

                    if ENT_TYPE in men:
                        key = f'num_mens:{men[ENT_TYPE]}'
                        counter[key] += 1
                        if not key in key2sets:
                            key2sets[key] = set()
                        key2sets[key].add(men[TXT])

                    if MEN_TYPE in men:
                        counter[f'num_mens:{men[MEN_TYPE]}'] += 1

            if ENTS in doc:
                counter['num_ents'] += len(doc[ENTS])

                for ent_id, ent in doc[ENTS].items():
                    if HAS_REF in ent and ent[HAS_REF]:
                        counter['num_ents:has_ref'] += 1

                    has_name = False
                    for men_id in ent[MEM_MEN_IDS]:
                        men = doc[MENS][men_id]
                        if men[ENT_TYPE].endswith('NAME'):
                            has_name = True

                    if has_name:
                        counter['num_ents:has_name'] += 1

                    # tmp
                    if REF_URL in ent:
                        if ent[REF_URL].startswith('https://www.wikidata.org'):
                            key = 'num_ents:has_wikidata_ref'
                            counter[key] += 1
                            if not key in key2sets:
                                key2sets[key] = set()
                            key2sets[key].add(ent[REF_URL])
                        else:
                            key = 'num_ents:has_other_ref'
                            counter[key] += 1
                            if not key in key2sets:
                                key2sets[key] = set()
                            key2sets[key].add(ent[REF_URL])

        logger.info('Data statistics.')
        main_keys = ['num_docs', 'num_sens', 'num_mens', 'num_ents']
        for key in main_keys:
            val = counter[key]
            if key in key2sets:
                val2 = len(key2sets[key])
                logger.info(f'{key}\t{val}\t({val2})')
            else:
                logger.info(f'{key}\t{val}')
            
        for key, val in sorted(counter.items()):
            if not key in main_keys:
                if key in key2sets:
                    val2 = len(key2sets[key])
                    logger.info(f'{key}\t{val}\t({val2})')
                else:
                    logger.info(f'{key}\t{val}')


if __name__ == '__main__':
    main()
