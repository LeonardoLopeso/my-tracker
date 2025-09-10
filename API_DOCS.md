# 📊 API de Rastreamento - Documentação

## 🚀 Endpoints Disponíveis

### 1. **Página Inicial**
- **URL**: `http://localhost:5000/`
- **Método**: GET
- **Descrição**: Página inicial com links para todos os endpoints

### 2. **Rastrear Clique**
- **URL**: `http://localhost:5000/track/<campaign_id>`
- **Método**: GET
- **Descrição**: Captura dados do usuário e redireciona para Instagram
- **Exemplo**: `http://localhost:5000/track/minha_campanha`

### 3. **Visualizar Logs (JSON)**
- **URL**: `http://localhost:5000/logs`
- **Método**: GET
- **Descrição**: Retorna todos os cliques em formato JSON
- **Resposta**:
```json
{
  "status": "success",
  "total_clicks": 5,
  "logs": [
    {
      "Timestamp": "2025-09-10 01:34:39",
      "IP": "192.168.3.16",
      "User Agent": "Mozilla/5.0...",
      "Referrer": "N/A",
      "Latitude": "Local",
      "Longitude": "Local",
      "Cidade": "Rede Local",
      "Região": "Rede Local",
      "País": "Rede Local",
      "Campanha": "teste"
    }
  ]
}
```

### 4. **Baixar Logs (CSV)**
- **URL**: `http://localhost:5000/logs/csv`
- **Método**: GET
- **Descrição**: Baixa o arquivo de logs em formato CSV

### 5. **Estatísticas**
- **URL**: `http://localhost:5000/stats`
- **Método**: GET
- **Descrição**: Retorna estatísticas dos cliques
- **Resposta**:
```json
{
  "status": "success",
  "stats": {
    "total_clicks": 5,
    "campaigns": {
      "teste": 3,
      "minha_campanha": 2
    },
    "countries": {
      "Rede Local": 5
    },
    "cities": {},
    "unique_ips": 2,
    "ip_frequency": {
      "127.0.0.1": 2,
      "192.168.3.16": 3
    }
  }
}
```

## 🧪 Como Testar

1. **Inicie o servidor**:
```bash
cd /home/leolopeso/projects/digital-investigation/capture-info
source venv/bin/activate
python my-tracker.py
```

2. **Teste os endpoints**:
- Acesse: `http://localhost:5000/`
- Clique em: `http://localhost:5000/track/teste`
- Veja os logs: `http://localhost:5000/logs`
- Veja estatísticas: `http://localhost:5000/stats`

## 📝 Estrutura dos Dados

Cada clique captura:
- **Timestamp**: Data e hora do clique
- **IP**: Endereço IP do usuário
- **User Agent**: Navegador/dispositivo
- **Referrer**: Página de origem
- **Latitude/Longitude**: Coordenadas geográficas
- **Cidade/Região/País**: Localização
- **Campanha**: ID da campanha

## 🔧 Configuração

- **URL de destino**: Instagram (`https://www.instagram.com/`)
- **Arquivo de log**: `clicks.log`
- **Porta**: 5000
- **API de geolocalização**: IPStack (gratuita)
