# backend/apps/profile_agent/llm_config.py
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()  # Load environment variables once

# Global configuration dictionary
LLM_CONFIGS = {
    'gpt-4o': {'model': 'gpt-4o'},
    'gpt-4o-mini': {'model': 'gpt-4o-mini'},
}

class LLMFactory:
    def __init__(self, configs=None):
        # Use the global config if none provided
        self.LLM_CONFIGS = configs or LLM_CONFIGS

    def get_llm(self, model_key='gpt-4o'):
        key = self.LLM_CONFIGS.get(model_key)
        if key is None:
            raise ValueError(f"Invalid model_key '{model_key}'. Available keys: {list(self.LLM_CONFIGS.keys())}")
        return ChatOpenAI(**key)

# Optionally, create a singleton instance that everyone can use:
global_llm_factory = LLMFactory()
