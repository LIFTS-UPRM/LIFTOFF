# Knowledge Ingestion Pipeline

**Status**: Architecture specification  
**Last Updated**: 2026-07-22  
**Audience**: Data engineers, ML/LLM specialists, copilot maintainers

---

## Overview

The Knowledge Ingestion Pipeline feeds domain knowledge into the AI copilot so it can make informed decisions about missions, weather, trajectories, and LIFTS procedures.

**Sources**:
- Historical mission data (past launches, success rates, lessons learned)
- LIFTS procedures & documentation (org principles, design standards)
- Weather patterns & launch criteria
- Trajectory simulation data (altitudes, landing zones, timing)
- External knowledge (HAB best practices, FAA regulations)

**Output**: Retrieval-Augmented Generation (RAG) vector database, copilot context.

---

## Knowledge Sources

### 1. Mission History

**Purpose**: Learn from past launches (what worked, what failed, patterns)

**Data**:
- Mission name, objectives, team
- Launch conditions (weather, location, time)
- Payload specs (mass, instruments)
- Telemetry (altitude, duration, sensor readings)
- Recovery status (successful/lost, location)
- Lessons learned (post-flight reports)

**Format**: JSON export from STRATOS database
```json
{
  "mission_id": "mission_001",
  "name": "ASCENT",
  "year": 2025,
  "team": "LIFTS Flight Operations",
  "objectives": ["Solar cell efficiency", "Ozone detection"],
  "payload_mass_kg": 2.3,
  "launch_location": "Puerto Rico",
  "max_altitude_m": 115000,
  "flight_duration_min": 185,
  "success": true,
  "recovery": "Successful, 12km from launch site",
  "lessons": [
    "GPS antenna orientation critical",
    "Battery heating tape prevented early shutoff",
    "Radio link lost above 95km; planned for next mission"
  ]
}
```

### 2. LIFTS Organizational Knowledge

**Purpose**: Understand LIFTS structure, roles, decision-making

**Sources**:
- Organization principles PDF (divisions, roles, processes)
- Project management docs (timelines, budgets, resource allocation)
- Design standards (power budgets, payload guidelines)
- Safety procedures (launch checklists, abort criteria)

**Ingest**: Parse PDFs → extract key sections → store in vector DB

### 3. Weather Patterns

**Purpose**: Copilot can learn seasonal patterns, optimal launch windows

**Data**:
- Historical weather for launch site (temperature, wind, humidity by month)
- Launch criteria from LIFTS procedures
- Weather forecast interpretation

**Format**: CSV or structured text
```
Month,Avg_Temp_C,Avg_Wind_ms,Humidity_Pct,Launch_Viability
Jan,25,4.2,75,Good
Feb,26,4.5,72,Good
Mar,27,5.1,70,Fair (higher winds)
...
```

### 4. Trajectory Simulation Data

**Purpose**: Copilot understands predicted landing zones, altitudes, timing

**Source**: SondeHub Tawhiri historical runs

**Data**:
- Launch location, payload weight, balloon type
- Predicted max altitude, landing location
- Flight duration, descent rate
- Sensitivity to launch conditions (time of day, weather)

### 5. External Knowledge

**Purpose**: Best practices, regulations, technical background

**Sources**:
- FAA regulations (airspace, NOTAM procedures)
- HAB community knowledge (launch best practices, common pitfalls)
- Physics (altitude pressure/temperature relationships)

**Ingest**: Web scraping or manual curation of key resources

---

## Ingestion Pipeline

### Step 1: Collect & Normalize

```python
# backend/knowledge_pipeline/collect.py

import json
from pathlib import Path

class KnowledgeCollector:
    def collect_mission_history(self):
        """Export mission history from database"""
        missions = db.query(Mission).all()
        documents = []
        
        for mission in missions:
            doc = {
                "source": "mission_history",
                "id": mission.id,
                "type": "mission",
                "content": f"""
Mission: {mission.name}
Year: {mission.year}
Team: {', '.join([m.user.name for m in mission.team])}
Objectives: {'; '.join(mission.objectives)}
Payload Mass: {mission.payload.mass_kg} kg
Max Altitude: {mission.flights[0].telemetry.max_altitude} m
Flight Duration: {mission.flights[0].telemetry.duration} minutes
Success: {'Yes' if mission.flights[0].recovery_status == 'recovered' else 'No'}
Recovery: {mission.flights[0].recovery_status}
Lessons Learned:
{chr(10).join([f'- {lesson}' for lesson in mission.lessons_learned])}
                """,
                "metadata": {
                    "year": mission.year,
                    "success": mission.flights[0].recovery_status == "recovered",
                    "altitude_m": mission.flights[0].telemetry.max_altitude
                }
            }
            documents.append(doc)
        
        return documents
    
    def collect_procedures(self):
        """Ingest LIFTS procedures (PDFs, docs)"""
        # Parse Organización y Principios LIFTS.pdf
        procedures = extract_text_from_pdf("docs/LIFTS_principles.pdf")
        
        documents = [{
            "source": "procedures",
            "type": "organizational",
            "content": procedures,
            "metadata": {"category": "organization"}
        }]
        
        return documents
```

### Step 2: Chunk Documents

Break large documents into chunks for embedding:

```python
# backend/knowledge_pipeline/chunk.py

from langchain.text_splitter import RecursiveCharacterTextSplitter

class DocumentChunker:
    def chunk(self, documents, chunk_size=1000, overlap=100):
        """Split documents into chunks for embedding"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunked = []
        for doc in documents:
            chunks = splitter.split_text(doc["content"])
            
            for i, chunk in enumerate(chunks):
                chunked.append({
                    "source": doc["source"],
                    "doc_id": doc["id"],
                    "chunk_index": i,
                    "content": chunk,
                    "metadata": doc.get("metadata", {})
                })
        
        return chunked
```

