-- ============================================================
-- Gmail AI Classifier - Schema inicial para Supabase
-- Ejecutar en: Supabase Dashboard → SQL Editor → New query
-- ============================================================

-- ============================================================
-- TABLA: emails
-- Almacena la metadata de los emails extraídos de Gmail
-- ============================================================
CREATE TABLE IF NOT EXISTS emails (
    id             TEXT PRIMARY KEY,            -- Gmail message ID
    thread_id      TEXT,
    subject        TEXT,
    sender         TEXT,
    sender_email   TEXT,
    snippet        TEXT,
    date           TEXT,
    labels_original TEXT[],                     -- Etiquetas originales de Gmail
    is_read        BOOLEAN DEFAULT FALSE,
    extracted_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABLA: classifications
-- Resultado de la clasificación con Claude
-- ============================================================
CREATE TABLE IF NOT EXISTS classifications (
    email_id       TEXT PRIMARY KEY REFERENCES emails(id) ON DELETE CASCADE,
    labels         TEXT[],                      -- Categorías asignadas (array)
    confidence     REAL DEFAULT 0.0,
    classified_at  TIMESTAMPTZ DEFAULT NOW(),
    applied        BOOLEAN DEFAULT FALSE,
    applied_at     TIMESTAMPTZ
);

-- ============================================================
-- TABLA: taxonomy
-- Mapeo label → Gmail label ID (se rellena al aplicar etiquetas)
-- ============================================================
CREATE TABLE IF NOT EXISTS taxonomy (
    label          TEXT PRIMARY KEY,
    gmail_label_id TEXT DEFAULT '',
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABLA: progress
-- Claves de progreso para reanudar operaciones interrumpidas
-- ============================================================
CREATE TABLE IF NOT EXISTS progress (
    key        TEXT PRIMARY KEY,
    value      TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ÍNDICES para mejorar rendimiento
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_emails_date
    ON emails(date DESC);

CREATE INDEX IF NOT EXISTS idx_emails_sender_email
    ON emails(sender_email);

CREATE INDEX IF NOT EXISTS idx_classifications_applied
    ON classifications(applied);

-- ============================================================
-- ROW LEVEL SECURITY
-- Por defecto deshabilitado para uso personal (un solo usuario).
-- Habilitar y configurar políticas cuando se implemente multi-usuario.
-- ============================================================
ALTER TABLE emails DISABLE ROW LEVEL SECURITY;
ALTER TABLE classifications DISABLE ROW LEVEL SECURITY;
ALTER TABLE taxonomy DISABLE ROW LEVEL SECURITY;
ALTER TABLE progress DISABLE ROW LEVEL SECURITY;

-- ============================================================
-- VISTA: resumen por categoría
-- ============================================================
CREATE OR REPLACE VIEW classification_summary AS
SELECT
    label,
    COUNT(*) AS email_count
FROM (
    SELECT UNNEST(labels) AS label
    FROM classifications
) sub
GROUP BY label
ORDER BY email_count DESC;
