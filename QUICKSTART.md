# 🚀 Guide Démarrage Rapide - AgentForce Local Assistant

Guide ultra-simple pour utiliser le code depuis GitHub.

---

## 📦 Prérequis

- Python 3.10 ou supérieur
- Salesforce CLI installé
- Ollama installé (pour l'IA locale)
- Git

---

## ⚡ Installation (5 minutes)

### Option A : Installation Automatique (Recommandé)

```bash
curl -o setup_agentforce.sh https://raw.githubusercontent.com/xlengelle-sf/agentforce-local-assistant/main/setup_agentforce.sh
chmod +x setup_agentforce.sh
./setup_agentforce.sh
```

Le script interactif vous guidera à travers toutes les étapes.

---

### Option B : Installation Manuelle

#### 1. Cloner le repository

```bash
cd ~/Code
git clone https://github.com/xlengelle-sf/agentforce-local-assistant.git
cd agentforce-local-assistant
```

#### 2. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

#### 3. Installer Ollama (si pas déjà fait)

**macOS:**
```bash
brew install ollama
ollama serve &
ollama pull llama3.2
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull llama3.2
```

#### 4. Télécharger la documentation Salesforce

```bash
cd agent
python -c "from knowledge_base_manager import KnowledgeBaseManager; KnowledgeBaseManager().initialize()"
```

---

## 🎯 Utilisation

### Lancer l'assistant

```bash
cd agent
python main.py
```

### Exemple de session complète

```
$ python main.py

╔══════════════════════════════════════════════════╗
║   🤖  AgentForce Local Assistant                ║
╚══════════════════════════════════════════════════╝

🎯 Select Working Mode

1. Conversational Mode
2. Object Discovery Mode ⭐ (Recommandé)

Choose mode [1/2]: 2

────────────────────────────────────
Step 1/6: Select Salesforce Org
────────────────────────────────────

Available orgs:
1. MySandbox (username@sandbox.com)
2. MyDevOrg (username@dev.com)

Select org [1-2]: 1

────────────────────────────────────
Step 2/6: Loading Objects
────────────────────────────────────

Found 287 objects

────────────────────────────────────
Step 3/6: Select Object
────────────────────────────────────

Search: Account

Results:
1. Account - Customer Account
2. AccountBrand - Account Brand

Select object [1-2]: 1

────────────────────────────────────
Step 4/6: Select Fields
────────────────────────────────────

💡 AI Recommendations: Name, Phone, Industry, AnnualRevenue

Available fields:
[ ] 1. Id
[⭐] 2. Name
[ ] 3. Phone
[ ] 4. Industry
...

Select fields [1,2,3 or 'ai']: ai

✅ Using AI recommendations

────────────────────────────────────
Step 5/6: Preview
────────────────────────────────────

Component: accountViewer
Object: Account
Fields: Name, Phone, Industry, AnnualRevenue

Confirm? [Y/n]: Y

────────────────────────────────────
Step 6/6: Deploy
────────────────────────────────────

✅ Code generated: force-app/main/default/lwc/accountViewer/
✅ Deployed to MySandbox
🎉 Done!
```

---

## 📝 Commandes Utiles

### Voir les objets disponibles dans votre org

```bash
sf sobject list --sobject all --target-org YOUR_ORG_ALIAS
```

### Vider le cache des objets

```bash
rm -rf knowledge_base/object_cache/*
```

### Re-télécharger la documentation

```bash
cd agent
python -c "from knowledge_base_manager import KnowledgeBaseManager; KnowledgeBaseManager().initialize(force=True)"
```

### Tester la connexion Ollama

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Hello",
  "stream": false
}'
```

---

## 🐛 Problèmes Courants

### "Ollama is not running"

```bash
ollama serve &
sleep 5
ollama pull llama3.2
```

### "Salesforce CLI not found"

```bash
# Installer SF CLI
npm install -g @salesforce/cli
sf --version
```

### "No org found"

```bash
# Authentifier un org
sf org login web --alias MySandbox
```

---

## 🎯 Workflow Simplifié

```
1. Cloner le repo
   ↓
2. pip install -r requirements.txt
   ↓
3. python main.py
   ↓
4. Choisir mode 2 (Object Discovery)
   ↓
5. Sélectionner org, objet, champs
   ↓
6. Confirmer et déployer
   ↓
7. ✅ Component créé !
```

---

## 📚 Structure du Projet

```
agentforce-local-assistant/
├── agent/
│   ├── main.py                  ← Point d'entrée
│   ├── object_discoverer.py     ← Découverte d'objets SF
│   ├── code_generator.py        ← Génération de LWC
│   └── knowledge_base_manager.py
├── knowledge_base/              ← Documentation SF
├── config/                      ← Configuration
└── force-app/                   ← Code SF généré
```

---

## ✨ C'est tout !

Ton assistant local est prêt à générer des Lightning Web Components pour AgentForce.

Questions ? Ouvre une issue sur GitHub.
