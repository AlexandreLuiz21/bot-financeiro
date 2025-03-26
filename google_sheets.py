import gspread
from oauth2client.service_account import ServiceAccountCredentials
import config
from datetime import datetime

def conectar_google_sheets():
    """Estabelece a conexão com o Google Sheets usando a API e retorna o cliente."""
    try:
        print("🔄 Tentando conectar ao Google Sheets...")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        print(f"📁 Usando arquivo de credenciais: {config.GOOGLE_SHEETS_CREDENTIALS}")
        creds = ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_SHEETS_CREDENTIALS, scope)
        client = gspread.authorize(creds)
        print("✅ Conexão com Google Sheets estabelecida com sucesso!")
        return client
    except Exception as e:
        print(f"❌ Erro ao conectar ao Google Sheets: {str(e)}")
        return None

def obter_planilha(nome_aba):
    """Obtém uma aba específica da planilha."""
    try:
        print(f"🔄 Tentando obter a aba '{nome_aba}'...")
        client = conectar_google_sheets()
        if client is None:
            return None
        
        print(f"📊 Tentando abrir planilha com ID: {config.SHEET_NAME}")
        spreadsheet = client.open_by_key(config.SHEET_NAME)
        try:
            worksheet = spreadsheet.worksheet(nome_aba)
            print(f"✅ Aba '{nome_aba}' obtida com sucesso!")
            return worksheet
        except gspread.exceptions.WorksheetNotFound:
            print(f"❌ Aba '{nome_aba}' não encontrada!")
            return None
    except Exception as e:
        print(f"❌ Erro ao obter planilha: {str(e)}")
        return None

def registrar_gasto():
    """Solicita os dados do usuário e registra um gasto na planilha."""
    sheet = obter_planilha(config.TRANSACOES_SHEET_NAME)
    if sheet is None:
        return
    
    data_atual = datetime.now().strftime("%d/%m/%Y")
    
    valor = input("Digite o valor do gasto: ").strip()
    try:
        valor = float(valor.replace(",", "."))
    except ValueError:
        print("❌ Erro: O valor deve ser numérico!")
        return
    
    descricao = input("Digite a descrição do gasto: ").strip()
    categoria = input("Digite a categoria (Ex: Alimentação, Transporte, Saúde, etc.): ").strip()

    if not descricao or not categoria:
        print("❌ Erro: Todos os campos devem ser preenchidos!")
        return
    
    try:
        sheet.append_row([data_atual, descricao, -abs(valor), categoria])
        print("\n✅ Gasto registrado com sucesso!")
        print(f"📝 Data: {data_atual}\n💰 Valor: R$ {valor:.2f}\n📌 Descrição: {descricao}\n📂 Categoria: {categoria}")
        atualizar_resumo_mensal()
    except Exception as e:
        print(f"❌ Erro ao registrar gasto: {e}")

def obter_total_gastos():
    """Calcula o total de gastos na planilha."""
    sheet = obter_planilha(config.TRANSACOES_SHEET_NAME)
    if sheet is None:
        return 0
    
    try:
        data = sheet.get_all_values()
        total = sum(float(row[2]) for row in data[1:] if len(row) > 2 and row[2].replace('.', '', 1).isdigit())
        print(f"\n💸 Total de gastos registrados: R$ {abs(total):.2f}")
        return abs(total)
    except Exception as e:
        print(f"❌ Erro ao calcular total de gastos: {e}")
        return 0

def atualizar_resumo_mensal():
    """Atualiza automaticamente o resumo mensal na aba 'Resumo Mensal'."""
    transacoes_sheet = obter_planilha(config.TRANSACOES_SHEET_NAME)
    resumo_sheet = obter_planilha(config.RESUMO_SHEET_NAME)
    
    if transacoes_sheet is None or resumo_sheet is None:
        return
    
    try:
        # Obter dados da planilha de transações
        data = transacoes_sheet.get_all_values()[1:]  # Pula o cabeçalho
        resumo = {}
        
        for row in data:
            if len(row) < 4:
                continue
            
            data_gasto, _, valor, categoria = row
            try:
                valor = float(valor)
            except ValueError:
                continue
            
            mes_ano = "/".join(data_gasto.split("/")[1:])  # Formato: MM/YYYY
            if mes_ano not in resumo:
                resumo[mes_ano] = {"receitas": 0, "despesas": 0}
            
            # Se o valor for positivo é receita, se for negativo é despesa
            if valor > 0:
                resumo[mes_ano]["receitas"] += valor
            else:
                resumo[mes_ano]["despesas"] += abs(valor)  # Usa valor absoluto para despesas
        
        # Limpar conteúdo existente mantendo o cabeçalho
        if resumo_sheet.row_count > 1:
            resumo_sheet.delete_rows(2, resumo_sheet.row_count)
        
        # Ordenar os meses em ordem cronológica reversa (mais recente primeiro)
        meses_ordenados = sorted(resumo.keys(), key=lambda x: [int(i) for i in x.split("/")[::-1]], reverse=True)
        
        # Adicionar dados ordenados
        for mes in meses_ordenados:
            valores = resumo[mes]
            saldo = valores["receitas"] - valores["despesas"]
            resumo_sheet.append_row([
                mes,
                valores["receitas"],
                valores["despesas"],
                saldo
            ])
        
        # Formatar células
        if len(meses_ordenados) > 0:
            ultima_linha = len(meses_ordenados) + 1
            # Formatar números como moeda
            resumo_sheet.format(f'B2:D{ultima_linha}', {
                "numberFormat": {
                    "type": "CURRENCY",
                    "pattern": "R$#,##0.00"
                }
            })
        
        print("\n📊 Resumo mensal atualizado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao atualizar resumo mensal: {e}")

