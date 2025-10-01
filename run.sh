#!/bin/bash

# AgentForce Local Assistant - Launch Script
# Quick launcher that activates venv and starts the assistant

cd "$(dirname "$0")"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Lancement de l'assistant AgentForce...${NC}"

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✅ Environnement virtuel activé${NC}"
else
    echo -e "${RED}❌ Environnement virtuel non trouvé${NC}"
    echo -e "${RED}Exécutez d'abord: ./setup_agentforce.sh${NC}"
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo -e "${RED}❌ Ollama n'est pas en cours d'exécution${NC}"
    echo -e "${BLUE}Démarrage d'Ollama...${NC}"
    ollama serve > /tmp/ollama.log 2>&1 &
    sleep 3
    
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Ollama démarré${NC}"
    else
        echo -e "${RED}❌ Échec du démarrage d'Ollama${NC}"
        echo -e "${BLUE}Vérifiez les logs: tail -f /tmp/ollama.log${NC}"
    fi
fi

echo ""

# Launch the assistant
cd agent
python main.py
