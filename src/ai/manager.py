"""
A dedicated manager class to handle all interactions with the AI provider (Ollama).
This class connects to a PRE-EXISTING Ollama server.
"""

from typing import Any
from typing import Dict

import ollama
from ollama import ResponseError

from src.core.config import settings
from src.core.logging_setup import log


class AIManager:
    """
    A singleton class to manage the connection and requests to a running Ollama service.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIManager, cls).__new__(cls)
            cls._instance._initialize_client()
        return cls._instance

    def _initialize_client(self):
        try:
            log.info(
                f"Attempting to connect to Ollama service at {settings.OLLAMA_BASE_URL}..."
            )
            self.client = ollama.Client(host=settings.OLLAMA_BASE_URL)

            models_info = self.client.list()

            # The client returns a list of Model objects, not dictionaries
            if hasattr(models_info, "models"):
                # It might be a response object with .models attribute
                models_list = models_info.models
            else:
                # Or it might be the list directly
                models_list = models_info

            # Extract model names from Model objects
            self.available_models = []
            for model in models_list:
                # Try different ways the name might be stored
                if hasattr(model, "model"):
                    self.available_models.append(model.model)
                elif hasattr(model, "name"):
                    self.available_models.append(model.name)
                elif isinstance(model, dict) and "name" in model:
                    self.available_models.append(model["name"])
                elif isinstance(model, dict) and "model" in model:
                    self.available_models.append(model["model"])

            if not self.available_models:
                log.warning(
                    f"Connected to Ollama, but no models found at {settings.OLLAMA_BASE_URL}."
                )
                log.info(
                    "Please run `ollama pull llama3` and `ollama pull llava` in your terminal."
                )
            else:
                log.success(
                    f"Successfully connected to Ollama. Available models: {self.available_models}"
                )

            # Proactively check if the models we need are present
            self._check_required_models()

        except Exception as e:
            log.error(
                f"Failed to connect to Ollama at {settings.OLLAMA_BASE_URL}. AI features disabled. Error: {repr(e)}"
            )
            self.client = None

    def _check_required_models(self):
        """Checks if the essential models defined in the config are available and provides instructions."""
        if not self.available_models:
            return

        required_text_model = getattr(settings, "AI_TEXT_MODEL_NAME", "llama3")
        required_vision_model = getattr(settings, "AI_VISION_MODEL_NAME", "llava")

        # Extract base model names from full model names (e.g., 'llama3' from 'llama3:latest')
        available_base_models = []
        for full_model_name in self.available_models:
            # Handle both 'model:tag' format and raw names
            if ":" in full_model_name:
                base_name = full_model_name.split(":")[0]
            else:
                base_name = full_model_name
            available_base_models.append(base_name)

        if required_text_model not in available_base_models:
            log.warning(
                f"Required text model '{required_text_model}' is not available in Ollama."
            )
            log.info(
                f"You can install it by running: ollama pull {required_text_model}"
            )

        if required_vision_model not in available_base_models:
            log.warning(
                f"Required vision model '{required_vision_model}' is not available in Ollama."
            )
            log.info(
                f"You can install it by running: ollama pull {required_vision_model}"
            )

    def is_available(self) -> bool:
        """Returns True if the client is connected and ready."""
        return self.client is not None

    def get_text_completion(
        self, system_prompt: str, user_prompt: str
    ) -> Dict[str, Any]:
        """Gets a structured JSON completion from a text model."""
        if not self.is_available():
            log.error("AI Manager is not available. Cannot get text completion.")
            return {}

        model_name = getattr(settings, "AI_TEXT_MODEL_NAME", "llama3")
        try:
            log.info(f"Sending request to text model '{model_name}'...")
            response = self.client.generate(
                model=model_name,
                system=system_prompt,
                prompt=user_prompt,
                format="json",
            )
            return response
        except ResponseError as e:
            log.error(f"Ollama API error during text completion: {e.error}")
            return {}
        except Exception as e:
            log.error(f"An unexpected error occurred during text completion: {e}")
            return {}

    def get_vision_completion(self, prompt: str, image_bytes: bytes) -> Dict[str, Any]:
        """Gets a structured JSON completion from a vision model."""
        if not self.is_available():
            log.error("AI Manager is not available. Cannot get vision completion.")
            return {}

        model_name = getattr(settings, "AI_VISION_MODEL_NAME", "llava")
        try:
            log.info(f"Sending request to vision model '{model_name}'...")
            response = self.client.generate(
                model=model_name,
                prompt=prompt,
                images=[image_bytes],
                format="json",
            )
            return response
        except ResponseError as e:
            log.error(f"Ollama API error during vision completion: {e.error}")
            return {}
        except Exception as e:
            log.error(f"An unexpected error occurred during vision completion: {e}")
            return {}


ai_manager = AIManager()

# Test block
if __name__ == "__main__":
    print("--- AI Manager Test ---")
    print(f"Manager is available: {ai_manager.is_available()}")
    if ai_manager.is_available():
        print(f"Available models: {ai_manager.available_models}")
    print("-----------------------")
