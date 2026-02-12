#!/bin/bash
# Automatická synchronizace s GitHub

echo "📦 Synchronizace projektu s GitHub..."

# Přidání všech změn
git add .

# Kontrola, zda jsou nějaké změny
if git diff --staged --quiet; then
    echo "✅ Žádné změny k commitování"
else
    # Commit se současným timestampem
    git commit -m "Auto-update: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "✅ Změny commitovány"
fi

# Push na GitHub
git push origin main

echo "🚀 Synchronizace dokončena!"
