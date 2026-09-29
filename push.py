import os
import subprocess
import sys
from datetime import datetime

def run_command(cmd, check=True):
    result = subprocess.run(cmd, shell=True)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result

def main():
    # Aktuální čas a datum
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Pokud uživatel zadal vlastní zprávu jako parametr, použijeme ji spolu s časem
    if len(sys.argv) > 1:
        custom_msg = " ".join(sys.argv[1:])
        commit_msg = f"{custom_msg} ({now_str})"
    else:
        commit_msg = f"Update: {now_str}"

    # 1. Pouze vygenerujeme migrační plány podle aktuálního kódu
    print("-> Generování nových migračních souborů (makemigrations)...")
    run_command("python manage.py makemigrations")

    # 2. Přidáme všechny soubory (včetně nových migrací) do Gitu
    print("-> Přidávání změn (git add .)...")
    run_command("git add .")

    # Kontrola, zda existují změny k commitu
    status = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if status.stdout.strip():
        print(f"-> Vytváření commitu: \"{commit_msg}\"...")
        run_command(f'git commit -m "{commit_msg}"')
    else:
        print("-> Žádné nové změny k uložení do commitu.")

    # 3. Odeslání na GitHub
    print("-> Odesílání na GitHub (git push)...")
    push_res = run_command("git push", check=False)

    if push_res.returncode == 0:
        # Vyčištění konzole po úspěšném odeslání
        os.system("cls")
        print(f"✓ Migrační plány vygenerovány, úspěšně commitnuto a odesláno na GitHub! ({now_str})")
    else:
        print("\n[!] Chyba: Odeslání na vzdálený repozitář (git push) selhalo.")
        sys.exit(push_res.returncode)


if __name__ == "__main__":
    main()