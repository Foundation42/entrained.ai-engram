# 🔑 OpenAI Setup for Memory Curation

## Quick Setup

1. **Set the API key** (export to environment):
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

Or create a `.env` file:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

2. **Start the server**:
```bash
python main.py
```

3. **Test the curation system**:
```bash
python test_memory_curation.py
```

## Configuration Details

### Model Used
- **Model**: `gpt-4.1-nano-2025-04-14`
- **Purpose**: Fast and cost-effective memory curation decisions
- **Temperature**: 0.1 (consistent decisions)
- **Max Tokens**: 1000 (sufficient for curation analysis)

### API Key Priority
The system looks for the OpenAI API key in this order:
1. `OPENAI_API_KEY` environment variable
2. `.env` file (`OPENAI_API_KEY=...`)
3. Settings configuration (`ENGRAM_OPENAI_API_KEY`)

### Fallback Behavior
If no API key is provided:
- ⚠️ Warning logged about missing API key
- 🔄 System uses conservative fallback decisions:
  - `should_store: true`
  - `storage_type: context`
  - `retention_policy: medium_term`
  - `confidence_score: 0.3`
  - `requires_review: true`

## Environment Variables

```bash
# Core memory curation
OPENAI_API_KEY=sk-proj-A72T5...
ENGRAM_OPENAI_CURATION_MODEL=gpt-4.1-nano-2025-04-14

# Optional Redis configuration
ENGRAM_REDIS_HOST=localhost
ENGRAM_REDIS_PORT=6379
ENGRAM_DEBUG=false
```

## Cost Estimation

With GPT-4.1-nano-2025-04-14:
- **Cost per curation**: ~$0.0001-0.0005
- **Expected volume**: 100-1000 curations/day
- **Monthly cost**: ~$3-15 (very affordable)

## Security Notes

🔒 **IMPORTANT**: Never commit the API key to Git!

The `set_openai_key.py` script:
- ✅ Sets environment variable for current session
- ✅ Creates `.env` file for persistence  
- ⚠️ Contains the actual API key (for convenience)
- 🚫 Should never be committed to Git

Add to `.gitignore`:
```
.env
set_openai_key.py
```

## Monitoring

Check if OpenAI integration is working:

```bash
# Health check
curl http://localhost:8000/health

# Test curation analysis
curl -X POST http://localhost:8000/cam/curated/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "My name is Christian",
    "agent_response": "Nice to meet you, Christian!",
    "conversation_context": "Initial introduction"
  }'
```

Expected response:
```json
{
  "should_store": true,
  "storage_type": "facts",
  "retention_policy": "permanent",
  "confidence_score": 0.95,
  "reasoning": "High-value factual information about user identity"
}
```

## Troubleshooting

### Issue: "No OpenAI API key provided"
```bash
# Solution 1: Run setup script
python set_openai_key.py

# Solution 2: Set environment variable manually
export OPENAI_API_KEY="sk-proj-A72T5..."

# Solution 3: Create .env file manually
echo "OPENAI_API_KEY=sk-proj-A72T5..." > .env
```

### Issue: "Model not found" or API errors
- ✅ Verify API key is valid
- ✅ Check model name: `gpt-4.1-nano-2025-04-14`
- ✅ Ensure sufficient API credits

### Issue: High API costs
- 📊 Monitor usage in OpenAI dashboard
- ⚙️ Adjust `retention_bias` to "conservative" 
- 🎯 Use `force_storage=false` for non-critical conversations

## Production Deployment

For production:

1. **Use environment variables**:
```bash
export OPENAI_API_KEY="your-production-key"
export ENGRAM_OPENAI_CURATION_MODEL="gpt-4.1-nano-2025-04-14"
```

2. **Monitor costs**:
   - Set up OpenAI billing alerts
   - Track usage with curation statistics: `GET /cam/curated/stats/{entity_id}`

3. **Rate limiting** (if needed):
   - OpenAI has generous rate limits for this model
   - Consider caching curation decisions for identical inputs

The memory curation system is now production-ready with OpenAI! 🚀