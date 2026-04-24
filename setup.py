#!/usr/bin/env python3
"""
Tradovate Dashboard - Interactive Setup Wizard
Configura las credenciales de forma interactiva
"""

import os
import json
import getpass

CONFIG_FILE = "config.json"


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    print("""
╔══════════════════════════════════════════════════════════════╗
║          TRADOVATE DASHBOARD - SETUP WIZARD                 ║
║                                                              ║
║  🔐 Configura tus credenciales de Tradovate                  ║
╚══════════════════════════════════════════════════════════════╝
    """)


def print_success(message):
    print(f"  ✅ {message}")


def print_error(message):
    print(f"  ❌ {message}")


def print_info(message):
    print(f"  ℹ️  {message}")


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"name": "", "password": "", "access_token": ""}


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def validate_credentials(name, password):
    """Valida que las credenciales no estén vacías"""
    if not name or len(name) < 3:
        return False, "El email debe tener al menos 3 caracteres"
    if not password or len(password) < 4:
        return False, "El password debe tener al menos 4 caracteres"
    return True, ""


def test_connection(name, password):
    """Prueba la conexión con Tradovate"""
    import requests
    
    url = "https://live.tradovateapi.com/v1/auth/accesstokenrequest"
    payload = {
        "name": name,
        "password": password,
        "appId": "TradovateDashboard",
        "appVersion": "1.0",
        "cid": 0,
        "sec": ""
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('accessToken')
            if access_token:
                return True, access_token
        return False, "Credenciales inválidas"
    except requests.exceptions.Timeout:
        return False, "Timeout conectando a Tradovate"
    except requests.exceptions.ConnectionError:
        return False, "No se puede conectar a Tradovate (revisa tu conexión)"
    except Exception as e:
        return False, f"Error: {str(e)}"


def setup_interactive():
    clear_screen()
    print_header()
    
    config = load_config()
    
    print("\n  📋 Credenciales guardadas actualmente:")
    if config.get('access_token'):
        print("  ├── Access Token: ✓ configurado")
        print(f"  ├── Usuario: {config.get('name', 'NO')}")
        print("  └── Password: ✓ configurado")
    elif config.get('name'):
        print(f"  ├── Usuario: {config.get('name')}")
        print("  └── Password: NO configurado")
    else:
        print("  └── Sin credenciales guardadas")
    
    print("\n" + "─" * 60)
    print("  ¿Qué deseas hacer?")
    print("  ─" * 60)
    print("""
  [1] 🔑 Ingresar nuevas credenciales
  [2] 🔄 Actualizar Access Token
  [3] 🗑️  Borrar credenciales guardadas
  [4] 🚀 Ir al dashboard (usar credenciales existentes)
  [5] ❌ Salir
    """)
    
    choice = input("\n  → Selecciona una opción (1-5): ").strip()
    
    if choice == "1":
        setup_credentials(config)
    elif choice == "2":
        setup_token(config)
    elif choice == "3":
        clear_credentials(config)
    elif choice == "4":
        if config.get('name') and config.get('password'):
            start_dashboard()
        else:
            print_error("No hay credenciales configuradas!")
            input("\n  Presiona Enter para continuar...")
            setup_interactive()
    elif choice == "5":
        print("\n  👋 ¡Hasta luego!\n")
        exit(0)
    else:
        print_error("Opción inválida")
        input("\n  Presiona Enter para continuar...")
        setup_interactive()


def setup_credentials(config):
    clear_screen()
    print_header()
    
    print("\n  📧 INGRESO DE CREDENCIALES")
    print("  " + "─" * 50)
    print("  (Ingresa tus datos de Tradovate)\n")
    
    # Email
    default_name = config.get('name', '')
    name = input(f"  Email/Usuario [{default_name}]: ").strip()
    if not name and default_name:
        name = default_name
    
    # Password
    password = getpass.getpass("  Password: ").strip()
    
    # Confirmar password
    password_confirm = getpass.getpass("  Confirmar Password: ").strip()
    
    if not name:
        print_error("El email es requerido")
        input("\n  Presiona Enter para continuar...")
        setup_credentials(config)
        return
    
    if not password:
        print_error("El password es requerido")
        input("\n  Presiona Enter para continuar...")
        setup_credentials(config)
        return
    
    if password != password_confirm:
        print_error("Los passwords no coinciden")
        input("\n  Presiona Enter para continuar...")
        setup_credentials(config)
        return
    
    # Validar formato
    valid, error = validate_credentials(name, password)
    if not valid:
        print_error(error)
        input("\n  Presiona Enter para continuar...")
        setup_credentials(config)
        return
    
    print("\n  🔄 Probando conexión con Tradovate...")
    
    success, result = test_connection(name, password)
    
    if success:
        config['name'] = name
        config['password'] = password
        config['access_token'] = result
        save_config(config)
        
        print_success("¡Conexión exitosa!")
        print(f"  Access Token guardado: {result[:20]}...")
        
        print("\n  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("  ✅ ¡Configuración completada!")
        print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("""
  Ahora puedes iniciar el dashboard:
  
  → python app.py
  
  O ejecutar este wizard nuevamente para cambiar credenciales.
        """)
        input("  Presiona Enter para ir al dashboard...")
        start_dashboard()
    else:
        print_error(f"Conexión fallida: {result}")
        print_info("Verifica tu email y password de Tradovate")
        input("\n  Presiona Enter para intentar de nuevo...")
        setup_credentials(config)


def setup_token(config):
    clear_screen()
    print_header()
    
    print("\n  🔄 ACTUALIZAR ACCESS TOKEN")
    print("  " + "─" * 50)
    print("""
  El Access Token se usa para reconectar sin repetir password.
  Se genera automáticamente cuando te conectas,
  o puedes usar uno existente de tu cuenta de Tradovate.
    """)
    
    current_token = config.get('access_token', '')
    if current_token:
        print(f"\n  Token actual: {current_token[:30]}...")
    
    print("\n  Ingresa tu Access Token (o Enter para generar uno nuevo con password):")
    new_token = input("\n  → ").strip()
    
    if new_token:
        config['access_token'] = new_token
        save_config(config)
        print_success("Token actualizado")
    else:
        print_info("Necesitarás el password para generar un nuevo token")
        if config.get('name') and config.get('password'):
            print("\n  Generando nuevo token con credenciales guardadas...")
            success, result = test_connection(config['name'], config['password'])
            if success:
                config['access_token'] = result
                save_config(config)
                print_success(f"Nuevo token generado: {result[:20]}...")
            else:
                print_error(f"Error generando token: {result}")
        else:
            print_error("No hay credenciales guardadas")
            input("\n  Presiona Enter para configurar credenciales...")
            setup_credentials(config)
            return
    
    input("\n  Presiona Enter para continuar...")
    setup_interactive()


def clear_credentials(config):
    clear_screen()
    print_header()
    
    print("\n  🗑️  BORRAR CREDENCIALES")
    print("  " + "─" * 50)
    print("""
  ¿Estás seguro de que quieres borrar todas las credenciales?
  
  Esto NO eliminará el dashboard ni el código, solo las credenciales
  guardadas para conectarte a Tradovate.
    """)
    
    confirm = input("\n  → Escribe 'SI' para confirmar: ").strip().upper()
    
    if confirm == "SI":
        config = {"name": "", "password": "", "access_token": ""}
        save_config(config)
        print_success("Credenciales borradas")
        print_info("La próxima vez que quieras usar el dashboard, tendrás que configurar tus credenciales nuevamente")
    else:
        print_info("Operación cancelada")
    
    input("\n  Presiona Enter para continuar...")
    setup_interactive()


def start_dashboard():
    clear_screen()
    print_header()
    
    print("\n  🚀 INICIANDO DASHBOARD...")
    print("  " + "─" * 50)
    print("""
  El servidor web arrancará en:
  
  → http://localhost:5000
  
  Abre esa dirección en tu navegador.
  
  Presiona Ctrl+C para detener el servidor.
    """)
    
    import subprocess
    import sys
    
    try:
        subprocess.run([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n\n  👋 Dashboard detenido.")
        print("  Para iniciarlo nuevamente: python app.py\n")


if __name__ == "__main__":
    setup_interactive()