import json


def create_jupyter_notebook(code_cells: list, text_cells: list) -> str:
    """Cria o conteúdo de um arquivo .ipynb a partir de listas de células de código e texto."""

    notebook = {
        "cells": [],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.9.0"  # Exemplo
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }

    # Intercala células de texto e código
    max_len = max(len(code_cells), len(text_cells))
    for i in range(max_len):
        if i < len(text_cells):
            notebook["cells"].append({
                "cell_type": "markdown",
                "metadata": {},
                "source": [text_cells[i]]
            })
        if i < len(code_cells):
            notebook["cells"].append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [code_cells[i]]
            })

    return json.dumps(notebook, indent=2)