import requests
from typing import Dict, List, Optional
from config.settings import settings
import logging
import time
from requests.exceptions import RequestException, HTTPError, Timeout

logger = logging.getLogger(__name__)


class TwitterAPIError(Exception):
    """Custom exception for Twitter API errors"""
    pass


class TwitterAPIClient:
    """
    Wrapper for TwitterAPI.io
    """
    
    def __init__(self, cost_tracker=None):
        self.api_key = settings.TWITTERAPI_KEY
        self.base_url = "https://api.twitterapi.io"
        self.headers = {
            "X-API-Key": self.api_key
        }
        self.timeout = 30
        self.max_retries = 3
        self.rate_limit_delay = 5
        self.cost_tracker = cost_tracker
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, retry_count: int = 0) -> Dict:
        """
        Make HTTP request with retry logic and rate limit handling
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(f"Making request to: {url}")
            # logger.debug(f"Params: {params}")
            
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )
            
            logger.info(f"Response status: {response.status_code}")
            
            response.raise_for_status()
            
            # Rate limit protection - wait before next request
            time.sleep(self.rate_limit_delay)
            
            return response.json()
            
        except HTTPError as e:
            logger.error(f"HTTP Error: {e}")
            logger.error(f"Response: {e.response.text}")
            
            if e.response.status_code == 429:  # Rate limit
                if retry_count < self.max_retries:
                    wait_time = 10
                    logger.warning(f"Rate limited. Waiting {wait_time}s before retry {retry_count + 1}")
                    time.sleep(wait_time)
                    return self._make_request(method, endpoint, params, retry_count + 1)
                else:
                    raise TwitterAPIError("API rate limit exceeded. Free tier: 1 request per 5 seconds.")
            
            elif e.response.status_code == 404:
                raise TwitterAPIError("Account not found or endpoint incorrect")
            
            elif e.response.status_code == 401 or e.response.status_code == 403:
                raise TwitterAPIError("Invalid API key. Check TWITTERAPI_KEY in .env")
            
            else:
                raise TwitterAPIError(f"API error: {e.response.status_code}")
        
        except Timeout:
            if retry_count < self.max_retries:
                logger.warning(f"Timeout. Retry {retry_count + 1}")
                time.sleep(2)
                return self._make_request(method, endpoint, params, retry_count + 1)
            else:
                raise TwitterAPIError("Request timeout")
        
        except RequestException as e:
            logger.error(f"Request failed: {e}")
            raise TwitterAPIError(f"Network error: {str(e)}")
    
    def get_user_by_handle(self, handle: str) -> Dict:
        """Fetch user profile by handle"""
        handle = handle.lstrip('@')
        
        logger.info(f"Fetching profile for @{handle}")
        
        endpoint = "/twitter/user/info"
        params = {"userName": handle}
        
        try:
            response = self._make_request("GET", endpoint, params=params)
            
            # Track cost
            if self.cost_tracker:
                self.cost_tracker.add_user_info_call()
            
            # Response format: {"data": {...user object...}}
            if 'data' in response and response['data']:
                user_data = response['data']
                
                # Validate required fields exist
                if not user_data.get('id') or not user_data.get('userName'):
                    logger.error(f"Invalid user data for @{handle}")
                    return None
                
                # Transform to standard format
                return {
                    'id': user_data.get('id'),
                    'username': user_data.get('userName'),
                    'name': user_data.get('name'),
                    'description': user_data.get('description', ''),
                    'profile_image_url': user_data.get('profilePicture', ''),
                    'public_metrics': {
                        'followers_count': user_data.get('followers', 0),
                        'following_count': user_data.get('following', 0),
                        'tweet_count': user_data.get('statusesCount', 0),
                        'listed_count': 0  # Not in response
                    }
                }
            else:
                logger.error(f"Account @{handle} not found or no data returned")
                return None
        
        except TwitterAPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    def search_users(self, query: str, max_results: int = 20) -> List[Dict]:
        """Search for users by keyword"""
        logger.info(f"Searching users with query: '{query}'")
        
        endpoint = "/twitter/user/search"
        params = {"query": query}
        
        try:
            response = self._make_request("GET", endpoint, params=params)
            
            # Track cost
            if self.cost_tracker:
                self.cost_tracker.add_search_call()
            
            if 'users' in response:
                users = response['users']
                
                # Transform to standard format
                results = []
                for user in users[:max_results]:
                    # Skip unavailable/protected accounts
                    if user.get('protected') or not user.get('id'):
                        continue
                    
                    # FIXED: Correct field names from actual API response
                    results.append({
                        'id': user.get('id'),
                        'username': user.get('username') or user.get('screen_name'),  # Try both
                        'name': user.get('name'),
                        'description': user.get('description', ''),
                        'profile_image_url': user.get('profile_image_url_https', ''),
                        'public_metrics': {
                            'followers_count': user.get('followers_count', 0),  # FIXED: was 'followers'
                            'following_count': user.get('following_count', 0),  # FIXED: was 'following'
                            'tweet_count': user.get('statuses_count', 0),       # FIXED: was 'statusesCount'
                            'listed_count': 0
                        }
                    })
                
                logger.info(f"Found {len(results)} users")
                return results
            else:
                logger.warning(f"No users found for query: {query}")
                return []
        
        except TwitterAPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise TwitterAPIError(f"Failed to search users: {str(e)}")
    
    def get_user_tweets(self, handle: str, max_results: int = 50) -> List[Dict]:
        """Fetch recent tweets from user"""
        handle = handle.lstrip('@')
        
        logger.info(f"Fetching tweets for @{handle}")
        
        endpoint = "/twitter/user/last_tweets"
        params = {
            "userName": handle,
            "count": min(max_results, 100)
        }
        
        try:
            response = self._make_request("GET", endpoint, params=params)
            
            if 'data' in response and 'tweets' in response['data']:
                tweets_raw = response['data']['tweets']
                
                # Track cost (before filtering)
                if self.cost_tracker:
                    self.cost_tracker.add_tweets_call(len(tweets_raw))
                
                # Transform to standard format
                tweets = []
                for tweet in tweets_raw:
                    # Skip retweets
                    if tweet.get('type') == 'retweet' or tweet.get('retweeted_tweet'):
                        continue
                    
                    # Skip replies (focus on original content)
                    if tweet.get('isReply'):
                        continue
                    
                    tweets.append({
                        'id': tweet.get('id'),
                        'text': tweet.get('text', ''),
                        'created_at': tweet.get('createdAt'),
                        'public_metrics': {
                            'like_count': tweet.get('likeCount', 0),
                            'retweet_count': tweet.get('retweetCount', 0),
                            'reply_count': tweet.get('replyCount', 0),
                            'quote_count': tweet.get('quoteCount', 0)
                        },
                        'entities': tweet.get('entities', {})
                    })
                
                logger.info(f"Fetched {len(tweets)} original tweets (filtered from {len(tweets_raw)} total)")
                return tweets
            else:
                logger.warning(f"Unexpected response structure: {list(response.keys())}")
                return []
        
        except TwitterAPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise TwitterAPIError(f"Failed to fetch tweets: {str(e)}")
    
    def validate_account(self, handle: str) -> bool:
        """
        Check if account exists and is accessible
        """
        try:
            self.get_user_by_handle(handle)
            return True
        except TwitterAPIError:
            return False


# Test function
def test_client():
    """Test the Twitter API client"""
    client = TwitterAPIClient()
    
    test_handle = "naval"
    
    try:
        print(f"\n🧪 Testing TwitterAPI.io client\n")
        
        # Test user fetch
        print(f"1️⃣ Fetching user @{test_handle}...")
        user = client.get_user_by_handle(test_handle)
        print(f"   ✅ Success!")
        print(f"   Name: {user['name']}")
        print(f"   Username: @{user['username']}")
        print(f"   Followers: {user['public_metrics']['followers_count']:,}")
        print(f"   Bio: {user['description'][:100]}...\n")
        
        # Test tweets fetch
        print(f"2️⃣ Fetching tweets...")
        tweets = client.get_user_tweets(test_handle, max_results=10)
        print(f"   ✅ Fetched {len(tweets)} tweets")
        
        if tweets:
            print(f"   Latest: {tweets[0]['text'][:80]}...")
            print(f"   Likes: {tweets[0]['public_metrics']['like_count']:,}")
            print(f"   Retweets: {tweets[0]['public_metrics']['retweet_count']:,}")
        
        print("\n🎉 All tests passed!")
        print("\n⚠️ Note: Each request waits 5 seconds due to free tier rate limit")
        
    except TwitterAPIError as e:
        print(f"\n❌ Test failed: {e}")


if __name__ == "__main__":
    test_client()