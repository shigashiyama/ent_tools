import json

from logzero import logger


def load_json(
        input_path: str,
) -> dict:

    with open(input_path, encoding='utf-8') as f:
        logger.info(f'Read: {input_path}')
        data = json.load(f)
    return data


def load_jsonl(
        input_path: str,
) -> dict:

    data = {}
    with open(input_path, encoding='utf-8') as f:
        logger.info(f'Read: {input_path}')
        for line in f:
            data_line = json.loads(line.strip('\n'))
            data.update(data_line)
    return data


def write_as_json(
        data: dict,
        output_path: str,
) -> None:

    with open(output_path, 'w', encoding='utf-8') as fw:
        json.dump(data, fw, ensure_ascii=False, indent=2)
    logger.info(f'Saved: {output_path}')
