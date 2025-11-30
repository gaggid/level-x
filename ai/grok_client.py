# ai/grok_client.py
import requests
from typing import Dict, List, Optional
from config.settings import settings
import logging
import time
import json
import re
from requests.exceptions import RequestException, HTTPError, Timeout

logger = logging.getLogger(__name__)


class GrokAPIError(Exception):
    """Custom exception for Grok API errors"""
    pass


class GrokClient:
    """
    Wrapper for xAI Grok API
    Compatible with OpenAI format
    """
    
    def __init__(self):
        self.api_key = settings.XAI_API_KEY
        if not self.api_key:
            raise GrokAPIError("XAI_API_KEY not found in settings")
        
        self.base_url = "https://api.x.ai/v1"
        self.model = "grok-2-1212"
        self.timeout = 60
        self.max_retries = 3
        
        logger.info(f"GrokClient initialized with model: {self.model}")
    
    def _make_request(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        retry_count: int = 0,
        cost_tracker=None
    ) -> str:
        """Make request to Grok API with retry logic"""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4000
        }
        
        try:
            logger.info(f"Making Grok API request (attempt {retry_count + 1})")
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract text from response
            text = data['choices'][0]['message']['content']
            
            # Log token usage
            usage = data.get('usage', {})
            logger.info(
                f"Grok response received. "
                f"Input tokens: {usage.get('prompt_tokens', 0)}, "
                f"Output tokens: {usage.get('completion_tokens', 0)}"
            )
            
            # Track cost
            if cost_tracker:
                cost_tracker.add_grok_call(
                    usage.get('prompt_tokens', 0),
                    usage.get('completion_tokens', 0)
                )
            
            return text
            
        except HTTPError as e:
            logger.error(f"HTTP Error: {e}")
            
            if e.response.status_code == 429:  # Rate limit
                if retry_count < self.max_retries:
                    wait_time = 2 ** retry_count
                    logger.warning(f"Rate limited. Waiting {wait_time}s before retry {retry_count + 1}")
                    time.sleep(wait_time)
                    return self._make_request(messages, temperature, retry_count + 1, cost_tracker)
                else:
                    raise GrokAPIError("Rate limit exceeded after retries")
            
            elif e.response.status_code == 401 or e.response.status_code == 403:
                raise GrokAPIError("Invalid API key. Check XAI_API_KEY in .env")
            
            else:
                raise GrokAPIError(f"API error: {e.response.status_code}")
        
        except Timeout:
            if retry_count < self.max_retries:
                logger.warning(f"Timeout. Retry {retry_count + 1}")
                time.sleep(2)
                return self._make_request(messages, temperature, retry_count + 1, cost_tracker)
            else:
                raise GrokAPIError("Request timeout")
        
        except RequestException as e:
            logger.error(f"Request failed: {e}")
            raise GrokAPIError(f"Network error: {str(e)}")
    
    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        cost_tracker=None
    ) -> str:
        """Simple completion"""
        messages = []
        
        if system:
            messages.append({"role": "system", "content": system})
        
        messages.append({"role": "user", "content": prompt})
        
        return self._make_request(messages, temperature, 0, cost_tracker)
    
    def complete_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.0,
        cost_tracker=None
    ) -> Dict:
        """
        Complete and parse JSON response
        Temperature set to 0 for deterministic JSON output
        """
        response = self.complete(prompt, system, temperature, cost_tracker)
        
        # Clean response (remove markdown if present)
        response_clean = response.strip()
        if response_clean.startswith('```json'):
            response_clean = response_clean[7:]
        if response_clean.startswith('```'):
            response_clean = response_clean[3:]
        if response_clean.endswith('```'):
            response_clean = response_clean[:-3]
        
        response_clean = response_clean.strip()
        
        # FIX: Remove commas from numbers (Grok sometimes returns 1,250,000)
        # This is invalid JSON, so we need to clean it
        # Match numbers with commas like 1,250,000 and remove commas
        response_clean = re.sub(r'(\d),(\d)', r'\1\2', response_clean)
        
        try:
            return json.loads(response_clean)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Response was: {response_clean[:500]}")
            raise GrokAPIError(f"Invalid JSON response: {str(e)}")


# Test function
def test_grok_client():
    """Test Grok API client"""
    try:
        print("\n🧪 Testing Grok API Client\n")
        
        client = GrokClient()
        
        # Test 1: Simple completion
        print("1️⃣ Testing simple completion...")
        response = client.complete(
            prompt="Say 'Hello from Grok!' and nothing else.",
            temperature=0
        )
        print(f"   Response: {response}")
        print("   ✅ Simple completion works!\n")
        
        # Test 2: JSON response
        print("2️⃣ Testing JSON response...")
        response = client.complete_json(
            prompt='Return exactly this JSON: {"status": "working", "value": 42}',
            temperature=0
        )
        print(f"   Response: {response}")
        assert response.get('status') == 'working'
        print("   ✅ JSON parsing works!\n")
        
        print("🎉 All tests passed!")
        
    except GrokAPIError as e:
        print(f"\n❌ Test failed: {e}")
        print("\n⚠️ Make sure XAI_API_KEY is set in your .env file")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    test_grok_client()