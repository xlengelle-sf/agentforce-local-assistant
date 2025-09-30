#!/bin/bash

# AgentForce Local Assistant - Interactive Setup Script
# Author: Xavier Lengellé
# Description: Script interactif pour installer et configurer l'assistant local

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emojis
CHECK="✅"
CROSS="❌"
ARROW="➜"
ROCKET="🚀"
WRENCH="🔧"
PACKAGE="📦"
QUESTION="❓"
WAIT="⏳"

# Function to print colored messages
print_header() {
    echo -e "\n${PURPLE}════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}  $1${NC}"
    echo -e "${PURPLE}════════════════════════════════════════════════${NC}\n"
}

print_step() {
    echo -e "${CYAN}${ARROW} $1${NC}"
}

print_success() {
    echo -e "${GREEN}${CHECK} $1${NC}"
}

print_error() {
    echo -e "${RED}${CROSS} $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}${QUESTION} $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to ask yes/no question
ask_confirmation() {
    local question="$1"
    local default="${2:-y}"
    
    if [ "$default" = "y" ]; then
        prompt="[Y/n]"
    else
        prompt="[y/N]"
    fi
    
    while true; do
        echo -ne "${YELLOW}${QUESTION} ${question} ${prompt}: ${NC}"
        read -r response
        
        # Use default if empty
        if [ -z "$response" ]; then
            response="$default"
        fi
        
        case "${response,,}" in
            y|yes|o|oui) return 0 ;;
            n|no|non) return 1 ;;
            *) echo -e "${RED}Réponse invalide. Utilisez Y ou N.${NC}" ;;
        esac
    done
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main installation directory
INSTALL_DIR="$HOME/Code/agentforce-local-assistant"

