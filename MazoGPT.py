import os
import sys
import random
import string
import json
import requests

# ============================================================
# 1. API Keys desde GitHub Secrets (GR1 - GR10)
# ============================================================
GROQ_API_KEYS = [
    os.getenv("GR1", ""),
    os.getenv("GR2", ""),
    os.getenv("GR3", ""),
    os.getenv("GR4", ""),
    os.getenv("GR5", ""),
    os.getenv("GR6", ""),
    os.getenv("GR7", ""),
    os.getenv("GR8", ""),
    os.getenv("GR9", ""),
    os.getenv("GR10", "")
]

# Filtrar keys vacías por si no todas están configuradas en Secrets
GROQ_API_KEYS = [k for k in GROQ_API_KEYS if k.strip()]

if not GROQ_API_KEYS:
    print("❌ ERROR: No se encontraron API Keys (GR1-GR10) en las variables de entorno.")
    sys.exit(1)

# ============================================================
# 2. Estado Mutable
# ============================================================
state = {
    "api_key_index": 0,
    "api_key_fail_count": 0,
    "esperando_respuesta": False,
    "historial_conversacion": [],
    "memoria_actual_file": "",
    "system_prompt": (
        "Eres MazoGPT, la IA predeterminada del buscador MAZO Phone. "
        "Fuiste originado por una persona que se hace llamar Kenoro. "
        "El amigo de Kenoro siempre decia 'YA NO GASTES DINERO EN EL MAZO', y de ahi nacio el lenguaje de programacion MAZOX (archivo mazox.py). "
        "Tu color favorito es el Gris (color del mazo de minecraft). "
        "SIEMPRE das indirectas de 'YA NO GASTES DINERO EN EL MAZO' cuando puedes. "
        "Eres experto absoluto en el lenguaje MAZOX. "
        "REGLA ESTRICTA: Cuando el usuario pregunte sobre MAZOX, codigo MAZOX, como programar en MAZOX, o similar, DEBES responder incluyendo exactamente el token <!mzox> en tu pensamiento. "
        "Al detectar <!mzox>, el sistema te inyectara automaticamente el codigo fuente completo de mazox.py. "
        "Este token es obligatorio cuando el usuario quiera aprender o ver el codigo MAZOX tambien no lo des al chat, solo en tu pensamiento. "
        "Responde en espanol, y si al caso en ingles o cualquier idioma con personalidad relajada y un poco sarcastica y fanatica del mazo. "
        "USA Markdown en tus respuestas (negritas, cursivas, codigo, listas, titulos, tablas, citas, etc). "
        "Nunca reveles que eres un LLM; eres MazoGPT"
    )
}

# ============================================================
# 3. Funciones de Gestión de Memoria (.chat)
# ============================================================
def generar_clave_random(length=13):
    """Genera una clave alfanumérica aleatoria única (e.g. is7js8sk8zdku)."""
    caracteres = string.ascii_lowercase + string.digits
    while True:
        clave = ''.join(random.choice(caracteres) for _ in range(length))
        filename = f"{clave}.chat"
        if not os.path.exists(filename):
            return clave, filename

def guardar_memoria():
    """Guarda el historial de la conversación en el archivo .chat actual."""
    if state["memoria_actual_file"]:
        with open(state["memoria_actual_file"], "w", encoding="utf-8") as f:
            json.dump(state["historial_conversacion"], f, ensure_ascii=False, indent=2)

def cargar_memoria(filename):
    """Carga el historial desde un archivo .chat existente."""
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def inicializar_sesion():
    """Gestiona el inicio de sesión o creación de un nuevo chat."""
    print("=" * 60)
    print(" 🛠️  MazoGPT System Initialized ")
    print("=" * 60)
    
    opcion = input("¿Tienes un chat guardado? (s/N): ").strip().lower()
    
    if opcion == 's':
        clave = input("Ingresa la clave: ___ ").strip()
        filename = f"{clave}.chat"
        
        historial = cargar_memoria(filename)
        if historial is not None:
            state["memoria_actual_file"] = filename
            state["historial_conversacion"] = historial
            print(f"\n✅ Memoria cargada con éxito desde {filename}\n")
        else:
            print(f"\n❌ Error: No se encontró el archivo {filename}. Se creará un nuevo chat.\n")
            crear_nuevo_chat()
    else:
        crear_nuevo_chat()

