import os
import sys

# Ensure backend directory is in python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

# Test cases
test_cases = [
    # Case 1: Standard URL string
    "http://localhost:7860",
    # Case 2: Comma separated string
    "http://localhost:7860,http://localhost:3000",
    # Case 3: JSON array representation
    '["http://localhost:7860"]',
    # Case 4: JSON array representation with multiple origins
    '["http://localhost:7860", "http://localhost:3000"]',
    # Case 5: Empty/None
    "",
    # Case 6: Star
    "*"
]

for i, test_value in enumerate(test_cases, 1):
    os.environ["ALLOWED_ORIGINS"] = test_value
    try:
        from app.config import Settings
        settings = Settings()
        print(f"Test {i}: ALLOWED_ORIGINS={repr(test_value)} -> settings.allowed_origins={settings.allowed_origins} (SUCCESS)")
    except Exception as e:
        print(f"Test {i}: ALLOWED_ORIGINS={repr(test_value)} -> FAILED with: {type(e).__name__}: {e}")
