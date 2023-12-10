#!/bin/bash

# Set file paths
INPUT_DIR=../data/original/sample_ja_ner
OUTPUT_DIR=../data/processed/sample_ja_ner
mkdir -p $OUTPUT_DIR/json_per_doc
mkdir -p $OUTPUT_DIR/json

## Convert ann -> json
for TXT_PATH in $INPUT_DIR/*.txt; do
    # check whether input file is empty
    if [ ! -s "$TXT_PATH" ]; then
        echo Skip: empty file $TXT_PATH
        continue
    fi

    FILE_NAME=`basename $TXT_PATH`
    DOC_NAME=${FILE_NAME%.*}
    ANN_PATH=$INPUT_DIR/$DOC_NAME.ann
    
    python ent_tools/data_conversion/brat_ann_to_json.py \
           -txt $TXT_PATH \
           -ann $ANN_PATH \
           -json_dir $OUTPUT_DIR/json_per_doc \
           -json_name $DOC_NAME
done

## Merge json files into a single json file
MERGED_JSON_PATH=$OUTPUT_DIR/json/all.json
python ent_tools/data_conversion/merge_jsons_into_single_json.py \
       -i $OUTPUT_DIR/json_per_doc \
       -o $MERGED_JSON_PATH
