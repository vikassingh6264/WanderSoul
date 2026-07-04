"""
Tools package — individual GenAI-powered capability functions.

Each tool is a separate module with a single async function that:
1. Filters the curated dataset based on user context
2. Calls the Groq LLM (via LangChain) for enrichment/generation
3. Returns a structured Pydantic response

All six required capabilities are represented:
- destination_recommender: Recommend attractions
- hidden_gem_finder: Uncover hidden gems
- storytelling_generator: Generate immersive storytelling
- heritage_promoter: Promote heritage
- event_suggester: Suggest local events
- experience_connector: Connect with authentic cultural experiences
"""
