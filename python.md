---
name: python
description: >
  Python coding standards và best practices cho Claude Code. Dùng khi viết, review,
  refactor, hoặc debug bất kỳ code Python nào — script nhỏ, web backend, data pipeline,
  CLI tool, hay test suite. PHẢI đọc skill này trước khi generate Python code. Bao gồm:
  project structure, code style, error handling, testing, dependency management, và
  các pattern tránh lỗi phổ biến.
---

# Python Coding Standards

## Triết lý

**Rõ ràng hơn thông minh.** Code Python tốt là code mà người khác (và bạn sau 6 tháng)
đọc được ngay không cần giải thích. Ưu tiên: readable → correct → performant.

---

## 1. Python Version & Tooling

```
Python: 3.11+ (dùng tính năng mới khi phù hợp: match/case, tomllib, etc.)
Package manager: uv (ưu tiên) hoặc pip + venv
Formatter: ruff format  (thay thế black)
Linter: ruff check      (thay thế flake8 + isort + pylint)
Type checker: mypy hoặc pyright
Test runner: pytest
```

### Setup nhanh project mới
```bash
uv init my-project
cd my-project
uv add --dev ruff mypy pytest pytest-cov
```

---

## 2. Project Structure

### Script đơn giản
```
my_script.py
README.md
requirements.txt  (hoặc pyproject.toml)
```

### Package / application
```
my_project/
├── pyproject.toml          # cấu hình project, deps, tools
├── README.md
├── .python-version         # pin python version (uv)
├── src/
│   └── my_project/
│       ├── __init__.py
│       ├── main.py         # entry point
│       ├── config.py       # settings / env vars
│       ├── models.py       # data models (dataclass / pydantic)
│       ├── services/       # business logic
│       │   ├── __init__.py
│       │   └── user_service.py
│       └── utils/
│           ├── __init__.py
│           └── helpers.py
├── tests/
│   ├── conftest.py
│   ├── test_main.py
│   └── services/
│       └── test_user_service.py
└── scripts/                # one-off scripts, không thuộc package
    └── seed_data.py
```

### pyproject.toml template
```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[project.scripts]
my-cli = "my_project.main:app"

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
```

---

## 3. Code Style

### Naming conventions
```python
# Variables & functions: snake_case
user_name = "alice"
def get_user_by_id(user_id: int) -> User: ...

# Classes: PascalCase
class UserService: ...
class HttpClient: ...

# Constants: SCREAMING_SNAKE_CASE (module level)
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30.0

# Private: single underscore prefix
def _validate_email(email: str) -> bool: ...

# "Magic" / dunder: double underscore (chỉ dùng khi cần thiết)
def __init__(self): ...
```

### Imports — thứ tự và grouping
```python
# 1. Standard library
import os
import sys
from pathlib import Path
from typing import Any

# 2. Third-party (blank line)
import httpx
from pydantic import BaseModel

# 3. Local (blank line)
from my_project.config import Settings
from my_project.models import User
```

Dùng `ruff check --select I --fix` để auto-sort.

### Type hints — LUÔN dùng
```python
# Tốt
def process_items(items: list[str], limit: int = 10) -> dict[str, int]:
    ...

# Tránh
def process_items(items, limit=10):
    ...

# Với Optional / Union (Python 3.10+)
def find_user(user_id: int) -> User | None:
    ...

# Với TypeAlias (Python 3.12+)
type UserId = int
type UserMap = dict[str, User]
```

### Docstrings
```python
def calculate_discount(price: float, percent: float) -> float:
    """Tính giá sau khi giảm.

    Args:
        price: Giá gốc (VND).
        percent: Phần trăm giảm, ví dụ 20 = giảm 20%.

    Returns:
        Giá sau khi đã áp dụng discount.

    Raises:
        ValueError: Nếu percent không nằm trong khoảng [0, 100].
    """
    if not 0 <= percent <= 100:
        raise ValueError(f"percent phải từ 0–100, nhận được {percent}")
    return price * (1 - percent / 100)
```

Dùng Google style (Args/Returns/Raises) cho hàm public. Hàm private ngắn có thể
bỏ qua docstring nếu tên hàm đủ rõ.

---

## 4. Data Models

### Dùng dataclass cho data đơn giản
```python
from dataclasses import dataclass, field

@dataclass
class Product:
    id: int
    name: str
    price: float
    tags: list[str] = field(default_factory=list)
    is_active: bool = True
```

### Dùng Pydantic cho validation / API models
```python
from pydantic import BaseModel, EmailStr, field_validator

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    age: int

    @field_validator("age")
    @classmethod
    def age_must_be_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError("age phải >= 0")
        return v
```

