import datetime
import csv
import requests
import json
import base64
import os
from io import StringIO

# Inicialização das variáveis de plantio
plantacao1 = []  # Para armazenar plantios de milho
plantacao2 = []  # Para armazenar plantios de trigo
historico_insumos = []

# Configurações do GitHub
GITHUB_USERNAME = "Fabiostrike"
GITHUB_REPO = "agrodata"

# ou alterar essa linha para incluir seu token diretamente (não recomendado para código compartilhado)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "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")  # Obtenha seu token em: https://github.com/settings/tokens

def nome_mes_para_numero(nome_mes):
    meses = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
        'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
        'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
    }
    return meses.get(nome_mes.lower(), 0)

def obter_estacao(data):
    mes = data.month
    if mes in [12, 1, 2]:
        return 'Verão'
    elif mes in [3, 4, 5]:
        return 'Outono'
    elif mes in [6, 7, 8]:
        return 'Inverno'
    else:
        return 'Primavera'

def ler_csv(url):
    response = requests.get(url)
    if response.status_code == 200:
        csv_data = response.text
        csv_reader = csv.DictReader(StringIO(csv_data))
        return list(csv_reader)
    else:
        print(f"Erro ao acessar o arquivo CSV: {response.status_code}")
        return []

def ler_recomendacoes_csv():
    url = 'https://raw.githubusercontent.com/Fabiostrike/agrodata/main/recomendacoes_mensais.csv'
    return ler_csv(url)

def carregar_dados_salvos():
    global plantacao1, plantacao2, historico_insumos
    
    # Carregar plantios existentes
    try:
        url_plantios = 'https://raw.githubusercontent.com/Fabiostrike/agrodata/main/plantios_existentes.csv'
        dados_plantios = ler_csv(url_plantios)
        
        if dados_plantios:
            plantacao1 = []
            plantacao2 = []
            for plantio in dados_plantios:
                if plantio['tipo_cultura'] == 'milho':
                    plantacao1.append({"area": float(plantio['area'])})
                elif plantio['tipo_cultura'] == 'trigo':
                    plantacao2.append({"area": float(plantio['area'])})
            print("Dados de plantios carregados com sucesso.")
    except Exception as e:
        print(f"Erro ao carregar plantios: {e}")
    
    # Carregar histórico de insumos
    try:
        url_historico = 'https://raw.githubusercontent.com/Fabiostrike/agrodata/main/historico_aplicacao_insumos.csv'
        dados_historico = ler_csv(url_historico)
        
        if dados_historico:
            historico_insumos = []
            for registro in dados_historico:
                historico_insumos.append({
                    "data": datetime.datetime.strptime(registro['data'], '%Y-%m-%d').date(),
                    "estacao": registro['estacao'],
                    "cultura": registro['cultura'],
                    "area": float(registro['area']),
                    "inseticida": float(registro['inseticida']),
                    "bactericida": float(registro['bactericida']),
                    "fungicida": float(registro['fungicida']),
                    "npk": float(registro['npk']),
                    "agua": float(registro['agua'])
                })
            print("Histórico de insumos carregado com sucesso.")
    except Exception as e:
        print(f"Erro ao carregar histórico de insumos: {e}")

def salvar_no_github(conteudo, caminho_arquivo, mensagem_commit):
    """Salva um arquivo no GitHub usando a API REST"""
    if not GITHUB_TOKEN:
        print("Token do GitHub não configurado. Configure a variável de ambiente GITHUB_TOKEN.")
        return False
    
    # Verificar se o arquivo já existe
    url_api = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{caminho_arquivo}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Obter SHA do arquivo atual (se existir)
    response = requests.get(url_api, headers=headers)
    
    conteudo_base64 = base64.b64encode(conteudo.encode("utf-8")).decode("utf-8")
    
    dados = {
        "message": mensagem_commit,
        "content": conteudo_base64,
    }
    
    # Adicionar SHA se o arquivo já existir
    if response.status_code == 200:
        dados["sha"] = response.json()["sha"]
    
    # Enviar requisição para criar/atualizar o arquivo
    response = requests.put(url_api, headers=headers, data=json.dumps(dados))
    
    if response.status_code in [200, 201]:
        print(f"Arquivo {caminho_arquivo} salvo com sucesso!")
        return True
    else:
        print(f"Erro ao salvar arquivo: {response.status_code}")
        print(response.text)
        return False

