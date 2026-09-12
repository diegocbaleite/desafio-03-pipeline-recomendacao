"""Sincroniza e inicializa automaticamente a conexão e o dashboard no Superset com base no .env."""
from __future__ import annotations

import os
import subprocess
import uuid
import zipfile
import yaml
from pathlib import Path
from superset.app import create_app


def extrair_banco_do_zip(caminho_zip: str | Path) -> tuple[uuid.UUID, str]:
    """Extrai dinamicamente o UUID e o nome do banco do próprio arquivo ZIP de exportação."""
    with zipfile.ZipFile(caminho_zip) as z:
        for name in z.namelist():
            if "databases/" in name and (name.endswith(".yaml") or name.endswith(".yml")):
                data = yaml.safe_load(z.read(name))
                return uuid.UUID(data["uuid"]), data.get("database_name", "Other")
    raise FileNotFoundError(f"Arquivo de definição de database não localizado em {caminho_zip}")


def localizar_zip_dashboard(diretorio: Path) -> Path | None:
    """Descobre dinamicamente qualquer arquivo ZIP de exportação presente na pasta do dashboard."""
    zips = sorted(diretorio.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    return zips[0] if zips else None


app = create_app()
with app.app_context():
    from superset import db
    from superset.models.core import Database
    from superset.models.dashboard import Dashboard

    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    database = os.environ["POSTGRES_DB"]
    admin_user = os.environ.get("SUPERSET_ADMIN_USERNAME", "admin")

    diretorio_dashboard = Path(__file__).resolve().parent
    arquivo_zip = localizar_zip_dashboard(diretorio_dashboard)

    if not arquivo_zip:
        raise FileNotFoundError(
            f"Nenhum arquivo .zip de exportação do Superset foi encontrado em {diretorio_dashboard}"
        )

    print(f"[Superset] Pacote ZIP localizado dinamicamente: {arquivo_zip.name}")
    db_uuid, db_name = extrair_banco_do_zip(arquivo_zip)
    print(f"[Superset] Metadados extraídos do ZIP: banco='{db_name}', uuid='{db_uuid}'")

    uri = f"postgresql://{user}:{password}@postgres:5432/{database}"

    # 1. Garante que a conexão com o PostgreSQL existe no Superset vinculada ao UUID dinâmico da exportação
    db_obj = db.session.query(Database).filter(
        (Database.uuid == db_uuid) | (Database.database_name == db_name)
    ).first()

    if not db_obj:
        db_obj = Database(
            database_name=db_name,
            uuid=db_uuid,
            expose_in_sqllab=True,
            allow_run_async=False,
            allow_ctas=False,
            allow_cvas=False,
            allow_dml=False,
        )
        db.session.add(db_obj)
        print(f"[Superset] Criando conexão '{db_name}' com UUID dinâmico {db_uuid}...")

    db_obj.uuid = db_uuid
    db_obj.database_name = db_name
    db_obj.set_sqlalchemy_uri(uri)
    db_obj.password = password
    db_obj.expose_in_sqllab = True
    db.session.commit()
    print(f"[Superset] Conexão '{db_name}' ({db_uuid}) sincronizada com sucesso: {user}@postgres:5432/{database}")

    # 2. Importa automaticamente o dashboard zip se presente
    if arquivo_zip:
        print(f"[Superset] Importando dashboard automaticamente a partir de {arquivo_zip}...")
        res = subprocess.run(
            ["superset", "import-dashboards", "-p", str(arquivo_zip), "-u", admin_user],
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            print("[Superset] Dashboard importado com sucesso via CLI!")
        else:
            print(f"[Superset] Resultado da importação CLI: {res.stdout}\n{res.stderr}")

    # 3. Garante que todos os dashboards estejam publicados (published=True)
    dashboards = db.session.query(Dashboard).all()
    for d in dashboards:
        d.published = True
    db.session.commit()
    print(f"[Superset] {len(dashboards)} dashboard(s) publicado(s) com sucesso.")