### Dùng Enum cho giá trị cố định
```python
from enum import StrEnum, auto

class OrderStatus(StrEnum):
    PENDING   = auto()  # "pending"
    CONFIRMED = auto()  # "confirmed"
    SHIPPED   = auto()  # "shipped"
    CANCELLED = auto()  # "cancelled"
```

---

## 5. Error Handling

### Custom exceptions — định nghĩa rõ ràng
```python
# exceptions.py
class AppError(Exception):
    """Base exception cho toàn bộ application."""

class NotFoundError(AppError):
    """Resource không tồn tại."""

class ValidationError(AppError):
    """Dữ liệu đầu vào không hợp lệ."""

class ExternalServiceError(AppError):
    """Lỗi từ service bên ngoài."""
    def __init__(self, service: str, message: str) -> None:
        self.service = service
        super().__init__(f"[{service}] {message}")
```

### Bắt lỗi đúng cách
```python
# Tốt: bắt lỗi cụ thể, xử lý có chủ đích
try:
    user = fetch_user(user_id)
except NotFoundError:
    return None
except ExternalServiceError as e:
    logger.error("External error: %s", e)
    raise

# Tránh: bắt hết mà không làm gì
try:
    do_something()
except Exception:
    pass  # ❌ nuốt lỗi

# Tránh: bắt Exception quá rộng ở business logic
try:
    do_something()
except Exception as e:  # ❌ quá rộng
    logger.error(e)
```

### Re-raise với context
```python
try:
    result = external_api.call()
except httpx.HTTPError as e:
    raise ExternalServiceError("payment-api", str(e)) from e
```

---

## 6. Logging

```python
import logging

# Module-level logger — KHÔNG dùng root logger
logger = logging.getLogger(__name__)

# Cấu hình ở entry point (main.py / app startup), không trong module
def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

# Dùng lazy % formatting, không f-string trong log calls
logger.info("Processing user %s", user_id)          # ✅
logger.info(f"Processing user {user_id}")            # ❌ (format ngay cả khi log bị tắt)

# Log level phù hợp
logger.debug("Cache hit for key: %s", key)           # dev detail
logger.info("User %s logged in", user.email)          # normal operation
logger.warning("Rate limit approaching: %d/min", n)   # cần chú ý
logger.error("Failed to send email: %s", err)         # lỗi không crash app
logger.critical("Database connection lost")           # cần action ngay
```

---

## 7. Configuration & Environment

```python
# config.py — dùng pydantic-settings
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    database_url: str
    secret_key: str
    debug: bool = False
    max_connections: int = 10
    allowed_origins: list[str] = ["http://localhost:3000"]

# Singleton — dùng lru_cache
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

```bash
# .env (không commit vào git)
DATABASE_URL=postgresql://user:pass@localhost/mydb
SECRET_KEY=supersecret

# .env.example (commit — làm template cho team)
DATABASE_URL=postgresql://user:pass@localhost/mydb
SECRET_KEY=change-me
```

---

## 8. File & Path Handling

```python
from pathlib import Path

# Luôn dùng pathlib, không dùng os.path
base_dir = Path(__file__).parent.parent
data_dir = base_dir / "data"
config_path = base_dir / "config" / "settings.toml"

# Đọc file an toàn
def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)

# Tạo thư mục nếu chưa có
output_dir = Path("output")
output_dir.mkdir(parents=True, exist_ok=True)

# Glob pattern
for csv_file in data_dir.glob("*.csv"):
    process(csv_file)
```

---

## 9. Testing với pytest

### Cấu trúc test
```python
# tests/test_discount.py
import pytest
from my_project.services import calculate_discount

class TestCalculateDiscount:
    def test_apply_10_percent(self):
        result = calculate_discount(price=100_000, percent=10)
        assert result == 90_000.0

    def test_full_discount(self):
        result = calculate_discount(price=100_000, percent=100)
        assert result == 0.0

    def test_zero_discount(self):
        result = calculate_discount(price=100_000, percent=0)
        assert result == 100_000.0

    def test_invalid_percent_raises(self):
        with pytest.raises(ValueError, match="phải từ 0–100"):
            calculate_discount(price=100_000, percent=101)

    @pytest.mark.parametrize("percent,expected", [
        (10, 90_000.0),
        (50, 50_000.0),
        (0,  100_000.0),
    ])
    def test_various_discounts(self, percent, expected):
        assert calculate_discount(100_000, percent) == expected
```

### Fixtures
```python
# tests/conftest.py
import pytest
from my_project.models import User

@pytest.fixture
def sample_user() -> User:
    return User(id=1, name="Alice", email="alice@example.com")

