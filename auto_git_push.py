
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

ARCHIVO_OBJETIVO = "app_online.py"

class CambiosHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(ARCHIVO_OBJETIVO):
            print(f"🔄 Archivo modificado: {ARCHIVO_OBJETIVO}")
            ejecutar_comandos_git()

def ejecutar_comandos_git():
    try:
        subprocess.run(["git", "add", ARCHIVO_OBJETIVO], check=True)
        subprocess.run(["git", "commit", "-m", "🧠 Actualización automática"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ Cambios enviados a GitHub correctamente.")
    except subprocess.CalledProcessError as e:
        print("❌ Error al ejecutar comandos git:", e)

if __name__ == "__main__":
    print("👁️ Escuchando cambios en", ARCHIVO_OBJETIVO)
    event_handler = CambiosHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
