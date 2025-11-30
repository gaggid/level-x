# ai/gemini_client.py

import google.generativeai as genai
from typing import Optional
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class GeminiAPIError(Exception):
    """Custom exception for Gemini API errors"""
    pass


class GeminiClient:
    """
    Wrapper for Google Gemini API (Free tier fallback)
    """
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key:
            raise GeminiAPIError("GEMINI_API_KEY not found in settings")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')  # Free tier
        
        logger.info("GeminiClient initialized with gemini-1.5-flash")
    
    def complete(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Simple completion
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
        
        Returns:
            Generated text
        """
        try:
            logger.info("Making Gemini API request...")
            
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": 2048,
            }
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            text = response.text
            logger.info(f"Gemini response received ({len(text)} chars)")
            
            return text
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise GeminiAPIError(f"API error: {str(e)}")


# Test function
def test_gemini():
    """Test Gemini client"""
    try:
        print("\n🧪 Testing Gemini API Client\n")
        
        client = GeminiClient()
        
        response = client.complete("Say 'Hello from Gemini!' and nothing else.")
        print(f"Response: {response}")
        
        print("\n✅ Gemini test passed!")
        
    except GeminiAPIError as e:
        print(f"\n❌ Test failed: {e}")
        print("\n⚠️ Make sure GEMINI_API_KEY is set in your .env file")


if __name__ == "__main__":
    test_gemini()