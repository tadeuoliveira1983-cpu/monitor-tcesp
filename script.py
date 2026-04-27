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

# Configurações de E-mail (Pegando das variáveis de ambiente do GitHub)
EMAIL_REMETENTE = os.environ.get("EMAIL_USER")
EMAIL_SENHA = os.environ.get("EMAIL_PASS")
EMAIL_DESTINATARIO = os.environ.get("EMAIL_USER") # Pode ser o mesmo ou outro

def enviar_email(assunto, corpo_html):
    # O EMAIL_USER será seu Gmail pessoal
    # O EMAIL_PASS será a Senha de App do seu Gmail
    remetente_gmail = os.environ.get("EMAIL_USER") 
    senha_gmail = os.environ.get("EMAIL_PASS")
    
    # Aqui você define como quer aparecer na caixa de entrada do seu corporativo
    # Exemplo: "Alerta TCE <seu-email@smarapd.com.br>"
    nome_exibicao = "Monitor TCE"
    email_corporativo = "atboliveira@smarapd.com.br" # Coloque seu e-mail da empresa aqui

    msg = MIMEMultipart()
    # Esta linha configura o remetente que você verá no Outlook
    msg['From'] = f"{nome_exibicao} <{email_corporativo}>"
    msg['To'] = email_corporativo 
    msg['Subject'] = assunto

    msg.attach(MIMEText(corpo_html, 'html'))

    try:
        # Configuração para Gmail
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
            data_pub = cols[3].get_text(strip=True)

           mes_atual = datetime.now().strftime("/%m/")
           
           if area in ['AUDESP', 'SDG'] and mes_atual in data_pub:
                comunicados.append({
                    "id": f"{codigo}-{data_pub}",
                    "codigo": codigo,
                    "data": data_pub,
                    "titulo": titulo_elem.get_text(strip=True),
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
        corpo = "<h2>Novos Comunicados TCE-SP (Março)</h2><ul>"
        for n in novos:
            corpo += f"<li><b>{n['codigo']}</b> ({n['data']})<br>{n['titulo']}<br><a href='{n['link']}'>Link Direto</a></li><br>"
            vistos.append(n['id'])
        corpo += "</ul>"
        
        enviar_email("Alerta: Novos Comunicados AUDESP/SDG", corpo)
        
        with open(DB_FILE, 'w') as f:
            json.dump(vistos, f)
    else:
        print("Sem novidades para enviar por e-mail.")

if __name__ == "__main__":
    main()
