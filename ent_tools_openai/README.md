# ent_tools_openai

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
    pip uninstall ent_tools_openai
    ~~~~

## Usage Examples

1. Named entity recognition  (NER) using OpenAI's GPT models
    - Throw query designed for NER using OpenAI API <https://platform.openai.com/docs/overview> and save results.
        - Edit and run `bin/examples/openai_throw_query.sh`.

### Notes

Neet to activate the virtual environment if ent_tools is installed via poetry, for example:
~~~~
poetry shell
(run some bash script)
exit
~~~~
