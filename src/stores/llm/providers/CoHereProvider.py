from ..LLMInterface import LLMInterface
from ..LLMEnums import CoHereEnums, DocumentTypeEnum
import cohere
import logging


class CoHereProvider(LLMInterface):
    def __init__(self, api_key: str,
                       default_input_max_characters: int=5000,
                       default_generation_max_output_tokens: int=1000,
                       default_generation_temperature: float=0.1):
        
        self.api_key = api_key
        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature    
        
        self.generation_model_id = None

        self.embedding_model_id = None
        self.embedding_size = None

        self.client = cohere.Client(api_key=self.api_key)
        
        self.enums = CoHereEnums

        self.logger = logging.getLogger(__name__ )
        
        
        
        
    def process_text(self, text: str):  
        return text[:self.default_input_max_characters].strip()
    
    
    def construct_prompt(self, prompt: str, role: str):
        return {
            "role": role,
            "text": self.process_text(prompt)
        }
        
        
    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id
        self.logger.info(f"Generation model set to: {model_id}")
        
        
    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size
        self.logger.info(f"Embedding model set to: {model_id} with embedding size: {embedding_size}")
        
        
        
        
    def generate_text(self, prompt: str, system_prompt: str = None, chat_history: list=[], max_output_tokens: int=None, temperature: float = None):
        if not self.client:
            logging.error("Cohere client is not initialized.")
            return None
        
        if not self.generation_model_id:
            logging.error("Generation model ID is not set.")
            return None
            
        try:
            response = self.client.chat(
                model=self.generation_model_id,
                chat_history=chat_history if len(chat_history) > 0 else None,
                message=prompt,
                preamble=system_prompt,
                max_tokens=max_output_tokens or self.default_generation_max_output_tokens,
                temperature=temperature or self.default_generation_temperature,
            )
            
            return response.text.strip()
        except Exception as e:
            logging.error(f"Error generating text with Cohere: {e}")
            return None
        
        
        
    def embed_text(self, text: str, document_type: str = None):
        if not self.client:
            logging.error("Cohere client is not initialized.")
            return None
        
        if not self.embedding_model_id:
            logging.error("Embedding model ID is not set.")
            return None
        
        
        input_type = CoHereEnums.DOCUMENT
        if document_type == DocumentTypeEnum.QUERY:
            input_type = CoHereEnums.QUERY
            
        try:
            response = self.client.embed(
                model=self.embedding_model_id,
                texts=[self.process_text(text)],
                input_type=input_type.value,
                embedding_types=['float'],
            )
            return response.embeddings.float[0]
        except Exception as e:
            logging.error(f"Error generating embeddings with Cohere: {e}")
            return None