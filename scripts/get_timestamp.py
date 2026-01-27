#!/usr/bin/env python3
"""Get current timestamp in Asia/Bangkok timezone."""
from datetime import datetime, timezone, timedelta

# Asia/Bangkok is UTC+7
bangkok_tz = timezone(timedelta(hours=7))
now = datetime.now(bangkok_tz)
print(now.strftime("%Y-%m-%d %H:%M:%S"))
