#!/bin/bash

# 🚀 Deploy Columbo Memory System to Production
# Run this script on the production server (46.62.130.230)

set -e  # Exit on any error

echo "🚀 Deploying Columbo Memory Curation System to Production"
echo "========================================================="

# 1. Check we're on the production server
if [[ $(hostname -I | grep -c "46.62.130.230") -eq 0 ]]; then
    echo "⚠️  Warning: This doesn't appear to be the production server"
    echo "Expected IP: 46.62.130.230"
    echo "Current IP: $(hostname -I)"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 2. Update repository
echo "📥 Pulling latest changes..."
git fetch origin
git checkout master
git pull origin master

# 3. Set OpenAI API key
echo "🔑 Setting up OpenAI API key..."
if [[ -z "$OPENAI_API_KEY" ]]; then
    echo "❌ OPENAI_API_KEY environment variable not set!"
    echo "Please set it before running this script:"
    echo "export OPENAI_API_KEY='your-key-here'"
    exit 1
fi

# Create .env file for persistence
cat > .env << EOF
# Engram Production Configuration
ENGRAM_DEBUG=false
ENGRAM_REDIS_HOST=localhost
ENGRAM_REDIS_PORT=6379

# OpenAI for memory curation
OPENAI_API_KEY=$OPENAI_API_KEY
ENGRAM_OPENAI_CURATION_MODEL=gpt-4.1-nano-2025-04-14
EOF

echo "✅ Environment configured"

# 4. Rebuild and restart containers
echo "🐳 Rebuilding Docker containers..."
docker compose down
docker compose up --build -d

# 5. Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# 6. Health check
echo "🏥 Running health check..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    echo "Checking container status:"
    docker compose ps
    echo "Checking logs:"
    docker compose logs --tail 20
    exit 1
fi

# 7. Test memory curation
echo "🧠 Testing memory curation..."
CURATION_TEST=$(curl -s -X POST http://localhost:8000/cam/curated/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "My name is Christian and I live in Liversedge",
    "agent_response": "Nice to meet you, Christian!",
    "conversation_context": "Deployment test"
  }')

if echo "$CURATION_TEST" | grep -q "Christian"; then
    echo "✅ Memory curation test passed"
else
    echo "❌ Memory curation test failed"
    echo "Response: $CURATION_TEST"
    exit 1
fi

# 8. Test weather filtering
echo "🌧️ Testing weather filtering..."
WEATHER_TEST=$(curl -s -X POST http://localhost:8000/cam/curated/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "It is raining today",
    "agent_response": "That is unfortunate about the weather.",
    "conversation_context": "Weather filtering test"
  }')

if echo "$WEATHER_TEST" | grep -q '"should_store":false'; then
    echo "✅ Weather filtering test passed"
else
    echo "❌ Weather filtering test failed"
    echo "Response: $WEATHER_TEST"
fi

# 9. Show deployment summary
echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================"
echo "✅ Production server: http://46.62.130.230:8000"
echo "✅ Health endpoint: http://46.62.130.230:8000/health"
echo "✅ Memory curation: AI-powered Columbo system active"
echo "✅ OpenAI integration: GPT-4.1-nano-2025-04-14"
echo "✅ Automatic cleanup: Scheduled daily/weekly/monthly"
echo ""
echo "📚 Agent Team Resources:"
echo "- Quick Start Guide: AGENT_TEAM_QUICK_START.md"
echo "- Full Documentation: AGENT_TEAM_MEMORY_CURATION.md"
echo "- Test Suite: python test_memory_curation.py"
echo "- Debug Tools: python agent_team_debug_query.py"
echo ""
echo "🔥 The Columbo Memory System is now LIVE! 🕵️‍♂️"