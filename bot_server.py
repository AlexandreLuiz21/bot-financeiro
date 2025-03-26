from flask import Flask, request, jsonify
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from google_sheets import registrar_gasto_telegram
import os
from dotenv import load_dotenv
import logging
import asyncio
import sys

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)

# Desabilitar logs do httpx para evitar spam
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Estados da conversa
ESCOLHA_TIPO, VALOR, DESCRICAO, CATEGORIA, MENU_FINAL = range(5)

# Botões iniciais
BOTOES_INICIAIS = [
    ['💰 Registrar Receita'],
    ['💸 Registrar Despesa'],
    ['🚪 Sair']
]

# Botões do menu final
BOTOES_FINAIS = [
    ['📝 Nova Transação'],
    ['🚪 Finalizar']
]

# Categorias predefinidas para despesas
CATEGORIAS_DESPESAS = [
    ['🍽️ Alimentação', '🚗 Transporte'],
    ['💊 Saúde', '🏠 Moradia'],
    ['🎓 Educação', '🎭 Lazer'],
    ['👕 Vestuário', '💡 Utilidades'],
    ['💰 Outros']
]

# Categorias predefinidas para receitas
CATEGORIAS_RECEITAS = [
    ['💼 Salário'],
    ['💵 Renda Extra'],
    ['🎁 Outros Ganhos']
]

# Criar o aplicativo Flask
app = Flask(__name__)

# Criar o aplicativo Telegram sem updater para evitar polling
application = (
    Application.builder()
    .token(os.getenv('TELEGRAM_BOT_TOKEN'))
    .updater(None)  # Desabilita explicitamente o updater
    .arbitrary_callback_data(True)  # Permite dados de callback arbitrários
    .build()
)

# Configurar webhook
@app.route(f"/{os.getenv('TELEGRAM_BOT_TOKEN')}", methods=['POST'])
def webhook():
    """Endpoint para receber atualizações do Telegram."""
    try:
        if request.method == "POST":
            logger.info("Recebida atualização do Telegram")
            # Criar uma nova task para processar a atualização
            update = Update.de_json(request.get_json(), application.bot)
            asyncio.run(application.process_update(update))
            logger.info("Atualização processada com sucesso")
            return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"Erro no webhook: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

# Rota de healthcheck
@app.route('/')
def health():
    """Endpoint para healthcheck do Railway."""
    try:
        return jsonify({
            "status": "healthy",
            "message": "Bot está rodando!",
            "service": os.getenv("RAILWAY_SERVICE_NAME", "local"),
            "environment": os.getenv("RAILWAY_ENVIRONMENT_NAME", "development")
        })
    except Exception as e:
        logger.error(f"Erro no healthcheck: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

async def setup():
    """Configura o bot e seus handlers."""
    try:
        # Configurar handlers
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                ESCOLHA_TIPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, escolher_tipo)],
                VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, escolher_valor)],
                DESCRICAO: [MessageHandler(filters.TEXT & ~filters.COMMAND, descricao)],
                CATEGORIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, categoria)],
                MENU_FINAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_final)],
            },
            fallbacks=[CommandHandler('cancel', cancel)]
        )
        
        application.add_handler(conv_handler)
        logger.info("Handlers configurados com sucesso")
        
        # Configurar webhook
        webhook_url = f"https://{os.getenv('RAILWAY_STATIC_URL')}/{os.getenv('TELEGRAM_BOT_TOKEN')}"
        await application.bot.set_webhook(webhook_url)
        logger.info(f"Webhook configurado: {webhook_url}")
        
    except Exception as e:
        logger.error(f"Erro na configuração do bot: {str(e)}", exc_info=True)
        raise

def main():
    """Função principal para iniciar o bot e o servidor."""
    try:
        # Configurar o bot de forma assíncrona
        asyncio.run(setup())
        
        # Iniciar o servidor Flask
        port = int(os.getenv("PORT", 5000))
        logger.info('🤖 Bot iniciado!')
        logger.info(f'Port: {port}')
        
        # Usar Gunicorn para produção (configurado no railway.toml)
        if os.getenv("RAILWAY_ENVIRONMENT_NAME"):
            app.run(host="0.0.0.0", port=port)
        else:
            # Para desenvolvimento local
            app.run(host="0.0.0.0", port=port, debug=True)
        
    except Exception as e:
        logger.error(f"Erro ao iniciar o bot: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    main() 