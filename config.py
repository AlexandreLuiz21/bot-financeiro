import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_SHEETS_CREDENTIALS = "bot-financeiro-454714-8a6fe14bfdfc.json"
SHEET_NAME = "1jLDVo94XDgPbk6eO7vhgjTw62f5EkNO-MrQp7ppZjD0"  # ID da planilha
DESPESAS_SHEET_NAME = "Despesas"  # Nome da aba de despesas
RECEITAS_SHEET_NAME = "Receitas"  # Nome da aba de receitas
RESUMO_SHEET_NAME = "Resumo Mensal"  # Nome da aba de resumo
