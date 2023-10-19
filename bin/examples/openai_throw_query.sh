#!/bin/bash

# Need to set API key in environment; e.g. `export OPENAI_API_KEY="***"`

# Set organization for OpenAI API
ORGANIZATION=

# Set constants for price estimation
# cf. <https://openai.com/pricing>
RATE_DOLLAR_TO_YEN=150
PRICE_PER_TOKEN=`bc  <<< "scale=7; 0.0015/1000"`

# Change prompt infomation if necessary
PROMPT_INSTRUCT='Given the list of entity types ["ORGANIZATION", "LOCATION", "FACILITY"], read the given sentence and find out all words/phrases that indicate the above types of named entities. Answer in the formeat ["entity_name","entity_type";"entity_name","entity_type";...] in the order of appearance without any explanation. Extract all instances even when named entities with the same exspression appears multiple times. If no entity exists, then just answer "[]".'
PROMPT_INPUT_HEAD='Sentence: '
PROMPT_INPUT_TAIL='Answer: '
PROMPT_EXAMPLES_PATH=data/supplement/llm_prompt/examples_jawiki_nara_city.tsv

# Set model name; e.g., "gpt-3.5-turbo-0613" or "gpt-4-0613"
MODEL_NAME="gpt-3.5-turbo-0613"

# Set the number of shots for prompts
NUM_SHOT=5

# Set input/output file paths
RUN_ID="${MODEL_NAME}_${NUM_SHOT}-shot_run1"
OUTPUT_DIR=data/output/sample_ja_ner/openai/$RUN_ID
mkdir -p $OUTPUT_DIR/txt
mkdir -p $OUTPUT_DIR/json_per_doc
mkdir -p $OUTPUT_DIR/json

INPUT_TXT_DIR=data/original/sample_ja_ner
for INPUT_TXT_PATH in $INPUT_TXT_DIR/*.txt; do
    DOC_NAME=`basename $INPUT_TXT_PATH`
    DOC_NAME=${DOC_NAME%.*}
    OUTPUT_TXT_PATH=$OUTPUT_DIR/txt/$DOC_NAME.txt
    OUTPUT_JSON_PATH=$OUTPUT_DIR/json_per_doc/$DOC_NAME.json

    python src/nlp_tools/openai/throw_query.py \
           -i $INPUT_TXT_PATH \
           -o $OUTPUT_TXT_PATH \
           -org $ORGANIZATION \
           -m $MODEL_NAME \
           --prompt_instruction "$PROMPT_INSTRUCT" \
           --prompt_input_head "$PROMPT_INPUT_HEAD" \
           --prompt_input_tail "$PROMPT_INPUT_TAIL" \
           --prompt_examples_path "$PROMPT_EXAMPLES_PATH" \
           --prompt_examples_max_num 5 \
           --rate_dollar_to_yen $RATE_DOLLAR_TO_YEN \
           --price_per_token $PRICE_PER_TOKEN \
    
    python src/nlp_tools/openai/convert_output_to_json.py \
           -i $OUTPUT_TXT_PATH \
           -o $OUTPUT_JSON_PATH
done

## Merge json files into a single json file
MERGED_JSON_PATH=$OUTPUT_DIR/json/all.json
python src/data_conversion/merge_jsons_into_single_json.py \
       -i $OUTPUT_DIR/json_per_doc \
       -o $MERGED_JSON_PATH
