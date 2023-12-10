#!/bin/bash

# Set model name. e.g., ja_ginza, ja_ginza_electra, ja_ginza_bert_large
MODEL_NAME="ja_ginza_electra"

DATA_IN_DIR=../data/original/sample_ja_ner
DATA_OUT_DIR=../data/output/sample_ja_ner/ginza/$MODEL_NAME
mkdir -p $DATA_OUT_DIR
mkdir -p $DATA_OUT_DIR/tsv_for_ner
mkdir -p $DATA_OUT_DIR/conll_per_doc
mkdir -p $DATA_OUT_DIR/json_per_doc
mkdir -p $DATA_OUT_DIR/json

## Parse txt using ginza and save result as json
for TXT_PATH in $DATA_IN_DIR/*.txt; do
    # check whether input file is empty
    if [ ! -s "$TXT_PATH" ]; then
        echo Skip: empty file $TXT_PATH
        continue
    fi

    FILE_NAME=`basename $TXT_PATH`
    DOC_NAME="${FILE_NAME%.*}"
    TSV_PATH=$DATA_OUT_DIR/tsv_for_ner/$DOC_NAME.tsv
    GINZA_CNL_PATH=$DATA_OUT_DIR/conll_per_doc/$DOC_NAME.conll
    GINZA_JSON_PATH=$DATA_OUT_DIR/json_per_doc/$DOC_NAME.json
    
    ## Convert txt -> tsv (for ginza)
    python ent_tools/data_conversion/txt_to_tsv_for_auto_ner.py \
           -itxt $TXT_PATH \
           -tsv $TSV_PATH

    ## Run ginza and save as conll
    cut -f4 $TSV_PATH | ginza -d -m $MODEL_NAME > $GINZA_CNL_PATH
    echo "Save: $GINZA_CNL_PATH"

    ## Convert conll -> json
    python ent_tools/data_conversion/ginza_conll_to_json.py \
           -conll $GINZA_CNL_PATH \
           -json $GINZA_JSON_PATH \
           -tsv $TSV_PATH
done

## Merge json files into a single json file
python ent_tools/data_conversion/merge_jsons_into_single_json.py \
       -i $DATA_OUT_DIR/json_per_doc \
       -o $DATA_OUT_DIR/json/all.json
