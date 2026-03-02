import time
import subprocess
import os

def run_pioneer_service():
    print("🚀 PIONEER 3.0 DAEMON : ACTIVÉ")
    print("Surveillance de l'intelligence en cours...")
    
    while True:
        try:
            # Exécution du cycle toutes les 60 secondes pour la démo
            subprocess.run(["python3", "pioneer_master.py"], check=True)
            time.sleep(60)
        except KeyboardInterrupt:
            print("
Arrêt du service.")
            break
        except Exception as e:
            print(f"Erreur Daemon : {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_pioneer_service()