def registrar_gasto_telegram(valor, descricao, categoria, tipo='despesa'):
    """Registra um gasto na planilha a partir de uma mensagem do Telegram."""
    try:
        print(f"🔄 Tentando registrar {tipo} no Google Sheets...")
        print(f"💰 Valor: {valor}")
        print(f"📝 Descrição: {descricao}")
        print(f"📂 Categoria: {categoria}")
        
        # Conectar ao Google Sheets
        client = conectar_google_sheets()
        if client is None:
            raise Exception("Não foi possível conectar ao Google Sheets")
        
        # Abrir a planilha correta baseado no tipo
        sheet_name = config.RECEITAS_SHEET_NAME if tipo == 'receita' else config.DESPESAS_SHEET_NAME
        sheet = obter_planilha(sheet_name)
        if sheet is None:
            raise Exception(f"Não foi possível acessar a aba '{sheet_name}'")
        
        # Formatar o valor (positivo para receitas, negativo para despesas)
        valor_formatado = abs(valor) if tipo == 'receita' else -abs(valor)
        
        # Obter a data atual
        data_atual = datetime.now().strftime("%d/%m/%Y")
        
        # Registrar na planilha
        print(f"📊 Registrando na planilha: {sheet_name}")
        sheet.append_row([data_atual, descricao, valor_formatado, categoria])
        
        print("✅ Registro concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao registrar {tipo}: {str(e)}")
        raise

def atualizar_resumo_mensal(valor, categoria, tipo):
    """Atualiza o resumo mensal com a nova transação."""
    try:
        sheet = obter_planilha(config.RESUMO_SHEET_NAME)
        if sheet is None:
            return False
        
        # Obtém o mês e ano atual
        data_atual = datetime.now()
        mes_ano = data_atual.strftime("%m/%Y")
        
        # Procura a linha do mês atual
        celula = sheet.find(mes_ano)
        if celula is None:
            # Se não encontrar, cria uma nova linha
            linha = [mes_ano, 0, 0, 0]  # [Mês/Ano, Total Receitas, Total Despesas, Saldo]
            sheet.append_row(linha)
            celula = sheet.find(mes_ano)
        
        linha = celula.row
        
        # Função auxiliar para converter valor formatado em moeda para float
        def converter_valor(valor_str):
            if isinstance(valor_str, (int, float)):
                return float(valor_str)
            # Remove R$, espaços e troca vírgula por ponto
            valor_str = str(valor_str).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
            try:
                return float(valor_str)
            except ValueError:
                return 0.0

        # Função para somar valores do mês atual
        def somar_valores_do_mes(sheet_name):
            try:
                aba = obter_planilha(sheet_name)
                if aba is None:
                    return 0
                
                # Pega todos os valores
                valores = aba.get_all_values()
                if len(valores) <= 1:  # Se só tem cabeçalho ou está vazia
                    return 0
                
                total = 0
                mes_atual = data_atual.strftime("%m/%Y")
                
                # Soma apenas os valores do mês atual
                for linha in valores[1:]:  # Pula o cabeçalho
                    try:
                        data_linha = datetime.strptime(linha[0], "%d/%m/%Y")
                        if data_linha.strftime("%m/%Y") == mes_atual:
                            valor_linha = converter_valor(linha[3])  # Coluna do valor
                            total += valor_linha
                    except (ValueError, IndexError):
                        continue
                
                return total
            except Exception as e:
                print(f"Erro ao somar valores: {str(e)}")
                return 0
        
        # Atualiza os totais
        if tipo == 'receita':
            total_receitas = somar_valores_do_mes(config.RECEITAS_SHEET_NAME)
            sheet.update_cell(linha, 2, total_receitas)
        elif tipo == 'despesa':
            total_despesas = somar_valores_do_mes(config.DESPESAS_SHEET_NAME)
            sheet.update_cell(linha, 3, total_despesas)
        
        # Atualiza o saldo (Receitas - Despesas)
        total_receitas = converter_valor(sheet.cell(linha, 2).value)
        total_despesas = converter_valor(sheet.cell(linha, 3).value)
        saldo = total_receitas - total_despesas
        sheet.update_cell(linha, 4, saldo)
        
        # Formata as células como moeda
        sheet.format(f'B{linha}:D{linha}', {
            "numberFormat": {
                "type": "CURRENCY",
                "pattern": "R$#,##0.00"
            }
        })
        
        return True
    except Exception as e:
        print(f"❌ Erro ao atualizar resumo mensal: {str(e)}")
        return False