import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# Configurações
URL_BASE = "https://www.tce.sp.gov.br"
URL_COMUNICADOS = f"{URL_BASE}/comunicados"
DB_FILE = "comunicados_vistos.json"

def buscar_comunicados():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(URL_COMUNICADOS, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Erro ao acessar o site: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    tabela = soup.find('table')
    if not tabela:
        return []

    comunicados = []
    # Ignora o cabeçalho da tabela
    rows = tabela.find_all('tr')[1:]

    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 4: continue

        area = cols[0].get_text(strip=True).upper()
        codigo = cols[1].get_text(strip=True)
        titulo_elem = cols[2].find('a')
        titulo = titulo_elem.get_text(strip=True)
        link = URL_BASE + titulo_elem['href']
        data_pub = cols[3].get_text(strip=True) # Formato DD/MM/AAAA

        # Filtro: Áreas AUDESP ou SDG e Mês de Março (03)
        if area in ['AUDESP', 'SDG'] and "/03/" in data_pub:
            comunicados.append({
                "id": f"{codigo}-{data_pub}", # Identificador único
                "codigo": codigo,
                "data": data_pub,
                "titulo": titulo,
                "link": link
            })
    
    return comunicados

def carregar_vistos():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def salvar_vistos(vistos):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(vistos, f, ensure_ascii=False, indent=4)

def main():
    print(f"Verificando comunicados em {datetime.now().strftime('%d/%m/%Y %H:%M')}...")
    
    todos_março = buscar_comunicados()
    vistos = carregar_vistos()
    
    # Identifica o que é novo (o ID não está na lista de vistos)
    novos = [c for c in todos_março if c['id'] not in vistos]
    
    if novos:
        print("\n--- NOVOS COMUNICADOS ENCONTRADOS ---")
        for n in novos:
            print(f"Código: {n['codigo']}")
            print(f"Data: {n['data']}")
            print(f"Título: {n['titulo']}")
            print(f"Link: {n['link']}")
            print("-" * 30)
            vistos.append(n['id']) # Adiciona aos vistos
        salvar_vistos(vistos)
    else:
        print("Não houve novos comunicados.")

if __name__ == "__main__":
    main()