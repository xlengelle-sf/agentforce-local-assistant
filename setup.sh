#!/bin/bash

echo "==================================="
echo "AgentForce Local Assistant - Setup"
echo "==================================="
echo ""

# Check if Python 3.10+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python $PYTHON_VERSION detected"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo ""
    echo "📥 Installing Ollama..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        curl -fsSL https://ollama.com/install.sh | sh
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -fsSL https://ollama.com/install.sh | sh
    else
        echo "❌ Unsupported OS. Please install Ollama manually from https://ollama.com"
        exit 1
    fi
else
    echo "✅ Ollama already installed"
fi

# Start Ollama service
echo ""
echo "🚀 Starting Ollama service..."
ollama serve > /dev/null 2>&1 &
sleep 3

# Pull Llama 3.2 model
echo ""
echo "📦 Downloading Llama 3.2 model (this may take a few minutes)..."
ollama pull llama3.2

# Create virtual environment
echo ""
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "📁 Creating project directories..."
mkdir -p knowledge_base/raw_docs
mkdir -p knowledge_base/processed
mkdir -p config
mkdir -p projects

# Create default config
echo ""
echo "⚙️  Creating default configuration..."
cat > config/settings.json << EOF
{
  "llm": {
    "model": "llama3.2",
    "base_url": "http://localhost:11434",
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "verbose": true,
  "auto_cleanup": true,
  "docs_urls": [
    "https://developer.salesforce.com/docs/einstein/genai/guide/lightning-types.html",
    "https://developer.salesforce.com/docs/einstein/genai/guide/lightning-types-get-started.html",
    "https://developer.salesforce.com/docs/einstein/genai/guide/lightning-types-standard.html",
    "https://developer.salesforce.com/docs/einstein/genai/guide/lightning-types-custom.html",
    "https://developer.salesforce.com/docs/einstein/genai/guide/lightning-types-custom-schema.html",
    "https://developer.salesforce.com/docs/einstein/genai/guide/lightning-types-custom-editor.html",
    "https://developer.salesforce.com/docs/einstein/genai/guide/lightning-types-custom-renderer.html",
    "https://developer.salesforce.com/docs/einstein/genai/guide/lightning-types-setup.html",
    "https://developer.salesforce.com/docs/einstein/genai/guide/lightning-types-examples.html",
    "https://developer.salesforce.com/docs/einstein/genai/guide/lightning-types-example-full-editor-renderer.html",
    "https://developer.salesforce.com/docs/einstein/genai/guide/lightning-types-example-collection-renderer.html",
    "https://developer.salesforce.com/docs/einstein/genai/guide/lightning-types-references.html",
    "https://developer.salesforce.com/docs/einstein/genai/guide/agents-metadata-tooling.html",
    "https://developer.salesforce.com/docs/einstein/genai/guide/agent-dx.html"
  ]
}
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the agent, run:"
echo "  source venv/bin/activate"
echo "  python agent/main.py"
echo ""
