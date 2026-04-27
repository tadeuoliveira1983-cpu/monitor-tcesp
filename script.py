import requests
from bs4 import BeautifulSoup
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Configurações do TCE
URL_BASE = "https://www.tce.sp.gov.br"
URL_COMUNICADOS = f"{URL_BASE}/comunicados"
DB_FILE = "comunicados_vistos.json"

# LISTA DE TERMOS PARA EXCLUIR (Filtro de assunto)
TERMOS_EXCLUIDOS = [
    "atos de pessoal", "fase iv", "área estadual", "composição do tribunal",
    "concursos públicos", "data comemorativa", "educação fiscal",
    "elaboração da política", "entidades proibidas de novos repasses",
    "fase iii", "fase v", "iralc", "ok", "plano municipal da primeira infância",
    "políticas públicas", "prorrogação do prazo de adesão",
    "questionários do ieg", "volume de processos"
]

def enviar_email(assunto, corpo_html):
    # Pega as credenciais do Gmail que você configurou nos Secrets do GitHub
    remetente_gmail = os.environ.get("EMAIL_USER") 
    senha_gmail = os.environ.get("EMAIL_PASS")
    
    # Suas configurações de exibição e destino corporativo
    nome_exibicao = "Monitor TCE"
    email_corporativo = "atboliveira@smarapd.com.br"

    msg = MIMEMultipart()
    # Mantém a configuração de "From" que você estava usando
    msg['From'] = f"{nome_exibicao} <{remetente_gmail}>"
    msg['To'] = email_corporativo 
    msg['Subject'] = assunto

    msg.attach(MIMEText(corpo_html, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente_gmail, senha_gmail)
        server.sendmail(remetente_gmail, email_corporativo, msg.as_string())
        server.quit()
        print("E-mail enviado via Gmail com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        
def buscar_comunicados():
    headers = {'User-Agent': 'Mozilla/5.0'}
    # Mantém a lógica de mês dinâmico que você adicionou (/04/, /05/, etc)
    mes_atual = datetime.now().strftime("/%m/")
    
    try:
        response = requests.get(URL_COMUNICADOS, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        tabela = soup.find('table')
        if not tabela: return []

        comunicados = []
        rows = tabela.find_all('tr')[1:]
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 4: continue
            
            area = cols[0].get_text(strip=True).upper()
            codigo = cols[1].get_text(strip=True)
            titulo_elem = cols[2].find('a')
            titulo = titulo_elem.get_text(strip=True)
            data_pub = cols[3].get_text(strip=True)

            # LÓGICA DE FILTRO:
            # 1. Verifica se é AUDESP/SDG e se é do mês atual
            # 2. Verifica se o título contém algum dos termos proibidos
            titulo_low = titulo.lower()
            contem_excluido = any(termo in titulo_low for termo in TERMOS_EXCLUIDOS)

            if area in ['AUDESP', 'SDG'] and mes_atual in data_pub and not contem_excluido:
                comunicados.append({
                    "id": f"{codigo}-{data_pub}",
                    "codigo": codigo,
                    "data": data_pub,
                    "titulo": titulo,
                    "link": URL_BASE + titulo_elem['href']
                })
        return comunicados
    except:
        return []

def main():
    todos = buscar_comunicados()
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f: vistos = json.load(f)
    else: vistos = []

    novos = [c for c in todos if c['id'] not in vistos]

    if novos:
        # Título dinâmico para o corpo do e-mail
        corpo = f"<h2>Novos Comunicados TCE-SP</h2><ul>"
        for n in novos:
            corpo += f"<li><b>{n['codigo']}</b> ({n['data']})<br>{n['titulo']}<br><a href='{n['link']}'>Link Direto</a></li><br>"
            vistos.append(n['id'])
        corpo += "</ul>"
        
        enviar_email("Alerta: Novos Comunicados AUDESP/SDG", corpo)
        
        with open(DB_FILE, 'w') as f:
            json.dump(vistos, f)
    else:
        print("Sem novidades relevantes para enviar por e-mail.")

if __name__ == "__main__":
    main()
