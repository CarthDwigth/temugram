#!/bin/bash
# Script para subir cambios a TemuGram automáticamente

echo "🚀 Iniciando subida a GitHub..."

# Añade todos los cambios
git add .

# Crea el commit con un mensaje que incluya la fecha y hora
git commit -m "Actualización automática: $(date +'%d/%m/%Y %H:%M')"

# Sube los cambios (como ya pusiste el helper store, no pedirá token)
git push

echo "✅ ¡Todo listo! Render empezará a actualizarse en un momento."

