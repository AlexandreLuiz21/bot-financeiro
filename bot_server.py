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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia o bot e mostra os botões principais."""
    if update.message is None:
        return ESCOLHA_TIPO
    
    reply_markup = ReplyKeyboardMarkup(BOTOES_INICIAIS, resize_keyboard=True)
    await update.message.reply_text(
        'Olá! 👋 Vou ajudar você a registrar suas finanças.\n\n'
        'Escolha uma opção:',
        reply_markup=reply_markup
    )
    return ESCOLHA_TIPO

async def escolher_tipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a escolha do tipo de registro (receita ou despesa)."""
    escolha = update.message.text
    
    if escolha == '💰 Registrar Receita':
        context.user_data['tipo'] = 'receita'
        await update.message.reply_text(
            '💰 Por favor, digite o valor da receita:\n'
            'Exemplo: 3000.00'
        )
    elif escolha == '💸 Registrar Despesa':
        context.user_data['tipo'] = 'despesa'
        await update.message.reply_text(
            '💸 Por favor, digite o valor da despesa:\n'
            'Exemplo: 50.90'
        )
    elif escolha == '🚪 Sair':
        await update.message.reply_text(
            '👋 Obrigado por usar o bot! Para começar novamente, use o comando /start',
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    else:
        reply_markup = ReplyKeyboardMarkup(BOTOES_INICIAIS, resize_keyboard=True)
        await update.message.reply_text(
            '❌ Opção inválida! Por favor, escolha uma das opções:',
            reply_markup=reply_markup
        )
        return ESCOLHA_TIPO
    
    return VALOR

async def escolher_valor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa o valor digitado pelo usuário."""
    try:
        # Remove espaços e troca vírgula por ponto
        valor_str = update.message.text.strip().replace(',', '.')
        
        # Tenta converter para float
        valor = float(valor_str)
        
        if valor <= 0:
            await update.message.reply_text(
                '❌ O valor deve ser maior que zero!',
                reply_markup=ReplyKeyboardRemove()
            )
            return VALOR
        
        # Armazena o valor no contexto
        context.user_data['valor'] = valor
        
        # Solicita a descrição
        await update.message.reply_text(
            '📝 Agora, digite uma descrição para esta transação:',
            reply_markup=ReplyKeyboardRemove()
        )
        
        return DESCRICAO
    except ValueError:
        await update.message.reply_text(
            '❌ Por favor, digite um valor numérico válido!',
            reply_markup=ReplyKeyboardRemove()
        )
        return VALOR

async def descricao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a descrição e solicita a categoria."""
    context.user_data['descricao'] = update.message.text
    
    # Mostra as categorias baseado no tipo escolhido
    if context.user_data['tipo'] == 'despesa':
        reply_markup = ReplyKeyboardMarkup(CATEGORIAS_DESPESAS, resize_keyboard=True)
        await update.message.reply_text(
            'Escolha a categoria da despesa:',
            reply_markup=reply_markup
        )
    else:
        reply_markup = ReplyKeyboardMarkup(CATEGORIAS_RECEITAS, resize_keyboard=True)
        await update.message.reply_text(
            'Escolha a categoria da receita:',
            reply_markup=reply_markup
        )
    
    return CATEGORIA

async def categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finaliza o registro e mostra o menu final."""
    categoria_texto = update.message.text
    # Remove emojis e espaços extras
    for emoji in ['🍽️ ', '🚗 ', '💊 ', '🏠 ', '🎓 ', '🎭 ', '👕 ', '💡 ', '💰 ', '💼 ', '💵 ', '🎁 ']:
        categoria_texto = categoria_texto.replace(emoji, '')
    
    context.user_data['categoria'] = categoria_texto
    
    # Registrar no Google Sheets
    try:
        registrar_gasto_telegram(
            context.user_data['valor'],
            context.user_data['descricao'],
            context.user_data['categoria'],
            context.user_data.get('tipo', 'despesa')  # Passa o tipo (receita ou despesa)
        )
        
        tipo = '💰 Receita' if context.user_data.get('tipo') == 'receita' else '💸 Despesa'
        
        # Mostrar mensagem de sucesso e menu final
        reply_markup = ReplyKeyboardMarkup(BOTOES_FINAIS, resize_keyboard=True)
        await update.message.reply_text(
            f'✅ {tipo} registrada com sucesso!\n\n'
            f'💰 Valor: R$ {context.user_data["valor"]:.2f}\n'
            f'📝 Descrição: {context.user_data["descricao"]}\n'
            f'📂 Categoria: {context.user_data["categoria"]}\n\n'
            'O que deseja fazer agora?',
            reply_markup=reply_markup
        )
    except Exception as e:
        reply_markup = ReplyKeyboardMarkup(BOTOES_FINAIS, resize_keyboard=True)
        await update.message.reply_text(
            f'❌ Erro ao registrar: {str(e)}\n\n'
            'O que deseja fazer agora?',
            reply_markup=reply_markup
        )
    
    context.user_data.clear()
    return MENU_FINAL

async def menu_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a escolha do menu final."""
    escolha = update.message.text
    
    if escolha == '📝 Nova Transação':
        reply_markup = ReplyKeyboardMarkup(BOTOES_INICIAIS, resize_keyboard=True)
        await update.message.reply_text(
            'Escolha uma opção:',
            reply_markup=reply_markup
        )
        return ESCOLHA_TIPO
    elif escolha == '🚪 Finalizar':
        await update.message.reply_text(
            '👋 Obrigado por usar o bot! Para começar novamente, use o comando /start',
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    else:
        reply_markup = ReplyKeyboardMarkup(BOTOES_FINAIS, resize_keyboard=True)
        await update.message.reply_text(
            '❌ Opção inválida! Por favor, escolha uma das opções:',
            reply_markup=reply_markup
        )
        return MENU_FINAL

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela a operação atual."""
    await update.message.reply_text(
        '❌ Operação cancelada! Para começar novamente, use o comando /start',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

if __name__ == '__main__':
    main() 