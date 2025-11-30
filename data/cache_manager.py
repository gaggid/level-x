from db.models import TweetsCache
from db.connection import get_session
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import json
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages tweet caching to reduce API costs
    """
    
    def __init__(self, ttl_hours: int = 6):
        """
        Initialize cache manager
        
        Args:
            ttl_hours: Cache time-to-live in hours (default 6)
        """
        self.ttl_hours = ttl_hours
        logger.info(f"CacheManager initialized with {ttl_hours}h TTL")
    
    def get_cached_tweets(self, handle: str) -> Optional[List[Dict]]:
        """
        Retrieve cached tweets if not expired
        
        Args:
            handle: X username (without @)
        
        Returns:
            List of tweets if cache hit and valid, None otherwise
        """
        handle = handle.lstrip('@').lower()
        
        try:
            session = get_session()
            
            # Calculate expiration threshold
            expiration_time = datetime.utcnow() - timedelta(hours=self.ttl_hours)
            
            # Query for recent cache entry
            cache_entry = session.query(TweetsCache).filter(
                TweetsCache.x_handle == handle,
                TweetsCache.fetched_at > expiration_time
            ).order_by(TweetsCache.fetched_at.desc()).first()
            
            session.close()
            
            if cache_entry:
                tweets = json.loads(cache_entry.tweet_data)
                logger.info(f"✅ Cache HIT for @{handle} - {len(tweets)} tweets (fetched {cache_entry.fetched_at})")
                return tweets
            else:
                logger.info(f"❌ Cache MISS for @{handle}")
                return None
        
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            session.close()
            return None
    
    def cache_tweets(self, handle: str, tweets: List[Dict]) -> bool:
        """
        Store tweets in cache
        
        Args:
            handle: X username (without @)
            tweets: List of tweet dictionaries
        
        Returns:
            True if cached successfully, False otherwise
        """
        handle = handle.lstrip('@').lower()
        
        try:
            session = get_session()
            
            # Create cache entry
            cache_entry = TweetsCache(
                x_handle=handle,
                tweet_data=json.dumps(tweets),
                fetched_at=datetime.utcnow()
            )
            
            session.add(cache_entry)
            session.commit()
            session.close()
            
            logger.info(f"✅ Cached {len(tweets)} tweets for @{handle}")
            return True
        
        except Exception as e:
            logger.error(f"Error caching tweets: {e}")
            session.rollback()
            session.close()
            return False
    
    def invalidate_cache(self, handle: str) -> bool:
        """
        Force invalidate cache for a user
        
        Args:
            handle: X username (without @)
        
        Returns:
            True if invalidated, False otherwise
        """
        handle = handle.lstrip('@').lower()
        
        try:
            session = get_session()
            
            deleted_count = session.query(TweetsCache).filter(
                TweetsCache.x_handle == handle
            ).delete()
            
            session.commit()
            session.close()
            
            logger.info(f"✅ Invalidated cache for @{handle} ({deleted_count} entries deleted)")
            return True
        
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            session.rollback()
            session.close()
            return False
    
    def cleanup_old_cache(self, days_old: int = 7) -> int:
        """
        Clean up cache entries older than specified days
        
        Args:
            days_old: Delete entries older than this many days
        
        Returns:
            Number of entries deleted
        """
        try:
            session = get_session()
            
            threshold = datetime.utcnow() - timedelta(days=days_old)
            
            deleted_count = session.query(TweetsCache).filter(
                TweetsCache.fetched_at < threshold
            ).delete()
            
            session.commit()
            session.close()
            
            logger.info(f"✅ Cleaned up {deleted_count} old cache entries (>{days_old} days)")
            return deleted_count
        
        except Exception as e:
            logger.error(f"Error cleaning cache: {e}")
            session.rollback()
            session.close()
            return 0
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics
        
        Returns:
            Dict with cache stats
        """
        try:
            session = get_session()
            
            total_entries = session.query(TweetsCache).count()
            
            # Count fresh entries (within TTL)
            expiration_time = datetime.utcnow() - timedelta(hours=self.ttl_hours)
            fresh_entries = session.query(TweetsCache).filter(
                TweetsCache.fetched_at > expiration_time
            ).count()
            
            session.close()
            
            return {
                'total_entries': total_entries,
                'fresh_entries': fresh_entries,
                'stale_entries': total_entries - fresh_entries,
                'ttl_hours': self.ttl_hours
            }
        
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            session.close()
            return {}


# Test function
def test_cache():
    """Test cache manager"""
    cache = CacheManager(ttl_hours=6)
    
    # Test data
    test_handle = "testuser"
    test_tweets = [
        {'id': '1', 'text': 'Test tweet 1'},
        {'id': '2', 'text': 'Test tweet 2'}
    ]
    
    # Test cache write
    success = cache.cache_tweets(test_handle, test_tweets)
    print(f"Cache write: {'✅' if success else '❌'}")
    
    # Test cache read
    cached = cache.get_cached_tweets(test_handle)
    print(f"Cache read: {'✅' if cached else '❌'}")
    
    if cached:
        print(f"Retrieved {len(cached)} tweets")
    
    # Test stats
    stats = cache.get_cache_stats()
    print(f"Cache stats: {stats}")


if __name__ == "__main__":
    test_cache()