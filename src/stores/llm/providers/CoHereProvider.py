from ..LLMInterface import LLMInterface
from ..LLMEnums import CoHereEnums, DocumentTypeEnum
import cohere
import logging
from typing import List, Union

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

        self.client = cohere.ClientV2(api_key=self.api_key)
        
        self.enums = CoHereEnums

        self.logger = logging.getLogger(__name__ )
        
        
        
        
    def process_text(self, text: str):  
        return text[:self.default_input_max_characters].strip()
    
    
    def construct_prompt(self, prompt: str, role: str):
        return {
            "role": role,
            "content": prompt
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
            self.logger.error("CoHere client was not set")
            return None

        if not self.generation_model_id:
            self.logger.error("Generation model for CoHere was not set")
            return None

        max_output_tokens = max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temperature = temperature if temperature else self.default_generation_temperature

        # Append user message — same pattern as OpenAIProvider
        chat_history.append(
            self.construct_prompt(prompt=prompt, role=self.enums.USER.value)
        )

        try:
            response = self.client.chat(
                model=self.generation_model_id,
                messages=chat_history,
                max_tokens=max_output_tokens,
                temperature=temperature,
            )

            if not response or not response.message or not response.message.content or len(response.message.content) == 0:
                self.logger.error("Error while generating text with CoHere")
                return None

            return response.message.content[0].text

        except Exception as e:
            logging.error(f"Error generating text with Cohere: {e}")
            return None
        
        
        
    def embed_text(self, text: Union[str, List[str]], document_type: str = None):
        if not self.client:
            logging.error("Cohere client is not initialized.")
            return None
        
        if not self.embedding_model_id:
            logging.error("Embedding model ID is not set.")
            return None
        if isinstance(text, str):
            text = [text]
        
        input_type = CoHereEnums.DOCUMENT
        if document_type == DocumentTypeEnum.QUERY.value:
            input_type = CoHereEnums.QUERY
            
        try:
            response = self.client.embed(
                model=self.embedding_model_id,
                texts=[self.process_text(t) for t in text],
                input_type=input_type.value,
                embedding_types=['float'],
            )
            return [ f for f in response.embeddings.float ]
        except Exception as e:
            logging.error(f"Error generating embeddings with Cohere: {e}")
            return None