# 🗄️ Migración a Supabase

Esta guía te ayudará a migrar de SQLite local a Supabase (PostgreSQL en la nube).

## ¿Por qué Supabase?

- ✅ **Acceso desde cualquier lugar**: No necesitas tu Mac encendido
- ✅ **Multi-usuario**: Varios usuarios pueden usar la misma instancia
- ✅ **Backups automáticos**: Nunca pierdas tus datos
- ✅ **APIs automáticas**: REST y GraphQL out-of-the-box
- ✅ **Gratis**: Hasta 500MB de almacenamiento + 2GB de transferencia
- ✅ **Escalable**: Crece con tu producto

## Paso 1: Crear Proyecto en Supabase

1. Ve a [https://app.supabase.com](https://app.supabase.com)
2. Crea una cuenta o inicia sesión
3. Click en "New Project"
4. Rellena:
   - **Name**: `gmail-classifier` (o el que prefieras)
   - **Database Password**: Genera una segura (guárdala!)
   - **Region**: Elige la más cercana a ti
   - **Plan**: Free tier (suficiente para empezar)
5. Click "Create new project"

⏳ Espera 1-2 minutos mientras se crea el proyecto.

## Paso 2: Crear Esquema de Base de Datos

### Opción A: SQL Editor (Web)

1. En Supabase Dashboard, ve a "SQL Editor"
2. Click "New query"
3. Copia y pega este SQL:

```sql
-- Tabla de emails
CREATE TABLE emails (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(255) UNIQUE NOT NULL,
    thread_id VARCHAR(255),
    subject TEXT,
    sender VARCHAR(500),
    date TIMESTAMP,
    snippet TEXT,
    labels TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabla de clasificaciones
CREATE TABLE classifications (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(255) NOT NULL,
    category VARCHAR(255) NOT NULL,
    confidence FLOAT,
    reasoning TEXT,
    model VARCHAR(100),
    classified_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (message_id) REFERENCES emails(message_id) ON DELETE CASCADE
);

-- Tabla de progreso (para tracking)
CREATE TABLE progress (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabla de usuarios (para multi-tenant)
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    gmail_email VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    settings JSONB DEFAULT '{}'::jsonb
);

-- Índices para mejorar rendimiento
CREATE INDEX idx_emails_message_id ON emails(message_id);
CREATE INDEX idx_emails_date ON emails(date DESC);
CREATE INDEX idx_classifications_message_id ON classifications(message_id);
CREATE INDEX idx_classifications_category ON classifications(category);
CREATE INDEX idx_users_email ON users(email);

-- Row Level Security (RLS)
ALTER TABLE emails ENABLE ROW LEVEL SECURITY;
ALTER TABLE classifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Políticas RLS (ajustar según necesites)
-- Por ahora, permitir todo (cambiar en producción)
CREATE POLICY "Allow all for authenticated users" ON emails
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all for authenticated users" ON classifications
    FOR ALL USING (auth.role() = 'authenticated');

-- Views útiles
CREATE VIEW classification_summary AS
SELECT
    category,
    COUNT(*) as email_count,
    AVG(confidence) as avg_confidence,
    MAX(classified_at) as last_classified
FROM classifications
GROUP BY category
ORDER BY email_count DESC;
```

4. Click "Run" (▶️)
5. Verifica que todo se creó correctamente

### Opción B: Desde CLI

```bash
# Instalar Supabase CLI
brew install supabase/tap/supabase

# Login
supabase login

# Link a tu proyecto
supabase link --project-ref your-project-ref

# Ejecutar migraciones
supabase db push
```

## Paso 3: Obtener Credenciales

1. En Supabase Dashboard, ve a "Settings" → "API"
2. Copia estos valores:

```env
# URL del proyecto
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co

# Anon key (pública, para frontend)
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Service role key (privada, para backend)
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

3. Añade estos valores a tu archivo `.env`:

```bash
# Añadir al .env
echo "SUPABASE_URL=https://xxxxx.supabase.co" >> .env
echo "SUPABASE_ANON_KEY=eyJhbG..." >> .env
echo "SUPABASE_SERVICE_KEY=eyJhbG..." >> .env
```

## Paso 4: Instalar Cliente de Supabase

```bash
pip install supabase
```

## Paso 5: Migrar Datos Existentes (Opcional)

Si ya tienes datos en SQLite que quieres migrar:

```bash
# Ejecutar script de migración
python scripts/migrate_to_supabase.py

# Ver progreso
python scripts/migrate_to_supabase.py --status
```

El script:
- ✅ Exporta emails de SQLite
- ✅ Los sube a Supabase
- ✅ Exporta clasificaciones
- ✅ Las sube a Supabase
- ✅ Verifica integridad de datos

## Paso 6: Actualizar Código para Usar Supabase

### Crear archivo `gmail_classifier/supabase_db.py`:

```python
from supabase import create_client, Client
from gmail_classifier.config import SUPABASE_URL, SUPABASE_SERVICE_KEY
from typing import List, Dict, Optional

class SupabaseDB:
    def __init__(self):
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    def insert_email(self, email_data: Dict) -> None:
        self.client.table('emails').upsert(email_data).execute()

    def insert_classification(self, classification_data: Dict) -> None:
        self.client.table('classifications').insert(classification_data).execute()

    def get_unclassified_emails(self) -> List[Dict]:
        response = self.client.table('emails') \
            .select('*') \
            .is_('classifications.id', 'null') \
            .execute()
        return response.data

    def get_stats(self) -> Dict:
        response = self.client.table('classification_summary') \
            .select('*') \
            .execute()
        return response.data
```

### Actualizar `config.py`:

```python
# Añadir al final
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# Modo de base de datos
DB_MODE = os.getenv("DB_MODE", "local")  # "local" o "supabase"
```

## Paso 7: Verificar

```bash
# Probar conexión
python -c "
from gmail_classifier.supabase_db import SupabaseDB
db = SupabaseDB()
print('✅ Conexión exitosa a Supabase')
"

# Ver estadísticas
python -m gmail_classifier.main stats --db=supabase
```

## Paso 8: Deploy (Opcional)

Una vez en Supabase, puedes desplegar en la nube:

### Google Cloud Function

```bash
cd cloud_function
gcloud functions deploy gmail_classifier \
    --runtime python311 \
    --trigger-http \
    --entry-point classify_emails \
    --set-env-vars SUPABASE_URL=xxx,SUPABASE_SERVICE_KEY=xxx,ANTHROPIC_API_KEY=xxx
```

### Vercel (Web App)

```bash
cd web
vercel --prod
# Configurar variables de entorno en Vercel Dashboard
```

## 💡 Tips

### Optimizar Costos

```sql
-- Ver tamaño de la base de datos
SELECT
    pg_size_pretty(pg_database_size(current_database())) as db_size;

-- Limpiar emails muy antiguos (>2 años)
DELETE FROM emails WHERE date < NOW() - INTERVAL '2 years';
```

### Backups

Supabase hace backups automáticos, pero puedes hacer backups manuales:

```bash
# Exportar a SQL
supabase db dump -f backup.sql

# Restaurar desde backup
psql -h db.xxxxx.supabase.co -U postgres -d postgres -f backup.sql
```

### Monitoreo

1. Dashboard de Supabase: Ver queries, uso de storage, etc.
2. Logs en tiempo real: Table Editor → Logs
3. Alertas: Configurar en Dashboard → Project Settings → Alerts

## 🔐 Seguridad en Producción

### 1. Habilitar Row Level Security (RLS)

```sql
-- Crear política para que users solo vean sus emails
CREATE POLICY "Users can only see their own emails"
ON emails
FOR SELECT
USING (auth.uid() = user_id);
```

### 2. No exponer Service Key

- ❌ NUNCA uses `SUPABASE_SERVICE_KEY` en frontend
- ✅ Usa `SUPABASE_ANON_KEY` en frontend
- ✅ Usa `SUPABASE_SERVICE_KEY` solo en backend/Cloud Functions

### 3. Validar Inputs

```python
# Siempre validar antes de insertar
def insert_email_safe(email_data):
    # Validar schema
    required_fields = ['message_id', 'subject', 'sender', 'date']
    for field in required_fields:
        if field not in email_data:
            raise ValueError(f"Missing field: {field}")

    # Sanitizar
    email_data['subject'] = email_data['subject'][:500]  # Limitar longitud

    # Insertar
    db.insert_email(email_data)
```

## 📊 Comparación: SQLite vs Supabase

| Característica | SQLite | Supabase |
|----------------|--------|----------|
| **Coste** | Gratis | Gratis (tier) |
| **Multi-usuario** | ❌ No | ✅ Sí |
| **Acceso remoto** | ❌ No | ✅ Sí |
| **Backups** | Manual | Automático |
| **Escalabilidad** | Limitada | Alta |
| **APIs** | No | REST + GraphQL |
| **Setup** | Simple | Media |
| **Offline** | ✅ Sí | ❌ No |

## ❓ Troubleshooting

**Error: "relation does not exist"**
→ Ejecuta las migraciones SQL del Paso 2

**Error: "Invalid API key"**
→ Verifica que copiaste correctamente las keys del Dashboard

**Lentitud en queries**
→ Añade índices:
```sql
CREATE INDEX idx_custom ON emails(your_column);
```

**Límite de storage**
→ En plan Free: 500MB. Considera:
- Limpiar emails antiguos
- No guardar attachments
- Upgrade a plan Pro ($25/mes)

## 🎯 Próximos Pasos

- [ ] Migrar datos existentes
- [ ] Probar conexión y queries
- [ ] Desplegar Cloud Function
- [ ] Configurar Web App
- [ ] Añadir autenticación multi-usuario
- [ ] Implementar analytics

---

**¿Necesitas ayuda?** Abre un issue en GitHub!
