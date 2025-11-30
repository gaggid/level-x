# App Constants

# Colors
PRIMARY_COLOR = "#667eea"
SECONDARY_COLOR = "#764ba2"
BACKGROUND_DARK = "#0a0a0a"
CARD_BG = "#1a1a1a"
SUCCESS_COLOR = "#10b981"
WARNING_COLOR = "#f59e0b"
DANGER_COLOR = "#ef4444"

# Subscription Tiers
TIER_FREE = "free"
TIER_PRO = "pro"

# Analysis Limits
FREE_PEER_COUNT = 3  # CHANGED: Was 3, optimized for cost
PRO_PEER_COUNT = 5
DEEP_DIVE_PEER_COUNT = 8

# User Caps (Cost Protection)
MAX_FREE_USERS = 200  # NEW: Cap free tier to control costs
ENABLE_WAITLIST_AFTER_CAP = True  # NEW: Waitlist mode

# Follower Range for Matching (±30%)
FOLLOWER_MATCH_RANGE = 0.3

# Tweet Analysis Defaults
DEFAULT_TWEET_COUNT = 50
MAX_TWEET_COUNT = 100

# Cache TTL (Time to Live)
USER_CACHE_TTL_HOURS = 6   # NEW: User-specific cache
PEER_CACHE_TTL_HOURS = 24  # NEW: Peers change slowly, cache longer
POPULAR_PEER_CACHE_TTL_HOURS = 72  # NEW: Very popular peers cached even longer

# API Cost Estimates (in INR)
COST_PER_PROFILE = 0.015  # NEW: ₹0.015 per profile fetch
COST_PER_TWEET = 0.0001   # NEW: ₹0.0001 per tweet
ESTIMATED_COST_PER_ANALYSIS = 1.92  # NEW: With caching

# Niche Categories
NICHES = [
    "tech",
    "business",
    "marketing",
    "design",
    "writing",
    "productivity",
    "finance",
    "crypto",
    "ai",
    "health",
    "education",
    "entertainment",
    "sports",
    "other"
]

# Peer Pool Management
PEER_POOL_MIN_SIZE = 20  # NEW: Minimum verified peers per niche/range
PEER_POOL_REFRESH_DAYS = 7  # NEW: Re-validate peer pools weekly