### Step 3: Embed & Store

Generate embeddings (vector representations) and store in vector DB:

```python
# backend/knowledge_pipeline/embed.py

from openai import OpenAI
import weaviate

class EmbeddingPipeline:
    def __init__(self):
        self.openai = OpenAI(api_key=LLM_API_KEY)
        self.weaviate = weaviate.Client("http://weaviate:8080")
    
    def embed_and_store(self, chunked_documents):
        """Embed chunks and store in Weaviate"""
        for chunk in chunked_documents:
            # Generate embedding
            embedding = self.openai.embeddings.create(
                model="text-embedding-3-small",
                input=chunk["content"]
            ).data[0].embedding
            
            # Store in Weaviate
            self.weaviate.data_object.create(
                class_name="KnowledgeChunk",
                data_object={
                    "content": chunk["content"],
                    "source": chunk["source"],
                    "chunk_index": chunk["chunk_index"],
                    "metadata": chunk["metadata"]
                },
                vector=embedding
            )
        
        print(f"Indexed {len(chunked_documents)} chunks")
```

---

## Retrieval in Chat

When copilot receives a user question, retrieve relevant knowledge chunks:

```python
# backend/llm.py (in chat flow)

async def execute_chat(user_message: str, mission_id: str):
    # Retrieve relevant knowledge
    relevant_docs = retrieve_knowledge(
        query=user_message,
        mission_id=mission_id,
        top_k=5
    )
    
    # Augment system prompt with retrieved knowledge
    context = format_knowledge_context(relevant_docs)
    
    # Append to system prompt before calling LLM
    system_prompt = SYSTEM_PROMPT + f"""

RELEVANT CONTEXT FROM MISSION HISTORY & PROCEDURES:
{context}
"""
    
    # Call OpenAI with augmented prompt
    response = await openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )
    
    return response.choices[0].message.content
```

### Retrieval Function

```python
# backend/knowledge_pipeline/retrieve.py

def retrieve_knowledge(query: str, mission_id: str, top_k: int = 5):
    """Retrieve relevant knowledge chunks for query"""
    
    # Generate query embedding
    query_embedding = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    ).data[0].embedding
    
    # Search Weaviate
    results = weaviate.query.get(
        class_name="KnowledgeChunk",
        properties=["content", "source", "metadata"]
    ).with_near_vector({
        "vector": query_embedding
    }).with_limit(top_k).with_where({
        "operator": "Or",
        "operands": [
            {"path": ["source"], "operator": "Equal", "valueString": "mission_history"},
            {"path": ["source"], "operator": "Equal", "valueString": "procedures"},
        ]
    }).do()
    
    return results["data"]["Get"]["KnowledgeChunk"]
```

---

## Update Schedule

### Initial Ingestion

Run once during setup:

```bash
# Collect all sources
python -m knowledge_pipeline.collect

# Chunk documents
python -m knowledge_pipeline.chunk

# Generate embeddings
python -m knowledge_pipeline.embed

# Verify indexing
curl http://weaviate:8080/v1/objects | jq '.totalResults'
```

### Incremental Updates

After each mission (weekly/monthly):

```bash
# Ingest latest mission completion
python -m knowledge_pipeline.add_recent_missions --since 2026-07-20

# Update weather patterns (monthly)
python -m knowledge_pipeline.update_weather_patterns
```

**Automation**: Scheduled task (cron) or event-triggered (Mission.state → Analyzed)

---

## Vector Database

### Weaviate Setup

```bash
# Docker Compose
docker run -d \
  -p 8080:8080 \
  -e "PERSISTENCE_DATA_PATH=/var/lib/weaviate" \
  semitechnologies/weaviate:latest
```

### Schema

```yaml
classes:
  - name: KnowledgeChunk
    properties:
      - name: content
        dataType: [text]
      - name: source
        dataType: [text]  # mission_history, procedures, weather, etc.
      - name: chunk_index
        dataType: [int]
      - name: metadata
        dataType: [object]
    vectorIndexConfig:
      name: hnsw
```

---

## Quality Control

### Relevance Testing

After ingestion, test retrieval quality:

```python
# tests/test_knowledge_retrieval.py

def test_weather_query():
    query = "What's the best weather for a HAB launch?"
    results = retrieve_knowledge(query, mission_id=None, top_k=5)
    
    # Verify top result is weather-related
    assert "weather" in results[0]["content"].lower()
    assert results[0]["source"] in ["weather_patterns", "procedures"]
```

### Hallucination Monitoring

Monitor copilot responses for unsupported claims:

```python
# backend/llm.py

async def execute_chat(...):
    response = await openai_client.chat.completions.create(...)
    
    # Check if response references knowledge sources
    if "according to" not in response or "history" not in response:
        logger.warning("Response may not cite knowledge sources", {"response": response})
    
    return response
```

---

## Privacy & Data Retention

- **Mission data**: Keep indefinitely (scientific archive)
- **Personal data**: Redact user email addresses before indexing
- **Procedures**: Version-controlled; old versions archived

---

## Future Enhancements

1. **Fine-tuning**: Fine-tune a smaller LLM on LIFTS data (vs. just RAG)
2. **Multi-modal**: Ingest images (mission photos, telemetry plots)
3. **Real-time updates**: Stream telemetry into knowledge base during flight
4. **Semantic search**: Allow copilot to query by intent ("best launch practices")

---

## Next: Deploy Weaviate, run initial ingestion

- `docker-compose.yml`: Weaviate service
- `backend/knowledge_pipeline/`: Full pipeline implementation
- Database migrations: Add `knowledge_chunks` metadata table