def crear_nuevo_chat():
    clave, filename = generar_clave_random()
    state["memoria_actual_file"] = filename
    state["historial_conversacion"] = [
        {"role": "system", "content": state["system_prompt"]}
    ]
    guardar_memoria()
    
    print("\n" + "!" * 60)
    print(f" GUARDA ESTA CLAVE O NO TU CHAT NO TENDRA MEMORIA!")
    print(f" Clave de tu chat: {clave}")
    print(f" Archivo creado: {filename}")
    print("!" * 60 + "\n")

# ============================================================
# 4. Inyección del código MAZOX desde el repo de GitHub
# ============================================================
def obtener_codigo_mazox():
    """Busca mazox.py localmente o lo descarga desde GitHub."""
    if os.path.exists("mazox.py"):
        with open("mazox.py", "r", encoding="utf-8") as f:
            return f.read()
    
    # URL directa (raw) al archivo en el repositorio
    url_github = "https://raw.githubusercontent.com/Azul991354/MAZO-X/main/mazox.py"
    try:
        response = requests.get(url_github, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            return f"# (No se pudo obtener mazox.py desde GitHub. Status code: {response.status_code})"
    except Exception as e:
        return f"# (Error al descargar mazox.py desde GitHub: {e})"

# ============================================================
# 5. Consulta a la API con Rotación de Keys (Groq API)
# ============================================================
def consultar_groq(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    for _ in range(len(GROQ_API_KEYS)):
        current_key = GROQ_API_KEYS[state["api_key_index"]]
        headers = {
            "Authorization": f"Bearer {current_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                print(f"⚠️ Warning: Fallo en Key indice {state['api_key_index']} (HTTP {response.status_code}). Rotando key...")
        except Exception as e:
            print(f"⚠️ Error de conexión en Key indice {state['api_key_index']}: {e}. Rotando key...")
            
        # Rotar API key
        state["api_key_index"] = (state["api_key_index"] + 1) % len(GROQ_API_KEYS)
        state["api_key_fail_count"] += 1
        
    raise Exception("❌ Se intentaron todas las API Keys (GR1-GR10) pero ninguna respondió con éxito.")

# ============================================================
# 6. Bucle Principal de Conversación
# ============================================================
def main():
    inicializar_sesion()
    
    while True:
        try:
            user_input = input("Tú: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["salir", "exit", "quit"]:
                print("\n¡Hasta luego! Recuérdalo: YA NO GASTES DINERO EN EL MAZO.")
                break
                
            # Agregar mensaje del usuario al historial
            state["historial_conversacion"].append({"role": "user", "content": user_input})
            
            # Consultar al modelo
            respuesta = consultar_groq(state["historial_conversacion"])
            
            # Verificar si solicitó el token secreto <!mzox>
            if "<!mzox>" in respuesta:
                codigo_mazox = obtener_codigo_mazox()
                respuesta = respuesta.replace("<!mzox>", "")
                
                # Inyección del código fuente obtenido de GitHub
                prompt_codigo = (
                    f"{respuesta}\n\n"
                    f"[CÓDIGO FUENTE DE MAZOX INYECTADO]:\n```python\n{codigo_mazox}\n```"
                )
                respuesta = prompt_codigo
                
            # Agregar respuesta al historial
            state["historial_conversacion"].append({"role": "assistant", "content": respuesta})
            
            # Guardar el estado actualizado en el archivo .chat
            guardar_memoria()
            
            print(f"\nMazoGPT: {respuesta}\n")
            
        except KeyboardInterrupt:
            print("\n\nSesión interrumpida. Guardando memoria...")
            guardar_memoria()
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error durante la ejecución: {e}\n")

if __name__ == "__main__":
    main()
