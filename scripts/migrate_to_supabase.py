#!/usr/bin/env python3
"""
Script para migrar datos de SQLite local a Supabase (PostgreSQL).

Uso:
    python scripts/migrate_to_supabase.py --migrate
    python scripts/migrate_to_supabase.py --status
    python scripts/migrate_to_supabase.py --verify
"""

import sys
import argparse
from pathlib import Path
import sqlite3
from typing import List, Dict
from tqdm import tqdm

# Añadir el directorio padre al path para importar gmail_classifier
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from supabase import create_client, Client
except ImportError:
    print("❌ Error: Instala primero: pip install supabase")
    sys.exit(1)

from gmail_classifier.config import (
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY,
    DB_FILE
)


class SupabaseMigrator:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            print("❌ Error: Configura SUPABASE_URL y SUPABASE_SERVICE_KEY en .env")
            sys.exit(1)

        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        self.local_db = sqlite3.connect(DB_FILE)
        self.local_db.row_factory = sqlite3.Row

    def get_local_stats(self) -> Dict:
        """Obtiene estadísticas de la base de datos local."""
        cursor = self.local_db.cursor()

        total_emails = cursor.execute("SELECT COUNT(*) FROM emails").fetchone()[0]
        total_classifications = cursor.execute("SELECT COUNT(*) FROM classifications").fetchone()[0]

        return {
            'emails': total_emails,
            'classifications': total_classifications
        }

    def get_supabase_stats(self) -> Dict:
        """Obtiene estadísticas de Supabase."""
        emails_count = self.supabase.table('emails').select('id', count='exact').execute()
        classifications_count = self.supabase.table('classifications').select('id', count='exact').execute()

        return {
            'emails': emails_count.count if emails_count else 0,
            'classifications': classifications_count.count if classifications_count else 0
        }

    def migrate_emails(self, batch_size: int = 100) -> int:
        """Migra emails de SQLite a Supabase."""
        cursor = self.local_db.cursor()
        cursor.execute("SELECT * FROM emails")

        emails = cursor.fetchall()
        total_migrated = 0

        print(f"\n📧 Migrando {len(emails)} emails...")

        for i in tqdm(range(0, len(emails), batch_size), desc="Procesando"):
            batch = emails[i:i + batch_size]

            # Convertir a diccionarios
            batch_data = [
                {
                    'message_id': row['message_id'],
                    'thread_id': row['thread_id'],
                    'subject': row['subject'],
                    'sender': row['sender'],
                    'date': row['date'],
                    'snippet': row['snippet'],
                    'labels': row['labels'].split(',') if row['labels'] else []
                }
                for row in batch
            ]

            try:
                # Upsert (insert or update)
                self.supabase.table('emails').upsert(batch_data).execute()
                total_migrated += len(batch_data)
            except Exception as e:
                print(f"\n⚠️  Error en batch {i}: {e}")
                continue

        return total_migrated

    def migrate_classifications(self, batch_size: int = 100) -> int:
        """Migra clasificaciones de SQLite a Supabase."""
        cursor = self.local_db.cursor()
        cursor.execute("SELECT * FROM classifications")

        classifications = cursor.fetchall()
        total_migrated = 0

        print(f"\n🤖 Migrando {len(classifications)} clasificaciones...")

        for i in tqdm(range(0, len(classifications), batch_size), desc="Procesando"):
            batch = classifications[i:i + batch_size]

            batch_data = [
                {
                    'message_id': row['message_id'],
                    'category': row['category'],
                    'confidence': row['confidence'],
                    'reasoning': row['reasoning'],
                    'model': row['model']
                }
                for row in batch
            ]

            try:
                self.supabase.table('classifications').insert(batch_data).execute()
                total_migrated += len(batch_data)
            except Exception as e:
                print(f"\n⚠️  Error en batch {i}: {e}")
                continue

        return total_migrated

    def verify_migration(self) -> bool:
        """Verifica que la migración fue exitosa."""
        local_stats = self.get_local_stats()
        supabase_stats = self.get_supabase_stats()

        print("\n📊 VERIFICACIÓN DE MIGRACIÓN")
        print("=" * 50)
        print(f"{'Tabla':<20} {'Local':<15} {'Supabase':<15} {'Status'}")
        print("-" * 50)

        emails_match = local_stats['emails'] == supabase_stats['emails']
        classifications_match = local_stats['classifications'] == supabase_stats['classifications']

        print(f"{'Emails':<20} {local_stats['emails']:<15} {supabase_stats['emails']:<15} {'✅' if emails_match else '❌'}")
        print(f"{'Classifications':<20} {local_stats['classifications']:<15} {supabase_stats['classifications']:<15} {'✅' if classifications_match else '❌'}")

        return emails_match and classifications_match

    def show_status(self):
        """Muestra el estado actual de ambas bases de datos."""
        print("\n📊 ESTADO ACTUAL")
        print("=" * 50)

        local_stats = self.get_local_stats()
        supabase_stats = self.get_supabase_stats()

        print(f"\n🗄️  SQLite Local ({DB_FILE}):")
        print(f"  • Emails: {local_stats['emails']:,}")
        print(f"  • Clasificaciones: {local_stats['classifications']:,}")

        print(f"\n☁️  Supabase ({SUPABASE_URL}):")
        print(f"  • Emails: {supabase_stats['emails']:,}")
        print(f"  • Clasificaciones: {supabase_stats['classifications']:,}")

        difference_emails = supabase_stats['emails'] - local_stats['emails']
        difference_classifications = supabase_stats['classifications'] - local_stats['classifications']

        if difference_emails != 0 or difference_classifications != 0:
            print(f"\n⚠️  Diferencias:")
            if difference_emails != 0:
                print(f"  • Emails: {difference_emails:+,}")
            if difference_classifications != 0:
                print(f"  • Clasificaciones: {difference_classifications:+,}")
        else:
            print(f"\n✅ Ambas bases de datos están sincronizadas")