# ============================================================
# WELCOME
# ============================================================
clear
echo -e "${PURPLE}"
cat << "EOF"
    ___                  __  ______                 
   /   | ____ ____  ____/ /_/ ____/___  _________ 
  / /| |/ __ `/ _ \/ __  / /___ \/ __ \/ ___/ __ \
 / ___ / /_/ /  __/ /_/ / ____/ / /_/ / /  / /_/ /
/_/  |_\__, /\___/\__,_/ /_____/\____/_/   \____/ 
      /____/                                       
       
   Local Assistant - Installation Interactive
EOF
echo -e "${NC}"

print_info "Ce script va installer et configurer l'assistant local AgentForce."
print_info "Vous serez invité à confirmer chaque étape importante."
echo ""

if ! ask_confirmation "Voulez-vous continuer avec l'installation" "y"; then
    print_warning "Installation annulée."
    exit 0
fi

# ============================================================
# STEP 1: Check Prerequisites
# ============================================================
print_header "${PACKAGE} ÉTAPE 1/6 : Vérification des Prérequis"

print_step "Vérification de Python 3.10+..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        print_success "Python $PYTHON_VERSION détecté"
    else
        print_error "Python 3.10+ requis. Version actuelle: $PYTHON_VERSION"
        print_info "Installez Python 3.10+ depuis https://www.python.org/"
        exit 1
    fi
else
    print_error "Python 3 non trouvé"
    print_info "Installez Python 3.10+ depuis https://www.python.org/"
    exit 1
fi

print_step "Vérification de Git..."
if command_exists git; then
    GIT_VERSION=$(git --version | cut -d' ' -f3)
    print_success "Git $GIT_VERSION détecté"
else
    print_error "Git non trouvé"
    print_info "Installez Git: brew install git (macOS) ou apt install git (Linux)"
    exit 1
fi

print_step "Vérification de Salesforce CLI..."
if command_exists sf; then
    SF_VERSION=$(sf --version | head -n1)
    print_success "Salesforce CLI détecté: $SF_VERSION"
else
    print_warning "Salesforce CLI non trouvé"
    if ask_confirmation "Voulez-vous l'installer maintenant" "y"; then
        print_step "Installation de Salesforce CLI..."
        npm install -g @salesforce/cli
        print_success "Salesforce CLI installé"
    else
        print_error "Salesforce CLI requis pour continuer"
        exit 1
    fi
fi

print_step "Vérification de Ollama..."
if command_exists ollama; then
    print_success "Ollama détecté"
    OLLAMA_INSTALLED=true
else
    print_warning "Ollama non trouvé"
    OLLAMA_INSTALLED=false
fi

# ============================================================
# STEP 2: Clone Repository
# ============================================================
print_header "${PACKAGE} ÉTAPE 2/6 : Clonage du Repository"

if [ -d "$INSTALL_DIR" ]; then
    print_warning "Le répertoire $INSTALL_DIR existe déjà"
    
    if ask_confirmation "Voulez-vous le mettre à jour (git pull)" "y"; then
        print_step "Mise à jour du repository..."
        cd "$INSTALL_DIR"
        git pull origin main
        print_success "Repository mis à jour"
    else
        print_info "Utilisation du repository existant"
    fi
else
    if ask_confirmation "Cloner le repository dans $INSTALL_DIR" "y"; then
        print_step "Clonage du repository..."
        mkdir -p "$HOME/Code"
        cd "$HOME/Code"
        git clone https://github.com/xlengelle-sf/agentforce-local-assistant.git
        print_success "Repository cloné"
    else
        print_error "Repository requis pour continuer"
        exit 1
    fi
fi

cd "$INSTALL_DIR"

# ============================================================
# STEP 3: Install Python Dependencies
# ============================================================
print_header "${PACKAGE} ÉTAPE 3/6 : Installation des Dépendances Python"

if ask_confirmation "Installer les dépendances Python (pip)" "y"; then
    print_step "Installation des packages Python..."
    
    # Check if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Dépendances Python installées"
    else
        print_warning "requirements.txt non trouvé, installation manuelle..."
        pip install ollama rich
        print_success "Packages de base installés"
    fi
else
    print_warning "Étape ignorée - assurez-vous que les dépendances sont installées"
fi

# ============================================================
# STEP 4: Install and Configure Ollama
# ============================================================
print_header "${WRENCH} ÉTAPE 4/6 : Configuration de Ollama"

if [ "$OLLAMA_INSTALLED" = false ]; then
    if ask_confirmation "Installer Ollama maintenant" "y"; then
        print_step "Installation de Ollama..."
        
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            if command_exists brew; then
                brew install ollama
            else
                print_error "Homebrew non trouvé. Installez-le depuis https://brew.sh/"
                exit 1
            fi
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            curl -fsSL https://ollama.com/install.sh | sh
        else
            print_error "OS non supporté pour l'installation automatique"
            print_info "Installez Ollama manuellement: https://ollama.com/"
            exit 1
        fi
        
        print_success "Ollama installé"
    else
        print_error "Ollama requis pour continuer"
        exit 1
    fi
fi

# Check if Ollama is running
print_step "Vérification du service Ollama..."
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    print_success "Ollama est déjà en cours d'exécution"
else
    print_warning "Ollama n'est pas en cours d'exécution"
    
    if ask_confirmation "Démarrer Ollama en arrière-plan" "y"; then
        print_step "Démarrage d'Ollama..."
        ollama serve > /tmp/ollama.log 2>&1 &
        sleep 3
        
        if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            print_success "Ollama démarré"
        else
            print_error "Échec du démarrage d'Ollama"
            print_info "Vérifiez les logs: tail -f /tmp/ollama.log"
            exit 1
        fi
    fi
fi

# Download Llama model
print_step "Vérification du modèle Llama 3.2..."
if ollama list | grep -q "llama3.2"; then
    print_success "Modèle llama3.2 déjà téléchargé"
else
    print_warning "Modèle llama3.2 non trouvé"
    
    if ask_confirmation "Télécharger llama3.2 (~2GB)" "y"; then
        print_step "Téléchargement de llama3.2 (cela peut prendre quelques minutes)..."
        print_info "${WAIT} Veuillez patienter..."
        ollama pull llama3.2
        print_success "Modèle llama3.2 téléchargé"
    else
        print_warning "Le modèle sera nécessaire pour utiliser l'assistant"
    fi
fi

# ============================================================
# STEP 5: Initialize Knowledge Base
# ============================================================
print_header "${PACKAGE} ÉTAPE 5/6 : Initialisation de la Base de Connaissances"

if ask_confirmation "Télécharger la documentation Salesforce" "y"; then
    print_step "Téléchargement et indexation de la documentation..."
    print_info "${WAIT} Cette étape peut prendre 2-3 minutes..."
    
    cd agent
    python3 -c "from knowledge_base_manager import KnowledgeBaseManager; KnowledgeBaseManager().initialize()" || {
        print_error "Échec de l'initialisation de la base de connaissances"
        print_info "Vous pourrez réessayer plus tard avec la commande fournie dans le guide"
    }
    cd ..
    
    print_success "Base de connaissances initialisée"
else
    print_warning "Vous devrez initialiser la base de connaissances plus tard"
    print_info "Commande: cd agent && python3 -c \"from knowledge_base_manager import KnowledgeBaseManager; KnowledgeBaseManager().initialize()\""
fi

# ============================================================
# STEP 6: Verify Installation
# ============================================================
print_header "${CHECK} ÉTAPE 6/6 : Vérification de l'Installation"

print_step "Vérification des composants..."

all_good=true

# Check Python
if command_exists python3; then
    print_success "Python: OK"
else
    print_error "Python: MANQUANT"
    all_good=false
fi

# Check Git
if command_exists git; then
    print_success "Git: OK"
else
    print_error "Git: MANQUANT"
    all_good=false
fi

# Check SF CLI
if command_exists sf; then
    print_success "Salesforce CLI: OK"
else
    print_error "Salesforce CLI: MANQUANT"
    all_good=false
fi

# Check Ollama
if command_exists ollama; then
    print_success "Ollama: OK"
else
    print_error "Ollama: MANQUANT"
    all_good=false
fi

# Check Ollama service
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    print_success "Service Ollama: OK"
else
    print_warning "Service Ollama: NON DÉMARRÉ"
fi

# Check repository
if [ -d "$INSTALL_DIR/agent" ]; then
    print_success "Repository: OK"
else
    print_error "Repository: MANQUANT"
    all_good=false
fi

echo ""

if [ "$all_good" = true ]; then
    print_success "Installation terminée avec succès! ${ROCKET}"
    echo ""
    print_header "🎯 PROCHAINES ÉTAPES"
    echo ""
    echo -e "${GREEN}Pour lancer l'assistant:${NC}"
    echo -e "  cd $INSTALL_DIR/agent"
    echo -e "  python3 main.py"
    echo ""
    echo -e "${BLUE}Pour plus d'informations, consultez le guide:${NC}"
    echo -e "  $INSTALL_DIR/QUICKSTART.md"
    echo ""
else
    print_error "Installation incomplète - certains composants sont manquants"
    echo ""
    print_info "Vérifiez les erreurs ci-dessus et réexécutez le script"
fi

# Optional: Launch the assistant
echo ""
if ask_confirmation "Voulez-vous lancer l'assistant maintenant" "n"; then
    cd "$INSTALL_DIR/agent"
    python3 main.py
fi

print_success "Script terminé!"
