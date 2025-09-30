# 🤖 AgentForce Local Assistant

Agent IA conversationnel **100% local et gratuit** pour créer et déployer des **Lightning Types personnalisés** sur Salesforce.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Ollama](https://img.shields.io/badge/LLM-Llama_3.2-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Fonctionnalités

- 🎯 **Business Analyst IA** : Comprend vos besoins métier via conversation naturelle
- 📋 **Génération de Specs** : Crée des spécifications techniques détaillées
- 💻 **Génération de Code** : Génère automatiquement le code Lightning Type complet
- 📚 **Base de Connaissance Locale** : Documentation Salesforce intégrée avec RAG
- 🔄 **Vérification Auto des Docs** : Détecte les mises à jour de documentation
- 🚀 **Déploiement Automatisé** : Intégration complète avec Salesforce CLI
- 🧹 **Auto-cleanup** : Nettoyage automatique après déploiement réussi
- 🗣️ **Mode Verbose** : Visibilité complète sur chaque étape

## 🏗️ Architecture

```
AgentForce Local Assistant
│
├── 🧠 LLM Local (Ollama + Llama 3.2)
│   └── 100% gratuit, aucune API key requise
│
├── 📚 RAG Engine
│   ├── Documentation Salesforce (14 pages)
│   └── Recherche par similarité (TF-IDF + cosine)
│
├── 🎨 Interface CLI (Rich)
│   └── Conversational + Mode verbose
│
└── 🔧 Salesforce CLI Integration
    ├── Listing des orgs
    ├── Création de projet
    └── Déploiement automatisé
```

## 📋 Prérequis

- **Python 3.10+**
- **macOS** ou **Linux** (Windows via WSL)
- **Salesforce CLI** ([Installer](https://developer.salesforce.com/tools/sfdxcli))
- Au moins **4 GB RAM** pour Ollama
- Connexion Internet (pour le téléchargement initial)

## 🚀 Installation Rapide

### Étape 1 : Cloner le Repository

```bash
cd /Users/xlengelle/Code
git clone https://github.com/xlengelle-sf/agentforce-local-assistant.git AFRT2
cd AFRT2
```

### Étape 2 : Exécuter le Script d'Installation

```bash
chmod +x setup.sh
./setup.sh
```

Le script d'installation va :
- ✅ Vérifier Python 3.10+
- ✅ Installer Ollama (si nécessaire)
- ✅ Télécharger le modèle Llama 3.2 (~ 2 GB)
- ✅ Créer un environnement virtuel Python
- ✅ Installer toutes les dépendances
- ✅ Créer la structure de répertoires
- ✅ Générer la configuration par défaut

**Note**: Le téléchargement du modèle Llama 3.2 peut prendre 5-10 minutes selon votre connexion.

### Étape 3 : Authentifier une Org Salesforce (si pas déjà fait)

```bash
sf org login web -a monOrg
```

## 🎮 Utilisation

### Lancer l'Agent

```bash
source venv/bin/activate
python agent/main.py
```

### Workflow Interactif

L'agent vous guidera à travers **7 étapes** :

#### **1️⃣ Business Requirements Analysis**
Questions sur :
- Objet Salesforce cible
- But de l'affichage
- Champs clés
- Style visuel
- Fonctionnalités spéciales

#### **2️⃣ Technical Specification**
Génération automatique de :
- Nom du Lightning Type
- Structure de données
- Composants LWC requis
- Features à implémenter

#### **3️⃣ Documentation Verification**
- Vérification des mises à jour de documentation
- Option de re-téléchargement si nécessaire

#### **4️⃣ Code Generation**
Génération de :
- `schema.json`
- `renderer.json`
- Composant LWC (JS, HTML, meta.xml)

#### **5️⃣ Salesforce Project Creation**
- Création automatique d'un projet SFDX

#### **6️⃣ Code Implementation**
- Intégration du code dans la structure du projet

#### **7️⃣ Deployment**
- Listing des orgs disponibles
- Sélection de l'org cible
- Déploiement
- Vérification
- Cleanup automatique

## 📁 Structure du Projet

```
AFRT2/
├── agent/
│   ├── main.py                 # Point d'entrée principal
│   ├── llm_client.py           # Client Ollama
│   ├── doc_fetcher.py          # Téléchargement docs
│   ├── rag_engine.py           # Moteur RAG
│   ├── business_analyst.py     # Analyse besoin
│   ├── spec_generator.py       # Génération specs
│   ├── code_generator.py       # Génération code
│   └── sf_deployer.py          # Déploiement SF
├── knowledge_base/
│   ├── raw_docs/               # Docs HTML brutes
│   └── processed/              # Docs traitées (JSON)
├── config/
│   └── settings.json           # Configuration
├── projects/                   # Projets SF générés
├── setup.sh                    # Script d'installation
├── requirements.txt            # Dépendances Python
└── README.md                   # Cette documentation
```

## ⚙️ Configuration

Le fichier `config/settings.json` permet de configurer :

```json
{
  "llm": {
    "model": "llama3.2",
    "base_url": "http://localhost:11434",
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "verbose": true,
  "auto_cleanup": true,
  "docs_urls": [...]
}
```

- **verbose**: `true` pour voir toutes les étapes en détail
- **auto_cleanup**: `true` pour nettoyer le projet après déploiement réussi
- **temperature**: 0.0-1.0 (créativité du modèle)

## 🔧 Commandes Utiles

### Relancer Ollama manuellement

```bash
ollama serve
```

### Lister les modèles installés

```bash
ollama list
```

### Télécharger un autre modèle

```bash
ollama pull mistral  # Alternative à Llama 3.2
```

### Vérifier les orgs Salesforce

```bash
sf org list
```

### Nettoyer manuellement

```bash
rm -rf projects/*
```

## 🐛 Troubleshooting

### Problème : "Ollama not found"

```bash
# Installer Ollama manuellement
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
```

### Problème : "Salesforce CLI not found"

```bash
# Installer SF CLI
npm install -g @salesforce/cli
# Ou via Homebrew sur macOS
brew install salesforce-cli
```

### Problème : "Module not found"

```bash
# Réinstaller les dépendances
pip install -r requirements.txt
```

### Problème : "Deployment failed"

1. Vérifier que l'org est authentifiée : `sf org display -o monOrg`
2. Vérifier les permissions sur l'org
3. Relancer avec `verbose: true` pour plus de détails

## 📊 Performance

- **Initialisation** : ~10 secondes
- **Téléchargement docs** (première fois) : ~1 minute
- **Analyse besoin** : ~5 questions interactives
- **Génération spec** : ~10 secondes
- **Génération code** : ~20-30 secondes
- **Déploiement** : ~30-60 secondes

**Total** : ~2-3 minutes pour un Lightning Type complet

## 🎯 Exemples d'Utilisation

### Cas 1 : Hotel Booking Display

```
Object: Hotel_Booking__c
Purpose: Display booking details with timeline
Key Fields: Name, Status__c, Check_in_Date__c, Customer_Name__c
Visual Style: Card with timeline
Features: Status badges, progress indicator
```

### Cas 2 : Product Catalog

```
Object: Product2
Purpose: Rich product card display
Key Fields: Name, Description, Price, Stock_Quantity
Visual Style: Card layout
Features: Image display, stock indicator, price badge
```

## 🤝 Contributing

Les contributions sont les bienvenues ! N'hésitez pas à :
- Ouvrir des issues pour bugs ou suggestions
- Proposer des pull requests
- Partager vos cas d'usage

## 📝 License

MIT License - voir le fichier [LICENSE](LICENSE)

## 🙏 Remerciements

- **Ollama** pour le runtime LLM local
- **Meta** pour Llama 3.2
- **Salesforce** pour la documentation complète
- **Rich** pour l'interface CLI élégante

## 📞 Support

- 📧 Email: xlengelle@salesforce.com
- 🐛 Issues: [GitHub Issues](https://github.com/xlengelle-sf/agentforce-local-assistant/issues)

---

**Développé avec ❤️ par Xavier Lengelle**

*Powered by Llama 3.2 🦙 • 100% Local • 100% Gratuit*
