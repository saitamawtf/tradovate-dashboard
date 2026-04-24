# Tradovate Trading Dashboard

Dashboard web para visualizar estadísticas de tu cuenta de Tradovate.

## Características

- 📊 **Resumen de cuenta**: Equity, Balance, Margin, PnL
- 📈 **Estadísticas de rendimiento**: Win Rate, Profit Factor, Avg Win/Loss
- 📋 **Trades recientes**: Últimos 20 trades con dirección y PnL
- 🟢 **Posiciones abiertas**: Ver posiciones actuales
- 🔄 **Auto-refresh**: Actualización automática cada 30 segundos

## Instalación

```bash
cd tradovate-dashboard
pip install -r requirements.txt
```

## Uso

1. **Iniciar el servidor**:
```bash
python app.py
```

2. **Abrir en el navegador**:
```
http://localhost:5000
```

3. **Conectar**:
- Ingresa tu email/password de Tradovate
- O usa un Access Token (más seguro)

## API Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Dashboard web |
| `/api/connect` | POST | Conectar a Tradovate |
| `/api/dashboard/summary` | GET | Resumen de cuenta |
| `/api/dashboard/performance` | GET | Métricas de rendimiento |
| `/api/dashboard/trades` | GET | Trades recientes |
| `/api/dashboard/positions` | GET | Posiciones abiertas |
| `/api/disconnect` | POST | Desconectar |

## Configuración

El dashboard guarda el Access Token en `config.json` para reconexiones automáticas.

## Notas

- Requiere cuenta de Tradovate con API Access
- $1000+ equity o $30/mes para acceso a la API
- Los datos se actualizan cada 30 segundos automáticamente

## Screenshots

El dashboard incluye:
- Cards con estadísticas principales
- Grilla de métricas de rendimiento
- Lista de trades recientes con colores según ganancia/pérdida
- Tabla de posiciones abiertas