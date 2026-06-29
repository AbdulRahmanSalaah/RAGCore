# This file defines the LLMInterface, which serves as an abstract base class for all LLM implementations. It specifies the methods that any LLM implementation must provide, such as setting generation and embedding models,
from abc import ABC, abstractmethod

class LLMInterface(ABC):

    @abstractmethod
    def set_generation_model(self, model_id: str): 
        pass

    @abstractmethod
    def set_embedding_model(self, model_id: str, embedding_size: int):  
        pass

    @abstractmethod
    def generate_text(self, prompt: str, system_prompt: str = None, chat_history: list=[], max_output_tokens: int=None,
                            temperature: float = None):
        pass

    @abstractmethod
    def embed_text(self, text: str, document_type: str = None):
        pass

    @abstractmethod
    def construct_prompt(self, prompt: str, role: str):
        pass