def salvar_alteracoes():
    """Salva plantios e histórico de insumos nos arquivos do GitHub"""
    # Preparar CSV de plantios
    output_plantios = StringIO()
    writer_plantios = csv.writer(output_plantios)
    writer_plantios.writerow(['tipo_cultura', 'area'])
    
    for p in plantacao1:
        writer_plantios.writerow(['milho', p['area']])
    
    for p in plantacao2:
        writer_plantios.writerow(['trigo', p['area']])
    
    # Preparar CSV de histórico de insumos
    output_historico = StringIO()
    writer_historico = csv.writer(output_historico)
    writer_historico.writerow(['data', 'estacao', 'cultura', 'area', 'inseticida', 'bactericida', 'fungicida', 'npk', 'agua'])
    
    for h in historico_insumos:
        writer_historico.writerow([
            h['data'].strftime('%Y-%m-%d'),
            h['estacao'],
            h['cultura'],
            h['area'],
            h['inseticida'],
            h['bactericida'],
            h['fungicida'],
            h['npk'],
            h['agua']
        ])
    
    # Salvar no GitHub
    sucesso_plantios = salvar_no_github(
        output_plantios.getvalue(), 
        "plantios_existentes.csv", 
        f"Atualização de plantios em {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    sucesso_historico = salvar_no_github(
        output_historico.getvalue(), 
        "historico_aplicacao_insumos.csv", 
        f"Atualização de histórico de insumos em {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    return sucesso_plantios and sucesso_historico

def menu_principal():
    print("\n===== SISTEMA DE GERENCIAMENTO DE PLANTAÇÕES =====")
    print("1 - Adicionar um plantio (máximo 5)")
    print("2 - Calcular insumos agrícolas necessários")
    print("3 - Exibir plantios adicionados")
    print("4 - Alterar plantio")
    print("5 - Deletar plantio")
    print("6 - Aplicar insumos")
    print("7 - Verificar histórico de insumos aplicados")
    print("8 - Salvar alterações no GitHub")
    print("9 - Sair do programa")
    return int(input("Escolha uma opção: "))

def adicionar_plantio():
    print("\n===== ADICIONAR PLANTIO =====")
    print("1 - Milho")
    print("2 - Trigo")
    pd = int(input("Escolha a cultura (1-Milho, 2-Trigo): "))
    area = float(input("Digite a área do plantio (m²): "))
    if pd == 1:
        if len(plantacao1) >= 5:
            print("Limite máximo de 5 plantios de milho!")
        else:
            plantacao1.append({"area": area})
            print("Plantio de milho adicionado!")
    elif pd == 2:
        if len(plantacao2) >= 5:
            print("Limite máximo de 5 plantios de trigo!")
        else:
            plantacao2.append({"area": area})
            print("Plantio de trigo adicionado!")
    else:
        print("Opção inválida!")

def escolher_plantio(lista, cultura):
    if not lista:
        print(f"Não há plantios de {cultura} registrados!")
        return None
    for i, p in enumerate(lista):
        print(f"{i + 1} - {p['area']} m²")
    idx = int(input(f"Escolha o plantio de {cultura} (número): ")) - 1
    if 0 <= idx < len(lista):
        return lista[idx]
    else:
        print("Índice inválido!")
        return None

def calcular_insumos():
    print("\n===== CÁLCULO DE INSUMOS =====")
    print("1 - Milho")
    print("2 - Trigo")
    pd = int(input("Escolha a cultura (1-Milho, 2-Trigo): "))

    dados_csv = ler_recomendacoes_csv()
    if not dados_csv:
        return

    hoje = datetime.date.today()
    estacao = obter_estacao(hoje)
    
    # Filtrar os dados para o mês atual
    dados_mes_atual = [linha for linha in dados_csv if nome_mes_para_numero(linha['mes']) == hoje.month]
    
    if not dados_mes_atual:
        print("Sem dados para o mês atual.")
        return
        
    # Pegar valores específicos do mês atual
    ph_mes_atual = float(dados_mes_atual[0]['ph_medio_solo'])
    umidade_mes_atual = float(dados_mes_atual[0]['umidade_media_solo'])
    
    # Continuar com o cálculo baseado na estação
    dados_estacao = [linha for linha in dados_csv if linha['estacao'] == estacao]

    if not dados_estacao:
        print("Sem dados para a estação atual.")
        return

    # Calcular médias sazonais
    umidade = sum(float(l['umidade_media_solo']) for l in dados_estacao) / len(dados_estacao)
    ph = sum(float(l['ph_medio_solo']) for l in dados_estacao) / len(dados_estacao)
    fosforo = sum(float(l['fosforo_P']) for l in dados_estacao) / len(dados_estacao)
    potassio = sum(float(l['potassio_K']) for l in dados_estacao) / len(dados_estacao)
    irrigacao = sum(float(l['agua_irrigacao']) for l in dados_estacao) / len(dados_estacao)

    plantio = None
    cultura = ""
    if pd == 1:
        plantio = escolher_plantio(plantacao1, "milho")
        cultura = "milho"
    elif pd == 2:
        plantio = escolher_plantio(plantacao2, "trigo")
        cultura = "trigo"
    else:
        print("Opção inválida!")
        return

    if not plantio:
        return

    area_ha = plantio["area"] / 10000
    inseticida = area_ha * 2.5
    bactericida = area_ha * 1.2
    fungicida = area_ha * 1.8
    npk = area_ha * (fosforo + potassio)
    agua = plantio["area"] * irrigacao

    print(f"\n--- Recomendação para plantio de {cultura} ({plantio['area']} m²) ---")
    print(f"Data atual: {hoje.strftime('%d/%m/%Y')}")
    print(f"Estação: {estacao}")
    print(f"pH do solo (mês atual): {ph_mes_atual:.2f}")
    print(f"Umidade do solo (mês atual): {umidade_mes_atual:.2f}%")
    print(f"pH médio do solo (mês atual ): {ph:.2f}")
    print(f"Umidade média do solo (mês atual): {umidade:.2f}%")
    print(f"Inseticida: {inseticida:.2f} L")
    print(f"Bactericida: {bactericida:.2f} L")
    print(f"Fungicida: {fungicida:.2f} L")
    print(f"NPK (baseado em P+K): {npk:.2f} kg")
    print(f"Água de irrigação: {agua:.2f} L")

def aplicar_insumos():
    print("\n===== APLICAR INSUMOS =====")
    print("1 - Milho")
    print("2 - Trigo")
    pd = int(input("Escolha a cultura (1-Milho, 2-Trigo): "))
    
    # Selecionar plantio para aplicar insumos
    plantio = None
    tipo_cultura = ""
    if pd == 1:
        plantio = escolher_plantio(plantacao1, "milho")
        tipo_cultura = "milho"
    elif pd == 2:
        plantio = escolher_plantio(plantacao2, "trigo")
        tipo_cultura = "trigo"
    else:
        print("Opção inválida!")
        return
    
    if not plantio:
        return
    
    # Calcular recomendações de insumos
    dados_csv = ler_recomendacoes_csv()
    if not dados_csv:
        return
    
    hoje = datetime.date.today()
    estacao = obter_estacao(hoje)
    
    # Filtrar os dados para o mês atual
    dados_mes_atual = [linha for linha in dados_csv if nome_mes_para_numero(linha['mes']) == hoje.month]
    
    if not dados_mes_atual:
        print("Sem dados para o mês atual.")
        return
        
    # Pegar valores específicos do mês atual
    ph_mes_atual = float(dados_mes_atual[0]['ph_medio_solo'])
    umidade_mes_atual = float(dados_mes_atual[0]['umidade_media_solo'])
    
    # Continuar com cálculos baseados na estação
    dados_estacao = [linha for linha in dados_csv if linha['estacao'] == estacao]
    
    if not dados_estacao:
        print("Sem dados para a estação atual.")
        return
    
    # Calcular médias sazonais
    umidade = sum(float(l['umidade_media_solo']) for l in dados_estacao) / len(dados_estacao)
    ph = sum(float(l['ph_medio_solo']) for l in dados_estacao) / len(dados_estacao)
    fosforo = sum(float(l['fosforo_P']) for l in dados_estacao) / len(dados_estacao)
    potassio = sum(float(l['potassio_K']) for l in dados_estacao) / len(dados_estacao)
    irrigacao = sum(float(l['agua_irrigacao']) for l in dados_estacao) / len(dados_estacao)
    
    area_ha = plantio["area"] / 10000
    inseticida_rec = area_ha * 2.5
    bactericida_rec = area_ha * 1.2
    fungicida_rec = area_ha * 1.8
    npk_rec = area_ha * (fosforo + potassio)
    agua_rec = plantio["area"] * irrigacao
    
    print(f"\n--- Recomendação para aplicação em {tipo_cultura} ({plantio['area']} m²) ---")
    print(f"Data atual: {hoje.strftime('%d/%m/%Y')}")
    print(f"Estação: {estacao}")
    print(f"pH do solo (mês atual): {ph_mes_atual:.2f}")
    print(f"Umidade do solo (mês atual): {umidade_mes_atual:.2f}%")
    print(f"Inseticida recomendado: {inseticida_rec:.2f} L")
    print(f"Bactericida recomendado: {bactericida_rec:.2f} L")
    print(f"Fungicida recomendado: {fungicida_rec:.2f} L")
    print(f"NPK recomendado: {npk_rec:.2f} kg")
    print(f"Água recomendada: {agua_rec:.2f} L")
    
    print("\nDeseja usar as quantidades recomendadas? (S/N)")
    usar_recomendacao = input().upper()
    
    if usar_recomendacao == 'S':
        qtd_inseticida = inseticida_rec
        qtd_bactericida = bactericida_rec
        qtd_fungicida = fungicida_rec
        qtd_npk = npk_rec
        qtd_agua = agua_rec
    else:
        print("Informe as quantidades manualmente:")
        qtd_inseticida = float(input("Qtd de inseticida (L): "))
        qtd_bactericida = float(input("Qtd de bactericida (L): "))
        qtd_fungicida = float(input("Qtd de fungicida (L): "))
        qtd_npk = float(input("Qtd de NPK (kg): "))
        qtd_agua = float(input("Qtd de água (L): "))
    
    historico_insumos.append({
        "data": datetime.date.today(),
        "estacao": estacao,
        "cultura": tipo_cultura,
        "area": plantio["area"],
        "inseticida": qtd_inseticida,
        "bactericida": qtd_bactericida,
        "fungicida": qtd_fungicida,
        "npk": qtd_npk,
        "agua": qtd_agua
    })
    print("Insumos aplicados com sucesso!")
    print("Lembre-se de salvar as alterações no GitHub (opção 8 do menu) para persistir esses dados.")

def verificar_historico():
    print("\n===== HISTÓRICO DE INSUMOS APLICADOS =====")
    if not historico_insumos:
        print("Nenhum insumo foi aplicado ainda.")
    else:
        for i, h in enumerate(historico_insumos, 1):
            print(f"{i}. Data: {h['data']} | Estação: {h['estacao']} | Cultura: {h['cultura']}")
            print(f"   Área: {h['area']:.2f} m² | Inseticida: {h['inseticida']:.4f} L | Bactericida: {h['bactericida']:.4f} L")
            print(f"   Fungicida: {h['fungicida']:.3f} L | NPK: {h['npk']:.3f} kg | Água: {h['agua']:.2f} L")

def exibir_plantios():
    print("\n--- Plantios de Milho ---")
    for i, p in enumerate(plantacao1, 1):
        print(f"{i} - {p['area']} m²")
    print("\n--- Plantios de Trigo ---")
    for i, p in enumerate(plantacao2, 1):
        print(f"{i} - {p['area']} m²")

def alterar_plantio():
    print("\n===== ALTERAR PLANTIO =====")
    print("1 - Milho")
    print("2 - Trigo")
    pd = int(input("Escolha a cultura: "))
    if pd == 1 and plantacao1:
        p = escolher_plantio(plantacao1, "milho")
        if p: p["area"] = float(input("Nova área (m²): "))
    elif pd == 2 and plantacao2:
        p = escolher_plantio(plantacao2, "trigo")
        if p: p["area"] = float(input("Nova área (m²): "))
    else:
        print("Nenhum plantio disponível.")

def deletar_plantio():
    print("\n===== DELETAR PLANTIO =====")
    print("1 - Milho")
    print("2 - Trigo")
    pd = int(input("Escolha a cultura: "))
    if pd == 1 and plantacao1:
        p = escolher_plantio(plantacao1, "milho")
        if p: plantacao1.remove(p)
    elif pd == 2 and plantacao2:
        p = escolher_plantio(plantacao2, "trigo")
        if p: plantacao2.remove(p)
    else:
        print("Nenhum plantio disponível.")

# Carregar dados salvos quando o programa inicia
print("Carregando dados do GitHub...")
carregar_dados_salvos()

# Loop principal
while True:
    try:
        opcao = menu_principal()
        if opcao == 1:
            adicionar_plantio()
            input("Pressione Enter para continuar...")
        elif opcao == 2:
            calcular_insumos()
            input("Pressione Enter para continuar...")
        elif opcao == 3:
            exibir_plantios()
            input("Pressione Enter para continuar...")
        elif opcao == 4:
            alterar_plantio()
            input("Pressione Enter para continuar...")
        elif opcao == 5:
            deletar_plantio()
            input("Pressione Enter para continuar...")
        elif opcao == 6:
            aplicar_insumos()
            input("Pressione Enter para continuar...")
        elif opcao == 7:
            verificar_historico()
            input("Pressione Enter para continuar...")
        elif opcao == 8:
            if salvar_alteracoes():
                print("Alterações salvas com sucesso no GitHub!")
            else:
                print("Não foi possível salvar todas as alterações.")
            input("Pressione Enter para continuar...")
        elif opcao == 9:
            print("Deseja salvar alterações antes de sair? (S/N)")
            salvar = input().upper()
            if salvar == 'S':
                salvar_alteracoes()
            print("Encerrando o programa.")
            break
        else:
            print("Opção inválida!")
    except Exception as e:
        print(f"Erro: {e}")