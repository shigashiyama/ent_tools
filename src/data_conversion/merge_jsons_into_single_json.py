import argparse
from collections import Counter
import json
import os
import sys

from logzero import logger

sys.path.append('src')          # TODO remove
from common.constants import SENS, MENS, ENT_TYPE
from common.data_io import load_json, write_as_json


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
        for doc_id, doc in data.items():
            counter['num_docs'] += 1
            counter['num_sens'] += len(doc[SENS])
            counter['num_mens'] += len(doc[MENS])

            for men_id, men in doc[MENS].items():
                counter[f'num_mens:{men[ENT_TYPE]}'] += 1

        logger.info('Data statistics.')
        main_keys = ['num_docs', 'num_sens', 'num_mens']
        for key in main_keys:
            val = counter[key]
            logger.info(f'{key}\t{val}')
            
        for key, val in sorted(counter.items()):
            if not key in main_keys:
                logger.info(f'{key}\t{val}')


if __name__ == '__main__':
    main()
