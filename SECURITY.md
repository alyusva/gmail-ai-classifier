# 🔒 Security Policy

## Archivos Sensibles

Este proyecto maneja información sensible que **NUNCA debe ser commiteada** a Git:

### ❌ NO subir a Git

| Archivo | Contenido | Protección |
|---------|-----------|------------|
| `.env` | API keys (Anthropic, Supabase) | ✅ En `.gitignore` |
| `credentials.json` | OAuth credentials de Google | ✅ En `.gitignore` |
| `data/token.json` | Token OAuth generado | ✅ En `.gitignore` |
| `data/*.db` | Base de datos SQLite con emails | ✅ En `.gitignore` |

### ✅ Sí incluir en Git

| Archivo | Propósito |
|---------|-----------|
| `.env.example` | Template sin datos reales |
| `.gitignore` | Configuración de archivos ignorados |
| `README.md` | Documentación pública |

## Configuración Segura

### 1. Variables de Entorno (Local)

```bash
# Copia el template
cp .env.example .env

# Edita con tus credenciales reales
nano .env

# Verifica que .env está en .gitignore
git status  # NO debe aparecer .env
```

### 2. GitHub Secrets (CI/CD)

Para configurar secrets en tu repositorio de GitHub:

#### Usando GitHub CLI (Recomendado)

```bash
# Anthropic API Key
gh secret set ANTHROPIC_API_KEY --body "sk-ant-api03-..."

# Supabase (si usas la versión cloud)
gh secret set SUPABASE_URL --body "https://xxx.supabase.co"
gh secret set SUPABASE_ANON_KEY --body "eyJhbGciOiJIUzI1NiI..."
gh secret set SUPABASE_SERVICE_KEY --body "eyJhbGciOiJIUzI1NiI..."

# Listar secrets configurados
gh secret list
```

#### Usando la interfaz web de GitHub

1. Ve a tu repositorio en GitHub
2. Settings → Secrets and variables → Actions
3. Click en "New repository secret"
4. Añade cada secret manualmente

### 3. Google OAuth Credentials

El archivo `credentials.json` contiene credenciales OAuth pero **no son secretas** en el sentido tradicional:

- ✅ Es seguro compartirlas en un contexto controlado (no público)
- ⚠️ **NO las subas a un repositorio público**
- ✅ Usa "Desktop app" OAuth (no "Web application")
- ✅ Google Cloud Console permite limitar el uso por dominio

**¿Cómo proteger?**

1. Ya está en `.gitignore` ✅
2. Si alguien las obtiene, solo pueden usarlas con autorización del usuario
3. Puedes revocar y regenerar en Google Cloud Console en cualquier momento

## Mejores Prácticas

### ✅ Hacer

- Usa `.env` para todas las credenciales locales
- Rota tus API keys periódicamente
- Revoca tokens OAuth si sospechas compromiso
- Usa diferentes API keys para desarrollo y producción
- Revisa el historial de git antes de hacer público un repositorio privado

### ❌ NO hacer

- Nunca hagas hardcode de API keys en el código
- No compartas tu `.env` por email o chat
- No subas screenshots que muestren variables de entorno
- No uses la misma API key en múltiples proyectos
- No ignores warnings de "secrets detected" en git

## Verificación de Seguridad

Antes de hacer push a un repositorio público, verifica:

```bash
# 1. Verifica que archivos sensibles estén en .gitignore
cat .gitignore | grep -E "(\.env|credentials|token)"

# 2. Verifica que NO estén trackeados en git
git ls-files | grep -E "(\.env|credentials\.json|token\.json)" || echo "✅ Ningún archivo sensible trackeado"

# 3. Verifica el historial (por si acaso)
git log --all --full-history --oneline -- credentials.json .env

# 4. Busca posibles secrets hardcodeados
grep -r "sk-ant-api" --exclude-dir=venv --exclude-dir=.git --exclude="*.md"
grep -r "GOCSPX-" --exclude-dir=venv --exclude-dir=.git --exclude="*.md"
```

Si encuentras algo en el historial de git:

```bash
# ⚠️ SOLO si es necesario - reescribe el historial
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch credentials.json' \
  --prune-empty --tag-name-filter cat -- --all

# Luego, forzar push (CUIDADO)
git push origin --force --all
```

## Reportar Vulnerabilidades

Si encuentras una vulnerabilidad de seguridad:

1. **NO abras un issue público**
2. Envía un email a: [tu-email@ejemplo.com]
3. Incluye:
   - Descripción del problema
   - Pasos para reproducir
   - Impacto potencial
   - Sugerencias de solución (opcional)

Responderé en menos de 48 horas.

## Permisos OAuth de Gmail

Este proyecto solicita los siguientes permisos:

| Permiso | Propósito | Riesgo |
|---------|-----------|--------|
| `gmail.readonly` | Leer metadata de emails (remitente, asunto, fecha) | ✅ Bajo - Solo lectura |
| `gmail.modify` | Modificar etiquetas de emails | ⚠️ Medio - Puede cambiar etiquetas |
| `gmail.labels` | Crear y gestionar etiquetas | ⚠️ Medio - Solo etiquetas |

**NO solicitamos:**
- ❌ `gmail.compose` - Enviar emails
- ❌ Acceso completo a Gmail
- ❌ Permiso para eliminar emails

## Auditoría de Dependencias

```bash
# Verifica vulnerabilidades en paquetes Python
pip install safety
safety check

# Actualiza paquetes con vulnerabilidades conocidas
pip install --upgrade google-api-python-client anthropic
```

## Licencia y Responsabilidad

Este software se proporciona "tal cual", sin garantías. El usuario es responsable de:

- Mantener seguras sus credenciales
- Cumplir con los términos de servicio de Gmail y Anthropic
- Proteger los datos de emails según GDPR/CCPA si aplica
- Usar el software de manera ética y legal

---

**Última actualización**: Marzo 2026
