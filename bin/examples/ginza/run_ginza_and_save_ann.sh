#!/bin/bash

# Set model name. e.g., ja_ginza, ja_ginza_electra, ja_ginza_bert_large
MODEL_NAME="ja_ginza_electra"

DATA_IN_DIR=data/original/sample_ja_ner
DATA_OUT_DIR=data/processed/sample_ja_ner
mkdir -p $DATA_OUT_DIR/brat
mkdir -p $DATA_OUT_DIR/tsv_for_ner
mkdir -p $DATA_OUT_DIR/ginza/conll_per_doc

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
    GINZA_CNL_PATH=$DATA_OUT_DIR/ginza/conll_per_doc/$DOC_NAME.conll
    ANN_PATH=$DATA_OUT_DIR/brat/$DOC_NAME.ann
    
    ## Convert txt -> tsv (for ginza)
    poetry run python ent_tools/data_conversion/txt_to_tsv_for_auto_ner.py \
           -itxt $TXT_PATH \
           -tsv $TSV_PATH

    ## Run ginza and save as conll
    # cut -f4 $TSV_PATH | ginza -d -m $MODEL_NAME > $GINZA_CNL_PATH
    # echo "Save: $GINZA_CNL_PATH"

    ## Convert conll -> ann (for brat)
    poetry run python ent_tools/data_conversion/ginza_conll_to_ann.py \
           -conll $GINZA_CNL_PATH \
           -ann $ANN_PATH \
           -tsv $TSV_PATH \
           -label data/supplement/label_map/labelmap_ene-v7.1.0_to_loc-fac-org-name.json
done
