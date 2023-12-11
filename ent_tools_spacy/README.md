# ent_tools_spacy

The package dependencies assuming the use of spacy 3.4.4 with ja_ginza_electra (ginza 5.1.3 and ja-ginza-electra 5.1.3) are described in `pyproject.toml`:
~~~~
[tool.poetry.dependencies]
python = "^3.10"
ent-tools = {path = "../ent_tools"}
spacy = "3.4.4"
ginza = "5.1.3"
ja-ginza-electra = "5.1.3"
~~~~

If using other spacy-based models, it will be necessary to change the library versions in `pyproject.toml`.

## Installation

There are several installation options available, as shown below. Note that it is assumed you are in this directory.

1. Using poetry

    ~~~~
    poetry install
    ~~~~

1. Using venv
    ~~~~
    python -m venv venv
    source venv/bin/activate
    pip install .
    deactivate                  # When exiting the virtual environment.
    ~~~~

1. Direct installation in the current environment
    ~~~~
    pip install .
    ~~~~

## Uninstallation

Assuming you are in this directory.

1. Using poetry

    ~~~~
    rm -rf .venv
    rm -f poetry.lock
    ~~~~

1. Using venv
    ~~~~
    pip uninstall venv
    rm -rf venv
    ~~~~

1. Direct installation in the current environment
    ~~~~
    pip uninstall ent_tools_spacy
    ~~~~

## Usage Examples

1. Convert gold standard data to spacy's DocBin
    1. Create JSON-style input data, for example:
        - Edit and run `../ent_tools/bin/examples/brat/convert_brat_files_to_json.sh`
        - Edit and run `../ent_tools/bin/examples/ginza/run_ginza_and_save_json.sh `
    1. Convert JSON to spacy's DocBin
        - Edit and run `bin/examples/spacy_build_data.sh`.

1. Decode data using existing (or your own trained) model
    - Edit and run `bin/examples/spacy_decode.sh`.

1. Evaluate model accuracy
    - Edit and run `../ent_tools/bin/examples/evaluate/evaluate_mention_recognition.sh`
    - I don't recommend to use `bin/examples/spacy_evaluate.sh`. Calculated scores would be inaccurate because spans in original gold standard data are ignored when model's tokenization results don't match those spans.

### Notes

Neet to activate the virtual environment if ent_tools is installed via poetry, for example:
~~~~
poetry shell
(run some bash script)
exit
~~~~
