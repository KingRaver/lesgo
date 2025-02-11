import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# Analysis Configuration
MAX_TIERS = int(os.getenv('MAX_TIERS', 4))
UPDATE_FREQUENCY = int(os.getenv('UPDATE_FREQUENCY', 3600))
BACKTEST_DAYS = int(os.getenv('BACKTEST_DAYS', 90))

# Data Storage
DATA_STORAGE_PATH = os.getenv('DATA_STORAGE_PATH', './data/processed')
Path(DATA_STORAGE_PATH).mkdir(parents=True, exist_ok=True)

# Analysis Parameters
ANALYSIS_PARAMS = {
    'volume_threshold': float(os.getenv('VOLUME_THRESHOLD', 2.0)),
    'correlation_threshold': float(os.getenv('CORRELATION_THRESHOLD', 0.7)),
    'min_confidence': float(os.getenv('MIN_CONFIDENCE', 0.6)),
    'lookback_periods': 30
}

# Tier-specific Parameters
TIER_PARAMS = {
    tier: {
        'position_size_adjustment': 1.0 - (tier * 0.15),  # Decrease size for lower tiers
        'stop_loss_multiplier': 0.05 * (tier + 1),       # Wider stops for lower tiers
        'take_profit_multiplier': 0.15 * (tier + 1),     # Higher targets for lower tiers
        'confidence_adjustment': 1.0 + (tier * 0.05)     # Higher confidence needed for lower tiers
    }
    for tier in range(MAX_TIERS)
}

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'crypto_analysis.log')

# Ensure the log directory exists
log_path = Path(LOG_FILE).parent
log_path.mkdir(parents=True, exist_ok=True)
