# SPDX-License-Identifier: GPL-3.0-or-later
"""CLI do dumper: detect, dump, save-read, save-write, identify, search, info, ports, systems, errors, rom-write, flash-*.

Feita para pessoas e para agentes de IA: --json (saída e erros), código de saída estável, progresso em JSON lines,
nenhum prompt fora de um terminal. Referência: docs/cli.md.

Organização (um assunto por arquivo):
  errors.py      códigos de saída, CliError e a tradução de erro em saída
  common.py      conexão (porta ou simulador), sistema, base de dados
  output.py      saída em JSON ou texto, progresso, nome e gravação de arquivo
  md_chip.py     chip de flash do Mega Drive (usado por detect e rom-write)
  cmd_*.py       um arquivo por grupo de comandos
  parser.py      argumentos (argparse)
  app.py         ponto de entrada: `main`
"""
from . import common  # noqa: F401  (os testes trocam `common.connect` e `common.list_ports`)
from .app import main
from .errors import CLI_EXIT_CODES, CliError
from .parser import build_parser

__all__ = ["main", "build_parser", "CliError", "CLI_EXIT_CODES", "common"]