@pytest.fixture
def mock_db(monkeypatch):
    """Patch database calls."""
    def fake_query(sql): return []
    monkeypatch.setattr("my_project.db.execute", fake_query)
```

### Mock external calls
```python
from unittest.mock import patch, MagicMock

def test_send_email_calls_smtp(mock_smtp):
    with patch("my_project.email.smtplib.SMTP") as mock_smtp:
        send_welcome_email("user@example.com")
        mock_smtp.return_value.__enter__.return_value.send_message.assert_called_once()
```

### Chạy tests
```bash
pytest                          # toàn bộ
pytest tests/test_discount.py   # file cụ thể
pytest -k "test_invalid"        # filter theo tên
pytest --cov=src --cov-report=term-missing  # với coverage
```

---

## 10. Patterns Hay Dùng

### Context manager
```python
from contextlib import contextmanager

@contextmanager
def timer(label: str):
    import time
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.debug("%s took %.3fs", label, elapsed)

# Dùng:
with timer("db query"):
    results = db.execute(query)
```

### Retry decorator
```python
import time
from functools import wraps
from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable)

def retry(times: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == times:
                        raise
                    logger.warning("Attempt %d/%d failed: %s", attempt, times, e)
                    time.sleep(delay * attempt)
        return wrapper  # type: ignore[return-value]
    return decorator

# Dùng:
@retry(times=3, delay=0.5, exceptions=(httpx.HTTPError,))
def fetch_data(url: str) -> dict: ...
```

### Batch processing
```python
from itertools import islice
from typing import Iterable, TypeVar

T = TypeVar("T")

def batched(iterable: Iterable[T], size: int) -> Iterable[list[T]]:
    """Chia iterable thành batches kích thước cố định."""
    it = iter(iterable)
    while batch := list(islice(it, size)):
        yield batch

# Dùng:
for batch in batched(all_users, size=100):
    process_batch(batch)
```

---

## 11. Những Điều TRÁNH

```python
# ❌ Mutable default argument
def append_item(items: list = []):  # bug kinh điển
    items.append(1)
    return items

# ✅ Đúng
def append_item(items: list | None = None):
    if items is None:
        items = []
    items.append(1)
    return items

# ❌ Bare except
try:
    risky()
except:  # bắt cả KeyboardInterrupt, SystemExit
    pass

# ✅ Đúng
try:
    risky()
except ValueError as e:
    handle(e)

# ❌ String concatenation trong loop
result = ""
for item in items:
    result += str(item)  # O(n²)

# ✅ Đúng
result = "".join(str(item) for item in items)

# ❌ Import * (ô nhiễm namespace)
from os.path import *

# ✅ Đúng
from pathlib import Path

# ❌ Global state mutation
_cache = {}
def get(key):
    if key not in _cache:
        _cache[key] = fetch(key)  # side effect ẩn
    return _cache[key]

# ✅ Tốt hơn: truyền cache vào, hoặc dùng lru_cache
from functools import lru_cache

@lru_cache(maxsize=256)
def get(key: str) -> str:
    return fetch(key)

# ❌ Magic numbers
if user.age >= 18:  # 18 là gì?

# ✅ Đúng
LEGAL_AGE = 18
if user.age >= LEGAL_AGE:
```

---

## 12. CLI Tools (với typer hoặc argparse)

```python
# Dùng typer cho CLI hiện đại
import typer

app = typer.Typer()

@app.command()
def process(
    input_file: typer.FileText = typer.Argument(..., help="File CSV đầu vào"),
    output: Path = typer.Option(Path("output.json"), help="File output"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Xử lý file CSV và xuất JSON."""
    if verbose:
        setup_logging("DEBUG")
    # ...

if __name__ == "__main__":
    app()
```

---

## 13. Async Python

```python
import asyncio
import httpx

# Dùng async/await khi có I/O bound tasks
async def fetch_all(urls: list[str]) -> list[dict]:
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
    return [r.json() for r in responses if not isinstance(r, Exception)]

# Entry point async
async def main() -> None:
    results = await fetch_all(["https://api.example.com/1", "https://api.example.com/2"])
    print(results)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 14. Checklist trước khi commit

- [ ] Type hints đầy đủ cho tất cả functions/methods public
- [ ] Không có bare `except:` hay `except Exception: pass`
- [ ] Imports được sort và grouped đúng (`ruff check --select I`)
- [ ] Không có magic numbers — dùng constants có tên
- [ ] Log messages dùng `%s` format, không f-string
- [ ] Custom exceptions kế thừa từ base exception của app
- [ ] Tests cover happy path + edge cases + error cases
- [ ] `.env` không bị commit (có trong `.gitignore`)
- [ ] `pathlib.Path` thay vì `os.path`
- [ ] `ruff format .` đã chạy
