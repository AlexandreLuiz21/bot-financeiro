# Bot Financeiro - Documentação

## Estrutura do Projeto

### Arquivos Principais
- `telegram_bot.py`: Código principal do bot do Telegram
- `google_sheets.py`: Integração com Google Sheets
- `config.py`: Configurações e variáveis do projeto
- `.env`: Variáveis de ambiente (tokens e credenciais)
- `requirements.txt`: Dependências do projeto
- `bot-financeiro-454714-8a6fe14bfdfc.json`: Credenciais do Google Sheets

### Planilha Google Sheets
A planilha está organizada em três abas:

1. **Aba "Receitas"**
   - Registra todas as entradas de dinheiro
   - Colunas: Data | Categoria | Descrição | Valor

2. **Aba "Despesas"**
   - Registra todos os gastos
   - Colunas: Data | Categoria | Descrição | Valor

3. **Aba "Resumo Mensal"**
   - Mostra o resumo financeiro mensal
   - Colunas: Mês/Ano | Total Receitas | Total Despesas | Saldo

## Fluxo de Funcionamento

### 1. Iniciar o Bot
- Comando: `/start`
- Mostra menu inicial com opções:
  - 💰 Registrar Receita
  - 💸 Registrar Despesa
  - 🚪 Sair

### 2. Registrar Receita
1. Usuário seleciona "💰 Registrar Receita"
2. Bot solicita o valor
3. Bot solicita a descrição
4. Bot mostra categorias disponíveis:
   - 💼 Salário
   - 💵 Renda Extra
   - 🎁 Outros Ganhos
5. Sistema:
   - Salva na aba "Receitas"
   - Soma todas as receitas do mês
   - Atualiza o "Total Receitas" no Resumo Mensal
   - Recalcula o saldo

### 3. Registrar Despesa
1. Usuário seleciona "💸 Registrar Despesa"
2. Bot solicita o valor
3. Bot solicita a descrição
4. Bot mostra categorias disponíveis:
   - 🍽️ Alimentação
   - 🚗 Transporte
   - 💊 Saúde
   - 🏠 Moradia
   - 🎓 Educação
   - 🎭 Lazer
   - 👕 Vestuário
   - 💡 Utilidades
   - 💰 Outros
5. Sistema:
   - Salva na aba "Despesas"
   - Soma todas as despesas do mês
   - Atualiza o "Total Despesas" no Resumo Mensal
   - Recalcula o saldo

### 4. Menu Final
Após cada transação, mostra opções:
- 📝 Nova Transação: volta ao menu inicial
- 🚪 Finalizar: encerra a conversa

## Cálculos Automáticos

### Resumo Mensal
- **Total Receitas**: Soma de todas as receitas do mês
- **Total Despesas**: Soma de todas as despesas do mês
- **Saldo**: Total Receitas - Total Despesas

## Comandos Disponíveis
- `/start`: Inicia o bot
- `/cancel`: Cancela a operação atual

## Como Executar o Bot
1. Configurar as variáveis de ambiente no arquivo `.env`
2. Instalar as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Executar o bot:
   ```
   python telegram_bot.py
   ```

## Observações Importantes
- O bot organiza os dados por mês automaticamente
- Os totais são atualizados em tempo real
- Todas as transações são registradas com data e hora
- Os valores são formatados automaticamente em reais (R$) 