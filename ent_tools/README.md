# ent_tools

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
    pip uninstall ent_tools
    ~~~~

## Usage Examples

1. brat
    - Convert the output file format of the annotation tool brat <https://github.com/nlplab/brat>.
        - Edit and run `bin/examples/brat/convert_brat_files_to_json.sh`.

1. ginza
    - Convert the output file format of the GiNZA NLP Library <https://github.com/megagonlabs/ginza>.
        - Edit and run `bin/examples/ginza/*.sh`

1. evaluation
    - Evaluate system accuracy for mention recognition (named entity recognition).
        - Edit and run `bin/examples/evaluate/evaluate_mention_recognition.sh`.

### Notes

Neet to activate the virtual environment if ent_tools is installed via poetry, for example:
~~~~
poetry shell
(run some bash script)
exit
~~~~
