import argparse
import os
from typing import Tuple

import openai
import tiktoken

from logzero import logger


def get_tokenizer(
        model_name: str,
) -> object:

    encoder = tiktoken.encoding_for_model(model_name)
    return encoder


def load_examples(
        input_path: str,
        max_num_sents: int = 5,
) -> Tuple[list, list]:

    texts = []
    labels = []

    with open(input_path, encoding='utf-8') as f:
        for line in f:
            array = line.rstrip('\n').split('\t')
            if (len(array) < 2
                or not array[0]
                or not array[1]
            ):
                continue

            texts.append(array[0])
            labels.append(array[1])

            if len(texts) == max_num_sents:
                break

    return texts, labels
                

def read_input_text(
        input_path: str,
) -> list[str]:

    texts = []

    logger.info(f'Read: {input_path}')
    with open(input_path, encoding='utf-8') as f:
        for line in f:
            text = line.rstrip('\n')
            texts.append(text)

    return texts


def gen_message_of_examples(
        texts: list[str],
        labels: list[str],
        prompt_input_head: str,
        prompt_input_tail: str,
) -> str:

    example_list = []
    for text, label in zip(texts, labels):
        example_list.append(f'{prompt_input_head}{text}\n{prompt_input_tail}{label}')
    msg_examples = '\n'.join(example_list)
    return msg_examples


def throw_query(
        message: str,
        model_name: str,
        max_tokens: int,
        temperature: float = 0,
        top_p: float = 1,
) -> str:

    logger.info(f"Start querying a prompt to {model_name}.")
    res = openai.ChatCompletion.create(
        model=model_name,
        messages=[{"role": "user", "content": message}],
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
    )
    res_content = res.choices[0]["message"]["content"]
    logger.info(f"Responce: {res_content}")    
    logger.info(f"Finish querying a prompt to {model_name}.")    
    return res_content


def write_results(
        output_path: str,
        input_texts: list[str],
        results: list[str],
) -> None:

    with open(output_path, 'w', encoding='utf-8') as fw:
        for text, res in zip(input_texts, results):
            fw.write(f"{text}\t{res}\n")
    logger.info(f'Save: {output_path}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input_txt_path', '-i',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--output_txt_path', '-o',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--organization', '-org',
        type=str,
    )
    parser.add_argument(
        '--model_name', '-m',
        type=str,
        default='gpt-3.5-turbo-0613',
    )
    parser.add_argument(
        '--max_tokens',
        type=int,
        default=3000,
    )
    parser.add_argument(
        '--temperature',
        type=float,
        default=0,
    )
    parser.add_argument(
        '--top_p',
        type=float,
        default=1,
    )
    parser.add_argument(
        '--prompt_instruction',
        type=str,
    )
    parser.add_argument(
        '--prompt_input_head',
        type=str,
    )
    parser.add_argument(
        '--prompt_input_tail',
        type=str,
    )
    parser.add_argument(
        '--prompt_examples_path',
        type=str,
    )
    parser.add_argument(
        '--prompt_examples_max_num',
        type=int,
        default=5,
    )
    parser.add_argument(
        '--price_per_token',
        type=float,
        default=0,
    )
    parser.add_argument(
        '--rate_dollar_to_yen',
        type=float,
        default=150,
    )
    parser.add_argument(
        '--simulate_without_querying', '-sim',
        action='store_true',
    )
    args = parser.parse_args()

    if args.simulate_without_querying:
        logger.info(f'Specified --simulate_without_querying.')
    else:
        openai.api_key = os.environ['OPENAI_API_KEY']
        logger.info(f'Set openai.api_key: ***')
        openai.organization = args.organization
        logger.info(f'Set openai.organization: ***')        

    logger.info(f"Model name: {args.model_name}")

    if not args.simulate_without_querying:
        encoder = get_tokenizer(args.model_name)

    # Prepare few-shot examples
    if args.prompt_examples_path:
        ex_texts, ex_labels = load_examples(
            args.prompt_examples_path, max_num_sents=args.prompt_examples_max_num)
        msg_examples = gen_message_of_examples(
            ex_texts, ex_labels, args.prompt_input_head, args.prompt_input_tail)
    else:
        msg_examples = None

    # Read input examples
    input_texts = read_input_text(args.input_txt_path)

    # Throw API query for each input example
    calc_price = (not args.simulate_without_querying
                  and args.price_per_token > 0
                  and args.rate_dollar_to_yen > 0)
    total_price_dol = 0
    results = []
    for text in input_texts:
        if text.strip(' 　'):
            msg = (f'{args.prompt_instruction}\n'
                   + (f'{msg_examples}\n' if msg_examples else '')
                   + f'{args.prompt_input_head}{text}\n{args.prompt_input_tail}')

            if args.simulate_without_querying:
                logger.info(f'Query (simulation):\n{msg}')
                results.append(None)
            else:
                if calc_price:
                    n_tokens = len(encoder.encode(msg))
                    price_dol = n_tokens * args.price_per_token
                    price_yen = price_dol * args.rate_dollar_to_yen
                    total_price_dol += price_dol
                    logger.info(f'Estimated price: ${price_dol:.6f} (\\{price_yen:.6f})')

                logger.info(f'Query:\n{msg}')
                res_content = throw_query(msg, args.model_name,
                                          args.max_tokens,
                                          args.temperature,
                                          args.top_p)
                results.append(res_content)
        else:
            logger.info(f'Skip empty text')
            results.append(None)

    if calc_price:
        total_price_yen = total_price_dol * args.rate_dollar_to_yen
        logger.info(f'Total estimated price: ${total_price_dol:.6f} (\\{total_price_yen:.6f})')

    # Save results
    write_results(args.output_txt_path, input_texts, results)


if __name__ == "__main__":
    main()
