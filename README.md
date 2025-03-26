# Bot Financeiro Telegram

Bot para Telegram que ajuda no controle financeiro pessoal, integrando com Google Sheets para registro de receitas e despesas.

## Funcionalidades

- ✅ Registro de receitas
- ✅ Registro de despesas
- ✅ Categorização automática
- ✅ Resumo mensal automático
- ✅ Interface amigável com botões
- ✅ Integração com Google Sheets

## Requisitos

- Python 3.7+
- Conta no Telegram
- Conta no Google Cloud (para API do Google Sheets)

## Configuração

1. Clone o repositório
```bash
git clone [URL_DO_SEU_REPOSITORIO]
cd bot-financeiro
```

2. Instale as dependências
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente no arquivo `.env`:
```
TELEGRAM_BOT_TOKEN=seu_token_aqui
GOOGLE_SHEETS_CREDENTIALS=caminho_do_arquivo_json
PLANILHA_TRANSACOES=nome_da_sua_planilha
```

4. Configure as credenciais do Google Sheets:
- Crie um projeto no Google Cloud Console
- Ative a API do Google Sheets
- Crie uma conta de serviço e baixe o arquivo JSON de credenciais
- Compartilhe sua planilha com o email da conta de serviço

## Como Usar

1. Inicie o bot:
```bash
python telegram_bot.py
```

2. No Telegram:
- Procure pelo seu bot
- Inicie com o comando `/start`
- Siga as instruções na tela

## Estrutura do Projeto

Para mais detalhes sobre a estrutura e funcionamento do projeto, consulte o arquivo [DOCUMENTACAO.md](DOCUMENTACAO.md).

## Contribuindo

Sinta-se à vontade para contribuir com o projeto através de issues e pull requests. 