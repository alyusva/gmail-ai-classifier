#!/usr/bin/env python3
"""
Migra datos de SQLite local a Supabase (PostgreSQL).

Uso:
    python scripts/migrate_to_supabase.py --migrate
    python scripts/migrate_to_supabase.py --status
    python scripts/migrate_to_supabase.py --verify
    python scripts/migrate_to_supabase.py --emails-only
    python scripts/migrate_to_supabase.py --classifications-only
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from supabase import create_client, Client
except ImportError:
    print("❌ Instala primero: pip install supabase")
    sys.exit(1)

from gmail_classifier.config import SUPABASE_URL, SUPABASE_SERVICE_KEY, DB_FILE


class SupabaseMigrator:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            print("❌ Configura SUPABASE_URL y SUPABASE_SERVICE_KEY en .env")
            sys.exit(1)

        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        self.local_db = sqlite3.connect(DB_FILE)
        self.local_db.row_factory = sqlite3.Row

    # ──────────────────────────────────────────────────────────────
    # Stats
    # ──────────────────────────────────────────────────────────────

    def get_local_stats(self) -> dict:
        cur = self.local_db.cursor()
        return {
            "emails": cur.execute("SELECT COUNT(*) FROM emails").fetchone()[0],
            "classifications": cur.execute("SELECT COUNT(*) FROM classifications").fetchone()[0],
            "taxonomy": cur.execute("SELECT COUNT(*) FROM taxonomy").fetchone()[0],
        }

    def get_supabase_stats(self) -> dict:
        return {
            "emails": self.supabase.table("emails").select("id", count="exact").execute().count or 0,
            "classifications": self.supabase.table("classifications").select("email_id", count="exact").execute().count or 0,
            "taxonomy": self.supabase.table("taxonomy").select("label", count="exact").execute().count or 0,
        }

    def show_status(self):
        local = self.get_local_stats()
        remote = self.get_supabase_stats()

        print(f"\n🗄️  SQLite local ({DB_FILE}):")
        for k, v in local.items():
            print(f"  • {k}: {v:,}")

        print(f"\n☁️  Supabase ({SUPABASE_URL}):")
        for k, v in remote.items():
            print(f"  • {k}: {v:,}")

        diffs = {k: remote[k] - local[k] for k in local}
        if any(v != 0 for v in diffs.values()):
            print("\n⚠️  Diferencias (Supabase − local):")
            for k, v in diffs.items():
                if v != 0:
                    print(f"  • {k}: {v:+,}")
        else:
            print("\n✅ Ambas bases de datos están sincronizadas")

    # ──────────────────────────────────────────────────────────────
    # Migrate
    # ──────────────────────────────────────────────────────────────

    def migrate_emails(self, batch_size: int = 200) -> int:
        """Migra emails de SQLite a Supabase."""
        rows = self.local_db.execute("SELECT * FROM emails").fetchall()
        print(f"\n📧 Migrando {len(rows):,} emails...")

        total = 0
        for i in tqdm(range(0, len(rows), batch_size)):
            batch = rows[i : i + batch_size]
            data = [
                {
                    "id": r["id"],
                    "thread_id": r["thread_id"] or "",
                    "subject": r["subject"] or "(sin asunto)",
                    "sender": r["sender"] or "",
                    "sender_email": r["sender_email"] or "",
                    "snippet": r["snippet"] or "",
                    "date": r["date"] or "",
                    # labels_original en SQLite es JSON string → convertir a lista
                    "labels_original": json.loads(r["labels_original"] or "[]"),
                    "is_read": bool(r["is_read"]),
                }
                for r in batch
            ]
            try:
                self.supabase.table("emails").upsert(data, on_conflict="id").execute()
                total += len(data)
            except Exception as e:
                print(f"\n⚠️  Error en batch {i}: {e}")

        return total

    def migrate_classifications(self, batch_size: int = 200) -> int:
        """Migra clasificaciones de SQLite a Supabase."""
        rows = self.local_db.execute("SELECT * FROM classifications").fetchall()
        print(f"\n🤖 Migrando {len(rows):,} clasificaciones...")

        total = 0
        for i in tqdm(range(0, len(rows), batch_size)):
            batch = rows[i : i + batch_size]
            data = [
                {
                    "email_id": r["email_id"],
                    # labels en SQLite es JSON string de lista → convertir
                    "labels": json.loads(r["labels"] or "[]"),
                    "confidence": r["confidence"] or 0.0,
                    "applied": bool(r["applied"]),
                    "applied_at": r["applied_at"],
                }
                for r in batch
            ]
            try:
                self.supabase.table("classifications").upsert(
                    data, on_conflict="email_id"
                ).execute()
                total += len(data)
            except Exception as e:
                print(f"\n⚠️  Error en batch {i}: {e}")

        return total

    def migrate_taxonomy(self, batch_size: int = 200) -> int:
        """Migra la taxonomía de etiquetas."""
        rows = self.local_db.execute("SELECT * FROM taxonomy").fetchall()
        if not rows:
            return 0
        print(f"\n🏷️  Migrando {len(rows):,} entradas de taxonomía...")

        data = [
            {"label": r["label"], "gmail_label_id": r["gmail_label_id"] or ""}
            for r in rows
        ]
        try:
            self.supabase.table("taxonomy").upsert(data, on_conflict="label").execute()
        except Exception as e:
            print(f"\n⚠️  Error migrando taxonomía: {e}")
            return 0

        return len(data)

    # ──────────────────────────────────────────────────────────────
    # Verify
    # ──────────────────────────────────────────────────────────────

    def verify_migration(self) -> bool:
        local = self.get_local_stats()
        remote = self.get_supabase_stats()

        print("\n📊 VERIFICACIÓN")
        print(f"{'Tabla':<20} {'Local':>10} {'Supabase':>10}  OK?")
        print("-" * 50)

        ok = True
        for k in local:
            match = local[k] == remote[k]
            ok = ok and match
            print(f"{k:<20} {local[k]:>10,} {remote[k]:>10,}  {'✅' if match else '❌'}")

        return ok


def main():
    parser = argparse.ArgumentParser(description="Migrar datos de SQLite a Supabase")
    parser.add_argument("--migrate", action="store_true", help="Migración completa")
    parser.add_argument("--status", action="store_true", help="Mostrar estado actual")
    parser.add_argument("--verify", action="store_true", help="Verificar migración")
    parser.add_argument("--emails-only", action="store_true", help="Solo emails")
    parser.add_argument("--classifications-only", action="store_true", help="Solo clasificaciones")
    parser.add_argument("--batch-size", type=int, default=200, help="Tamaño de lote")
    args = parser.parse_args()

    migrator = SupabaseMigrator()

    if args.status:
        migrator.show_status()

    elif args.verify:
        ok = migrator.verify_migration()
        sys.exit(0 if ok else 1)

    elif args.migrate or args.emails_only or args.classifications_only:
        print("=" * 50)
        print("🚀 MIGRACIÓN SQLite → SUPABASE")
        print("=" * 50)

        if args.migrate or args.emails_only:
            n = migrator.migrate_emails(args.batch_size)
            print(f"✅ {n:,} emails migrados")

        if args.migrate or args.classifications_only:
            n = migrator.migrate_classifications(args.batch_size)
            print(f"✅ {n:,} clasificaciones migradas")

        if args.migrate:
            n = migrator.migrate_taxonomy(args.batch_size)
            print(f"✅ {n:,} entradas de taxonomía migradas")

        print("\n🎉 ¡Completado!")
        migrator.verify_migration()

    else:
        parser.print_help()
        print("\nEjemplos:")
        print("  python scripts/migrate_to_supabase.py --status")
        print("  python scripts/migrate_to_supabase.py --migrate")
        print("  python scripts/migrate_to_supabase.py --verify")


if __name__ == "__main__":
    main()
