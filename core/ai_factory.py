import os
import yaml
from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

class AIFactory:
    @staticmethod
    def get_model():
        # Load the latest configuration
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
        
        provider = config.get("ai_provider", "sambanova").lower()
        model_name = config.get("model")

        # Configuration for SambaNova
        if provider == "sambanova":
            api_key = os.getenv("SAMBANOVA_API_KEY")
            if not api_key:
                logger.error("SAMBANOVA_API_KEY missing in .env. Falling back to Groq...")
                provider = "groq" # Automatic safety fallback
            else:
                logger.info(f"🧠 Initializing SambaNova Brain: {model_name}")
                return ChatOpenAI(
                    base_url="https://api.sambanova.ai/v1",
                    api_key=api_key,
                    model=model_name,
                    streaming=False
                )

        # Configuration for Groq (Backup)
        if provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY missing in .env. Cannot proceed.")
            
            # Use Groq default 70b if model name is still set to SambaNova string
            actual_model = "llama-3.1-70b-versatile" if "Meta-Llama" in model_name else model_name
            logger.info(f"🧠 Initializing Groq Backup Brain: {actual_model}")
            return ChatOpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=api_key,
                model=actual_model
            )

        # Configuration for Ollama (Local)
        if provider == "ollama":
            logger.info("🧠 Initializing Local Ollama Brain")
            return Ollama(
                base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
                model="llama3"
            )

        raise ValueError(f"Unsupported AI Provider: {provider}")