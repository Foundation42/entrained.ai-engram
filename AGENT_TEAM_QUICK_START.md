# 🚀 Agent Team Quick Start - Columbo Memory System

## 🎯 What Changed

Engram now uses **Detective Columbo-style memory curation** - the AI observes EVERYTHING and scores each piece of information, then our business logic decides what to store.

### ✅ **Benefits for Agents**
- **Higher Quality Memories**: No more weather comments or "I don't know" responses
- **Multiple Extractions**: Single conversation → Multiple categorized memories
- **Smart Filtering**: Ephemeral info (weather, mood) automatically filtered out
- **Better Context**: Each memory has confidence, privacy, and value scores

---

## 🔥 **READY TO USE - NO CHANGES NEEDED**

**Good news**: Your existing agent code will work perfectly! The new system is backward compatible.

### Current Endpoints Still Work:
```bash
POST /cam/multi/store     # ✅ Still works
POST /cam/multi/retrieve  # ✅ Still works  
GET  /cam/multi/memory/{id}  # ✅ Still works
```

### New Endpoints Available:
```bash
POST /cam/curated/analyze    # 🆕 Analyze before storing
POST /cam/curated/store      # 🆕 Store with AI curation
POST /cam/curated/retrieve   # 🆕 Intelligent retrieval
GET  /cam/curated/stats/{id} # 🆕 Curation statistics
```

---

## 🧪 **Test It Right Now**

### 1. **Quick Health Check**
```bash
curl http://46.62.130.230:8000/health
# Should show: "status": "healthy"
```

### 2. **Test Memory Curation**
```bash
curl -X POST http://46.62.130.230:8000/cam/curated/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "My name is Christian and I live in Liversedge. It'\''s raining today.",
    "agent_response": "Nice to meet you, Christian! I'\''ll remember you live in Liversedge.",
    "conversation_context": "Introduction with weather comment"
  }'
```

**Expected Result**: You'll see the AI extract Christian's name and location (high value, low ephemerality) but filter out the weather comment (high ephemerality).

---

## 🎯 **How The New System Works**

### **Step 1: Columbo Observation**
```json
{
  "observations": [
    {
      "memory_type": "facts",
      "content": "Christian lives in Liversedge", 
      "confidence_score": 0.95,
      "ephemerality_score": 0.0,    // ← Permanent info
      "contextual_value": 0.9       // ← Very useful
    },
    {
      "memory_type": "temporary", 
      "content": "It's raining today",
      "confidence_score": 1.0,
      "ephemerality_score": 0.95,   // ← Will be outdated soon
      "contextual_value": 0.1       // ← Not useful later
    }
  ]
}
```

### **Step 2: Business Logic Filtering**
- `ephemerality_score > 0.8` → **Filtered Out** 🚫
- `confidence_score < 0.3` → **Filtered Out** 🚫
- `contextual_value < 0.2` → **Filtered Out** 🚫
- Everything else → **Stored** ✅

### **Step 3: Smart Storage**
Only Christian's location gets stored. Weather gets observed but filtered out.

---

## 🔧 **Migration Options**

### **Option 1: Keep Current Code (Recommended)**
```python
# Your existing code works perfectly
response = requests.post(f"{BASE_URL}/cam/multi/store", json=memory_data)
```

### **Option 2: Upgrade to Curated Storage**
```python
# Enhanced with AI curation
curated_request = {
    **memory_data,  # Your existing data
    "user_input": user_message,
    "agent_response": your_response, 
    "curation_preferences": {
        "priority_topics": ["technical_details", "personal_info"],
        "retention_bias": "balanced",
        "agent_personality": "technical_assistant"
    }
}
response = requests.post(f"{BASE_URL}/cam/curated/store", json=curated_request)
```

### **Option 3: Analysis First**
```python
# Analyze before deciding to store
analysis = requests.post(f"{BASE_URL}/cam/curated/analyze", json={
    "user_input": user_message,
    "agent_response": your_response
}).json()

# Check what would be extracted
for obs in analysis["observations"]:
    print(f"Found: {obs['content']} (ephemeral: {obs['ephemerality_score']})")

# Only store if high-quality observations found
if analysis["should_store"]:
    requests.post(f"{BASE_URL}/cam/curated/store", json=memory_data)
```

---

## 📊 **What You'll Notice**

### **Before (Old System)**:
```json
{
  "memories": [
    {"content": "Christian lives in Liversedge"},
    {"content": "I don't know your name yet"},        // ← Noise
    {"content": "It's raining today"},               // ← Ephemeral  
    {"content": "You haven't told me your age"}      // ← Denial
  ]
}
```

### **After (Columbo System)**:
```json
{
  "memories": [
    {"content": "Christian lives in Liversedge"},
    {"content": "Christian prefers technical explanations"},
    {"content": "Christian works on AI systems"}
  ]
  // Weather and denials automatically filtered out! ✨
}
```

---

## 🎛️ **Agent Personality Tuning**

Customize curation for your agent's needs:

```python
# Technical Agent
curation_preferences = {
    "priority_topics": ["code", "technical_specs", "debugging"],
    "retention_bias": "aggressive",     # Keep more technical info
    "agent_personality": "technical_specialist"
}

# Personal Assistant  
curation_preferences = {
    "priority_topics": ["schedules", "preferences", "tasks"],
    "retention_bias": "conservative",   # Only keep important stuff
    "agent_personality": "personal_assistant"
}
```

---

## 🔍 **Debugging & Monitoring**

### **Check Memory Quality**:
```bash
curl http://46.62.130.230:8000/cam/curated/stats/your-entity-id
```

### **Debug Query Issues**:
Run the comprehensive test: `python agent_team_debug_query.py`

### **View Curation Decisions**:
```bash
curl -X POST http://46.62.130.230:8000/cam/curated/analyze \
  -H "Content-Type: application/json" \
  -d '{"user_input": "test", "agent_response": "test response"}'
```

---

## 🎉 **Expected Results**

After integrating the Columbo system, your agents should:

✅ **Remember Christian's name and location correctly**  
✅ **Ignore weather comments and casual chatter**  
✅ **Extract multiple facts from single conversations**  
✅ **Stop retrieving "I don't know" denial responses**  
✅ **Have higher quality, more relevant memories**  

---

## 🆘 **Need Help?**

1. **Test the working examples**: `python agent_team_debug_query.py`
2. **Check server health**: `curl http://46.62.130.230:8000/health`
3. **Review logs**: Check for any OpenAI API issues
4. **Verify memory quality**: Use the statistics endpoint

The system is **production-ready** and backward compatible. Your existing agents will work better immediately, and you can gradually adopt the enhanced features! 🚀