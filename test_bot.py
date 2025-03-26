import logging
import asyncio
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext)
import config
import google_sheets
import nest_asyncio

# Configuração do log
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Permite rodar múltiplos loops de eventos no VS Code
nest_asyncio.apply()

# Estados da conversa
VALOR, DESCRICAO = range(2)

async def iniciar(update: Update, context: CallbackContext) -> None:
    """Responde com uma mensagem de boas-vindas."""
    await update.message.reply_text("Olá! Sou seu bot financeiro. Use /gasto para registrar um gasto.")

async def pedir_valor(update: Update, context: CallbackContext) -> int:
    """Inicia a conversa para adicionar um gasto."""
    await update.message.reply_text("Informe o valor do seu gasto.")
    return VALOR

async def receber_valor(update: Update, context: CallbackContext) -> int:
    """Recebe o valor do gasto e pede a descrição."""
    try:
        valor = update.message.text.replace(",", ".")  # Aceita valores com vírgula
        context.user_data['valor'] = float(valor)
        await update.message.reply_text("Agora, informe a descrição do gasto.")
        return DESCRICAO
    except ValueError:
        await update.message.reply_text("Valor inválido! Digite um número válido.")
        return VALOR

async def receber_descricao(update: Update, context: CallbackContext) -> int:
    """Recebe a descrição e finaliza o registro do gasto."""
    descricao = update.message.text
    valor = context.user_data['valor']
    
    google_sheets.registrar_gasto(valor, descricao)
    
    await update.message.reply_text(f"✅ Gasto registrado:\n💰 *R$ {valor:.2f}*\n📝 {descricao}", parse_mode="Markdown")
    return ConversationHandler.END

async def mostrar_relatorio(update: Update, context: CallbackContext) -> None:
    """Exibe o total de gastos."""
    try:
        total = google_sheets.obter_total_gastos()
        await update.message.reply_text(f"📊 *Relatório financeiro*\n\n💰 Total gasto até agora: *R$ {total:.2f}*", parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Erro ao obter relatório: {e}")
        await update.message.reply_text("❌ Ocorreu um erro ao buscar o relatório.")

async def cancelar(update: Update, context: CallbackContext) -> int:
    """Cancela a operação."""
    await update.message.reply_text("Operação cancelada.")
    return ConversationHandler.END

async def main():
    """Inicializa o bot com polling."""
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    # Criando o handler de conversa
    gasto_handler = ConversationHandler(
        entry_points=[CommandHandler("gasto", pedir_valor)],
        states={
            VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_valor)],
            DESCRICAO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_descricao)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )
    
    # Adiciona os handlers
    application.add_handler(CommandHandler("start", iniciar))
    application.add_handler(gasto_handler)
    application.add_handler(CommandHandler("relatorio", mostrar_relatorio))
    
    # Inicia o polling para o bot responder a comandos
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())  # Agora o loop pode rodar sem conflitos no VS Code
