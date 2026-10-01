@echo off
rem Abre a EULER no navegador (Windows): dois cliques neste arquivo.
rem Instalacao, uma vez so, nesta pasta:
rem   python -m venv .venv
rem   .venv\Scripts\python -m pip install -e ".[dev]"
rem Para fechar a EULER, feche esta janela.
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m streamlit run app\main.py
) else (
  echo Ambiente .venv nao encontrado nesta pasta: tentando o Python do computador.
  echo Se der erro, veja a secao Comecar do README.md.
  python -m streamlit run app\main.py
)
pause
