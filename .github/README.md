# GitHub Configuration

Este directorio contiene la configuración de GitHub para el proyecto Gmail AI Classifier.

## Workflows (GitHub Actions)

### 🔒 Security Check (`security-check.yml`)

**Ejecuta:** En cada push a main/develop y en pull requests

**Verifica:**
- ✅ No hay API keys o secrets hardcodeados en el código
- ✅ No hay archivos sensibles (credentials.json, .env) en el repositorio
- ✅ El .gitignore está correctamente configurado
- ✅ Vulnerabilidades en dependencias Python (usando Safety)
- ✅ Análisis de seguridad del código (usando Bandit)

**Estado:**
- ✅ Verde = Todo seguro
- ⚠️ Amarillo = Vulnerabilidades menores encontradas
- ❌ Rojo = Problemas de seguridad críticos

## Secrets Configurados

Los siguientes secrets están configurados en el repositorio para uso en workflows:

| Secret | Propósito | Requerido |
|--------|-----------|-----------|
| `ANTHROPIC_API_KEY` | API key de Claude AI | ✅ Sí |
| `ANTHROPIC_MODEL` | Modelo de Claude a usar | ⚠️ Opcional |
| `SUPABASE_URL` | URL de Supabase (para cloud) | ⚠️ Solo para cloud |
| `SUPABASE_ANON_KEY` | Key pública de Supabase | ⚠️ Solo para cloud |
| `SUPABASE_SERVICE_KEY` | Key de servicio de Supabase | ⚠️ Solo para cloud |

### Ver secrets configurados

```bash
gh secret list
```

### Añadir un nuevo secret

```bash
# Interactivo (te pedirá el valor)
gh secret set NOMBRE_DEL_SECRET

# O desde un archivo
gh secret set NOMBRE_DEL_SECRET < valor.txt

# O desde stdin
echo "valor-secreto" | gh secret set NOMBRE_DEL_SECRET
```

### Eliminar un secret

```bash
gh secret remove NOMBRE_DEL_SECRET
```

## Badges para el README

Puedes añadir badges al README para mostrar el estado de los workflows:

```markdown
[![Security Check](https://github.com/alyusva/gmail-ai-classifier/workflows/Security%20Check/badge.svg)](https://github.com/alyusva/gmail-ai-classifier/actions)
```

## Issue Templates (Próximamente)

Plantillas para facilitar la creación de issues:
- Bug report
- Feature request
- Security vulnerability
- Question

## Pull Request Template (Próximamente)

Plantilla para estandarizar pull requests con:
- Descripción del cambio
- Checklist de revisión
- Tests realizados
- Screenshots (si aplica)

---

**Última actualización:** Marzo 2026
