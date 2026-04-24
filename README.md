# Tradovate Trading Dashboard 📊

Dashboard web para visualizar estadísticas de tu cuenta de Tradovate en tiempo real.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Características

- 📊 **Resumen de cuenta**: Equity, Balance, Margin, PnL
- 📈 **Estadísticas de rendimiento**: Win Rate, Profit Factor, Avg Win/Loss
- 📋 **Trades recientes**: Últimos 20 trades con dirección y PnL
- 🟢 **Posiciones abiertas**: Ver posiciones actuales
- 🔄 **Auto-refresh**: Actualización automática cada 30 segundos
- 🎨 **Dark theme**: Diseño profesional estilo trading
- 🔐 **Setup interactivo**: Wizard para configurar credenciales

## 🚀 Inicio Rápido

### 1. Clonar el repositorio
```bash
git clone https://github.com/saitamawtf/tradovate-dashboard.git
cd tradovate-dashboard
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecutar el setup interactivo
```bash
python setup.py
```

El wizard te pedirá:
- Email de Tradovate
- Password
- Probará la conexión automáticamente

### 4. Iniciar el dashboard
```bash
python app.py
```

### 5. Abrir en el navegador
```
http://localhost:5000
```

## 🎯 Uso del Setup Wizard

El wizard permite:

| Opción | Descripción |
|--------|-------------|
| [1] Ingresar credenciales | Configura email y password |
| [2] Actualizar Access Token | Cambia el token de acceso |
| [3] Borrar credenciales | Elimina credenciales guardadas |
| [4] Ir al dashboard | Inicia el servidor web |
| [5] Salir | Cierra el wizard |

## 📡 API Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Dashboard web |
| `/api/connect` | POST | Conectar a Tradovate |
| `/api/dashboard/summary` | GET | Resumen de cuenta |
| `/api/dashboard/performance` | GET | Métricas de rendimiento |
| `/api/dashboard/trades` | GET | Trades recientes |
| `/api/dashboard/positions` | GET | Posiciones abiertas |
| `/api/disconnect` | POST | Desconectar |

## 📁 Estructura del Proyecto

```
tradovate-dashboard/
├── app.py              # Flask web app
├── setup.py            # Wizard interactivo de configuración
├── tradovate_api.py    # Cliente API + estadísticas
├── templates/
│   └── index.html      # Interfaz web completa
├── config.json         # Credenciales (encriptado)
├── requirements.txt    # Dependencias
└── README.md           # Este archivo
```

## 🔒 Seguridad

- Las credenciales se guardan en `config.json` (local)
- El Access Token se genera automáticamente
- No se transmiten passwords en texto plano después de la primera conexión
- Puedes borrar credenciales en cualquier momento con el wizard

## ⚙️ Requisitos

- Python 3.8+
- Cuenta de Tradovate con API Access
- $1000+ equity o $30/mes para acceso a la API

## 🐛 Solución de Problemas

### Error de conexión
```
❌ Conexión fallida: Credenciales inválidas
```
→ Verifica tu email y password de Tradovate

### Timeout
```
❌ Timeout conectando a Tradovate
```
→ Revisa tu conexión a internet

### Puerto en uso
```
ERROR: Address already in use
```
→ Otro proceso está usando el puerto 5000. Cierra ese proceso o usa otro puerto.

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcion`)
3. Commit (`git commit -am 'Agrega nueva función'`)
4. Push (`git push origin feature/nueva-funcion`)
5. Abre un Pull Request

## 📄 Licencia

MIT License - ver archivo [LICENSE](LICENSE) para más detalles.

---

¿Tienes dudas o problemas? Abre un issue en GitHub. 🚀