def main():
    parser = argparse.ArgumentParser(description="Migrar datos de SQLite a Supabase")
    parser.add_argument('--migrate', action='store_true', help='Ejecutar migración completa')
    parser.add_argument('--status', action='store_true', help='Mostrar estado actual')
    parser.add_argument('--verify', action='store_true', help='Verificar migración')
    parser.add_argument('--emails-only', action='store_true', help='Migrar solo emails')
    parser.add_argument('--classifications-only', action='store_true', help='Migrar solo clasificaciones')
    parser.add_argument('--batch-size', type=int, default=100, help='Tamaño de lote para migración')

    args = parser.parse_args()

    migrator = SupabaseMigrator()

    if args.status:
        migrator.show_status()

    elif args.verify:
        success = migrator.verify_migration()
        sys.exit(0 if success else 1)

    elif args.migrate or args.emails_only or args.classifications_only:
        print("=" * 50)
        print("🚀 MIGRACIÓN A SUPABASE")
        print("=" * 50)

        if args.migrate or args.emails_only:
            emails_migrated = migrator.migrate_emails(args.batch_size)
            print(f"✅ {emails_migrated:,} emails migrados")

        if args.migrate or args.classifications_only:
            classifications_migrated = migrator.migrate_classifications(args.batch_size)
            print(f"✅ {classifications_migrated:,} clasificaciones migradas")

        print("\n🎉 ¡Migración completada!")
        print("\nVerificando...")
        migrator.verify_migration()

    else:
        parser.print_help()
        print("\nEjemplo de uso:")
        print("  python scripts/migrate_to_supabase.py --status")
        print("  python scripts/migrate_to_supabase.py --migrate")
        print("  python scripts/migrate_to_supabase.py --verify")


if __name__ == "__main__":
    main()
