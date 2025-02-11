crypto_tier_analyzer/
├── .env                          # Environment variables
├── requirements.txt              # Project dependencies
├── README.md                     # Project documentation
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py          # Configuration settings
│   ├── data/
│   │   ├── __init__.py
│   │   ├── coingecko_api.py     # CoinGecko API handler
│   │   └── data_processor.py    # Data processing utilities
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── rotation_detector.py  # Rotation detection logic
│   │   └── smart_money.py       # Smart money indicators
│   ├── backtesting/
│   │   ├── __init__.py
│   │   ├── backtest_engine.py   # Backtesting engine
│   │   └── optimizer.py         # Parameter optimization
│   └── visualization/
│       ├── __init__.py
│       └── tableau_export.py    # Tableau data preparation
└── tests/
    ├── __init__.py
    └── test_rotation_detector.py # Unit tests
