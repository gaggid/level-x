# utils/cost_tracker.py
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class CostTracker:
    """Track API costs for analysis"""
    
    # Pricing (per TwitterAPI.io)
    TWITTER_USER_INFO = 18      # credits
    TWITTER_TWEETS = 300         # credits (average for 50 tweets)
    TWITTER_SEARCH = 20          # credits (per search, estimate)
    
    # Grok pricing (per xAI)
    GROK_INPUT_TOKEN = 0.002 / 1000   # $0.002 per 1K input tokens (grok-beta)
    GROK_OUTPUT_TOKEN = 0.010 / 1000  # $0.010 per 1K output tokens (grok-beta)
    
    # Conversion
    TWITTER_CREDIT_TO_USD = 0.00001  # 1 credit = $0.00001
    
    def __init__(self):
        self.twitter_credits = 0
        self.grok_input_tokens = 0
        self.grok_output_tokens = 0
        self.api_calls = {
            'user_info': 0,
            'tweets': 0,
            'search': 0,
            'grok': 0
        }
    
    def add_user_info_call(self):
        """Track user info API call"""
        self.twitter_credits += self.TWITTER_USER_INFO
        self.api_calls['user_info'] += 1
    
    def add_tweets_call(self, tweet_count: int = 50):
        """Track tweets API call"""
        # Calculate credits based on actual tweet count
        credits = int((tweet_count / 1000) * 15000)  # 15 credits per tweet
        if credits < 15:  # Minimum charge
            credits = 15
        self.twitter_credits += credits
        self.api_calls['tweets'] += 1
    
    def add_search_call(self):
        """Track search API call"""
        self.twitter_credits += self.TWITTER_SEARCH
        self.api_calls['search'] += 1
    
    def add_grok_call(self, input_tokens: int, output_tokens: int):
        """Track Grok API call"""
        self.grok_input_tokens += input_tokens
        self.grok_output_tokens += output_tokens
        self.api_calls['grok'] += 1
    
    def get_twitter_cost(self) -> float:
        """Get Twitter API cost in USD"""
        return self.twitter_credits * self.TWITTER_CREDIT_TO_USD
    
    def get_grok_cost(self) -> float:
        """Get Grok API cost in USD"""
        input_cost = self.grok_input_tokens * self.GROK_INPUT_TOKEN
        output_cost = self.grok_output_tokens * self.GROK_OUTPUT_TOKEN
        return input_cost + output_cost
    
    def get_total_cost(self) -> float:
        """Get total cost in USD"""
        return self.get_twitter_cost() + self.get_grok_cost()
    
    def get_summary(self) -> Dict:
        """Get cost summary as dict"""
        return {
            'twitter': {
                'user_info_calls': self.api_calls['user_info'],
                'tweets_calls': self.api_calls['tweets'],
                'search_calls': self.api_calls['search'],
                'total_credits': self.twitter_credits,
                'cost_usd': self.get_twitter_cost()
            },
            'grok': {
                'api_calls': self.api_calls['grok'],
                'input_tokens': self.grok_input_tokens,
                'output_tokens': self.grok_output_tokens,
                'cost_usd': self.get_grok_cost()
            },
            'total_cost_usd': self.get_total_cost()
        }
    
    def print_summary(self):
        """Print cost summary"""
        print("\n💰 COST BREAKDOWN:")
        print("="*60)
        print(f"Twitter API:")
        print(f"  - User info calls: {self.api_calls['user_info']}")
        print(f"  - Tweets calls: {self.api_calls['tweets']}")
        print(f"  - Search calls: {self.api_calls['search']}")
        print(f"  - Total credits: {self.twitter_credits:,}")
        print(f"  - Cost: ${self.get_twitter_cost():.4f}")
        print(f"\nGrok AI:")
        print(f"  - API calls: {self.api_calls['grok']}")
        print(f"  - Input tokens: {self.grok_input_tokens:,}")
        print(f"  - Output tokens: {self.grok_output_tokens:,}")
        print(f"  - Cost: ${self.get_grok_cost():.4f}")
        print(f"\n{'='*60}")
        print(f"TOTAL COST: ${self.get_total_cost():.4f}")
        print("="*60)