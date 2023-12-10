#!/bin/bash

# Download UD_Japanese-BCCWJ (r2.8) from
# <https://github.com/UniversalDependencies/UD_Japanese-BCCWJ/archive/refs/tags/r2.8.tar.gz>
# and extract it to `data/original/UD_Japanese-BCCWJ/r2.8`.

# Obtain GSK2014-A <https://www.gsk.or.jp/catalog/gsk2014-a> and 
# extract it to `data/gsk-ene`.
# Generate XML files in `data/original/gsk-ene/bccwj/xml/` using the installation script.

mkdir -p ../data/processed/gsk-ene-bccwj/json/

python ent_tools/datasets/ene_bccwj/convert_xmls_to_json.py \
       -x ../data/original/gsk-ene/bccwj/xml \
       -j ../data/processed/gsk-ene-bccwj/json/bccwj-exPN-train.json \
       -i ../data/supplement/UD_Japanese-BCCWJ/UDJB_train_ids.txt \
       --exclude_domains PN

python ent_tools/datasets/ene_bccwj/convert_xmls_to_json.py \
       -x ../data/original/gsk-ene/bccwj/xml \
       -j ../data/processed/gsk-ene-bccwj/json/bccwj-exPN-dev.json \
       -i ../data/supplement/UD_Japanese-BCCWJ/UDJB_dev_ids.txt \
       --exclude_domains PN

python ent_tools/datasets/ene_bccwj/convert_xmls_to_json.py \
       -x ../data/original/gsk-ene/bccwj/xml \
       -j ../data/processed/gsk-ene-bccwj/json/bccwj-exPN-test.json \
       -i ../data/supplement/UD_Japanese-BCCWJ/UDJB_test_ids.txt \
       --exclude_domains PN
