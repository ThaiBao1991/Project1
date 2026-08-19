# generate_python_roadmap_v2.py
# Python RoadMap Full — Lộ trình học TOÀN BỘ Python (Foundation -> Pro), chu kỳ Ultimate.
# Mỗi topic: 30 ngày (mặc định) hoặc 45 ngày (topic lớn). Mỗi ngày ~60 phút.
# Cấu trúc dữ liệu TOPICS có prerequisites -> sắp xếp topo. Review Day mỗi 5 topic. Capstone cuối.
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILEPATH = os.path.join(BASE_DIR, "PythonRoadMapFull.md")

UNIT_DAYS_DEFAULT = 30
UNIT_DAYS_DEEP = 45

# Mỗi topic: (id, section, short_section, title, keywords, prerequisites, days)
# sections: F=Foundation, A=Advanced, W=Web, D=Data&AI, O=DevOps&Cloud, S=Specialized
TOPICS = [
    # ============ PHASE 1: FOUNDATION (bắt đầu từ 0) ============
    ("setup_git", "F", "Foundation", "Cài đặt Python, VS Code, Git & Tư duy lập trình",
     ["#setup", "#python", "#git"], [], UNIT_DAYS_DEFAULT),
    ("interpreter_repl", "F", "Foundation", "Python Interpreter, REPL, Jupyter Notebook, IPython",
     ["#setup", "#repl"], ["setup_git"], UNIT_DAYS_DEFAULT),
    ("variables_types", "F", "Foundation", "Biến & Kiểu dữ liệu: int, float, str, bool, None",
     ["#syntax", "#datatypes"], ["interpreter_repl"], UNIT_DAYS_DEFAULT),
    ("operators", "F", "Foundation", "Phép tính số học, Toán tử so sánh, Toán tử logic",
     ["#syntax", "#operators"], ["variables_types"], UNIT_DAYS_DEFAULT),
    ("strings", "F", "Foundation", "String: Index, Slice, f-string, format, join, split, replace",
     ["#strings"], ["variables_types"], UNIT_DAYS_DEFAULT),
    ("io_print", "F", "Foundation", "Input/Output: print, input, sep/end, repr vs str",
     ["#io", "#print"], ["variables_types"], UNIT_DAYS_DEFAULT),
    ("conditionals", "F", "Foundation", "Câu lệnh điều kiện: if, elif, else, Ternary Operator",
     ["#control", "#if"], ["operators"], UNIT_DAYS_DEFAULT),
    ("loops", "F", "Foundation", "Vòng lặp for/while: range, enumerate, zip, break, continue, List Comprehension",
     ["#loops"], ["conditionals"], UNIT_DAYS_DEFAULT),
    ("functions", "F", "Foundation", "Hàm: def, return, Default/Keyword/Positional args",
     ["#functions"], ["loops"], UNIT_DAYS_DEFAULT),
    ("functions_adv", "F", "Foundation", "Hàm nâng cao: *args, **kwargs, Lambda, map, filter, reduce",
     ["#functions", "#lambda"], ["functions"], UNIT_DAYS_DEFAULT),
    ("scope_legb", "F", "Foundation", "Phạm vi biến: Local, Enclosing, Global, Built-in (LEGB rule), nonlocal",
     ["#scope", "#legb"], ["functions_adv"], UNIT_DAYS_DEFAULT),
    ("lists", "F", "Foundation", "List: Methods, Slicing, Nested List, Copy vs Reference",
     ["#list"], ["variables_types"], UNIT_DAYS_DEFAULT),
    ("tuples", "F", "Foundation", "Tuple: Immutability, Packing/Unpacking, Named Tuple",
     ["#tuple"], ["lists"], UNIT_DAYS_DEFAULT),
    ("dicts", "F", "Foundation", "Dictionary: CRUD, dict comprehension, defaultdict, Counter, OrderedDict",
     ["#dict"], ["lists"], UNIT_DAYS_DEFAULT),
    ("sets", "F", "Foundation", "Set: union, intersection, difference, frozenset",
     ["#set"], ["lists"], UNIT_DAYS_DEFAULT),
    ("collections", "F", "Foundation", "Cấu trúc dữ liệu nâng cao: deque, heap, stack, queue (collections, heapq)",
     ["#collections", "#heapq"], ["dicts", "sets"], UNIT_DAYS_DEFAULT),
    ("oop_basic", "F", "Foundation", "OOP: Class, Object, __init__, Attributes, Methods, self",
     ["#oop", "#class"], ["functions", "scope_legb"], UNIT_DAYS_DEFAULT),
    ("oop_inheritance", "F", "Foundation", "OOP: Kế thừa (Inheritance), super(), Đa kế thừa (MRO)",
     ["#oop", "#inheritance"], ["oop_basic"], UNIT_DAYS_DEFAULT),
    ("oop_polymorphism", "F", "Foundation", "OOP: Encapsulation, Polymorphism, Duck Typing, Abstract",
     ["#oop", "#polymorphism"], ["oop_inheritance"], UNIT_DAYS_DEFAULT),
    ("oop_dunder", "F", "Foundation", "OOP: Dunder methods __str__, __repr__, __len__, __eq__, __lt__...",
     ["#oop", "#dunder"], ["oop_basic"], UNIT_DAYS_DEFAULT),
    ("oop_property", "F", "Foundation", "OOP: @property, @classmethod, @staticmethod, __slots__",
     ["#oop", "#property"], ["oop_dunder"], UNIT_DAYS_DEFAULT),
    ("oop_abc_dataclass", "F", "Foundation", "ABC, Protocol (Structural Subtyping), Dataclass, field(), frozen, post_init",
     ["#oop", "#abc", "#dataclass"], ["oop_property"], UNIT_DAYS_DEFAULT),
    ("exceptions", "F", "Foundation", "Exception Handling: try, except, else, finally, raise, Custom Exception",
     ["#exception"], ["functions"], UNIT_DAYS_DEFAULT),
    ("file_io", "F", "Foundation", "File I/O: open, read, write, with, pathlib.Path",
     ["#file", "#io", "#pathlib"], ["exceptions"], UNIT_DAYS_DEFAULT),
    ("json_csv_yaml", "F", "Foundation", "JSON, CSV, YAML: đọc, ghi, parse với json, csv, pyyaml",
     ["#json", "#csv", "#yaml"], ["file_io"], UNIT_DAYS_DEFAULT),
    ("modules_packages", "F", "Foundation", "Module & Package: import, __name__, __all__, __init__.py, pip, venv, pyproject.toml",
     ["#modules", "#pip", "#venv"], ["functions", "scope_legb"], UNIT_DAYS_DEFAULT),
    ("stdlib_core", "F", "Foundation", "Thư viện chuẩn: os, sys, shutil, glob, re, datetime, math, random",
     ["#stdlib"], ["modules_packages"], UNIT_DAYS_DEFAULT),
    ("stdlib_adv", "F", "Foundation", "Thư viện chuẩn nâng cao: itertools, functools, contextlib, abc",
     ["#stdlib", "#itertools"], ["stdlib_core"], UNIT_DAYS_DEFAULT),
    ("type_hints", "F", "Foundation", "Type Hints & typing: Any, Union, Optional, TypeVar, Generic, Literal, TypedDict",
     ["#typing", "#type_hints"], ["functions_adv"], UNIT_DAYS_DEFAULT),
    ("mypy", "F", "Foundation", "Mypy: Static Type Checking, Strict mode, Type narrowing",
     ["#mypy", "#static_typing"], ["type_hints"], UNIT_DAYS_DEFAULT),

    # ============ PHASE 2: ADVANCED & PATTERNS ============
    ("decorators", "A", "Advanced", "Decorator: Function/Class Decorator, Stacking, wraps, functools",
     ["#decorator"], ["scope_legb", "functions_adv"], UNIT_DAYS_DEFAULT),
    ("generators", "A", "Advanced", "Generator: yield, Generator Expression, send(), Lazy Evaluation",
     ["#generator", "#yield"], ["decorators"], UNIT_DAYS_DEFAULT),
    ("iterator_protocol", "A", "Advanced", "Iterator Protocol: __iter__, __next__, StopIteration",
     ["#iterator"], ["generators"], UNIT_DAYS_DEFAULT),
    ("context_manager", "A", "Advanced", "Context Manager: with, __enter__, __exit__, contextmanager",
     ["#context_manager"], ["exceptions"], UNIT_DAYS_DEFAULT),
    ("metaclass", "A", "Advanced", "Metaclass: type, __new__, __init_subclass__, ABC internals",
     ["#metaclass"], ["oop_dunder"], UNIT_DAYS_DEFAULT),
    ("descriptor", "A", "Advanced", "Descriptor Protocol: __get__, __set__, __delete__ — cách @property hoạt động",
     ["#descriptor"], ["oop_property"], UNIT_DAYS_DEFAULT),
    ("functional", "A", "Advanced", "Functional Programming: Immutability, pure functions, partial, compose",
     ["#functional"], ["generators"], UNIT_DAYS_DEFAULT),
    ("memory_mgmt", "A", "Advanced", "Memory Management: Reference Counting, GC, weakref, sys.getsizeof, __slots__",
     ["#memory", "#gc"], ["descriptor"], UNIT_DAYS_DEFAULT),
    ("cpython_internals", "A", "Advanced", "CPython Internals: Bytecode, dis, PVM, GIL, code objects",
     ["#cpython", "#gil", "#bytecode"], ["memory_mgmt"], UNIT_DAYS_DEEP),
    ("modern_syntax", "A", "Advanced", "Walrus (:=), Structural Pattern Matching (match/case), Python 3.11+ features",
     ["#python311", "#pattern_matching"], ["conditionals", "exceptions"], UNIT_DAYS_DEFAULT),
    ("threading", "A", "Advanced", "Threading: Thread, Lock, Event, Semaphore, RLock, Thread-safe",
     ["#threading"], ["exceptions", "memory_mgmt"], UNIT_DAYS_DEFAULT),
    ("multiprocessing", "A", "Advanced", "Multiprocessing: Process, Pool, Queue, Pipe, Manager, shared memory",
     ["#multiprocessing"], ["threading"], UNIT_DAYS_DEFAULT),
    ("concurrent_futures", "A", "Advanced", "concurrent.futures: ThreadPoolExecutor, ProcessPoolExecutor, as_completed",
     ["#concurrent_futures"], ["threading", "multiprocessing"], UNIT_DAYS_DEFAULT),
    ("asyncio", "A", "Advanced", "AsyncIO: event loop, async/await, coroutine, Task, gather, asyncio.run",
     ["#asyncio"], ["generators", "threading"], UNIT_DAYS_DEFAULT),
    ("asyncio_adv", "A", "Advanced", "AsyncIO nâng cao: Queue, Semaphore, timeout, shield, TaskGroup, cancellation",
     ["#asyncio", "#advanced"], ["asyncio"], UNIT_DAYS_DEEP),
    ("aiohttp", "A", "Advanced", "aiohttp: Async HTTP client/server, Session, WebSocket async",
     ["#aiohttp", "#async"], ["asyncio"], UNIT_DAYS_DEFAULT),
    ("solid", "A", "Advanced", "SOLID Principles trong Python — viết code sạch, dễ mở rộng",
     ["#solid", "#clean_code"], ["oop_polymorphism", "oop_abc_dataclass"], UNIT_DAYS_DEFAULT),
    ("patterns_creational", "A", "Advanced", "Creational Patterns: Singleton, Factory, Abstract Factory, Builder, Prototype",
     ["#patterns", "#creational"], ["solid"], UNIT_DAYS_DEFAULT),
    ("patterns_structural", "A", "Advanced", "Structural Patterns: Adapter, Bridge, Composite, Decorator, Facade, Proxy",
     ["#patterns", "#structural"], ["solid"], UNIT_DAYS_DEFAULT),
    ("patterns_behavioral", "A", "Advanced", "Behavioral Patterns: Observer, Strategy, Command, Iterator, State, Template Method",
     ["#patterns", "#behavioral"], ["solid"], UNIT_DAYS_DEFAULT),
    ("repository_di", "A", "Advanced", "Repository Pattern, Unit of Work, Dependency Injection trong Python",
     ["#patterns", "#di", "#repository"], ["patterns_creational", "patterns_structural"], UNIT_DAYS_DEFAULT),
    ("unittest", "A", "Advanced", "Unit Testing: unittest, assertions, setUp/tearDown, TestCase",
     ["#testing", "#unittest"], ["exceptions"], UNIT_DAYS_DEFAULT),
    ("pytest", "A", "Advanced", "pytest: fixtures, conftest, parametrize, marks, plugins",
     ["#pytest"], ["unittest"], UNIT_DAYS_DEFAULT),
    ("mocking", "A", "Advanced", "Mocking: unittest.mock, MagicMock, patch, side_effect, Mock trong pytest",
     ["#mock", "#testing"], ["pytest"], UNIT_DAYS_DEFAULT),
    ("tdd", "A", "Advanced", "TDD: Test-Driven Development — Red, Green, Refactor workflow",
     ["#tdd"], ["pytest"], UNIT_DAYS_DEFAULT),
    ("coverage", "A", "Advanced", "Coverage: coverage.py, pytest-cov, Branch coverage, CI integration",
     ["#coverage"], ["pytest"], UNIT_DAYS_DEFAULT),
    ("integration_e2e", "A", "Advanced", "Integration Testing, E2E Testing với pytest + Docker",
     ["#integration_testing"], ["pytest", "tdd"], UNIT_DAYS_DEFAULT),
    ("profiling", "A", "Advanced", "Profiling: cProfile, line_profiler, memory_profiler, Py-Spy",
     ["#profiling", "#performance"], ["memory_mgmt"], UNIT_DAYS_DEFAULT),
    ("optimization", "A", "Advanced", "Tối ưu Python: List vs Generator, local lookup, caching, micro-optim",
     ["#optimization"], ["profiling", "generators"], UNIT_DAYS_DEFAULT),
    ("cython", "A", "Advanced", "Cython: Biên dịch Python sang C — tốc độ như C",
     ["#cython"], ["cpython_internals"], UNIT_DAYS_DEFAULT),
    ("numba", "A", "Advanced", "Numba: JIT compilation, @jit, @njit, Parallel, GPU (CUDA)",
     ["#numba", "#jit"], ["cython"], UNIT_DAYS_DEFAULT),
    ("ctypes_cffi", "A", "Advanced", "ctypes, cffi: Gọi hàm C từ Python — Tích hợp C extension",
     ["#ctypes", "#cffi"], ["cpython_internals"], UNIT_DAYS_DEFAULT),
    ("pypy", "A", "Advanced", "PyPy: Python nhanh hơn với JIT — Khi nào dùng PyPy vs CPython",
     ["#pypy"], ["cpython_internals"], UNIT_DAYS_DEFAULT),

    # ============ PHASE 3: WEB DEVELOPMENT ============
    ("http", "W", "Web Dev", "HTTP Protocol: Methods, Status codes, Headers, REST vs GraphQL vs gRPC",
     ["#http", "#rest"], [], UNIT_DAYS_DEFAULT),
    ("requests", "W", "Web Dev", "requests: GET/POST/PUT/DELETE, Session, Auth, Retry, Timeout, SSL",
     ["#requests", "#http_client"], ["http"], UNIT_DAYS_DEFAULT),
    ("httpx", "W", "Web Dev", "httpx: Async HTTP client, HTTP/2, retry middleware",
     ["#httpx", "#async"], ["requests", "asyncio"], UNIT_DAYS_DEFAULT),
    ("fastapi_basic", "W", "Web Dev", "FastAPI: Setup, Path/Query params, Request Body, Response Model",
     ["#fastapi"], ["http", "type_hints"], UNIT_DAYS_DEFAULT),
    ("pydantic", "W", "Web Dev", "Pydantic v2: BaseModel, Field, validators, model_validator, Serialize",
     ["#fastapi", "#pydantic"], ["fastapi_basic"], UNIT_DAYS_DEFAULT),
    ("fastapi_advanced", "W", "Web Dev", "FastAPI: Dependency Injection, Security (OAuth2, JWT, API Key)",
     ["#fastapi", "#security", "#jwt"], ["fastapi_basic", "pydantic"], UNIT_DAYS_DEFAULT),
    ("fastapi_middleware", "W", "Web Dev", "FastAPI: BackgroundTask, Middleware, CORS, Static, Lifespan, WebSocket, SSE",
     ["#fastapi", "#middleware"], ["fastapi_advanced"], UNIT_DAYS_DEFAULT),
    ("fastapi_testing", "W", "Web Dev", "FastAPI: Testing với TestClient, pytest, Mock dependencies",
     ["#fastapi", "#testing"], ["fastapi_basic", "pytest"], UNIT_DAYS_DEFAULT),
    ("fastapi_deploy", "W", "Web Dev", "FastAPI: Deploy Uvicorn, Gunicorn, Docker, Nginx reverse proxy",
     ["#fastapi", "#deploy"], ["fastapi_advanced"], UNIT_DAYS_DEFAULT),
    ("django_basic", "W", "Web Dev", "Django: MTV Architecture, settings, URL routing, Apps",
     ["#django"], ["http"], UNIT_DAYS_DEFAULT),
    ("django_orm", "W", "Web Dev", "Django ORM: Models, Field types, Migrations, queryset, F/Q objects",
     ["#django", "#orm"], ["django_basic"], UNIT_DAYS_DEFAULT),
    ("django_orm_adv", "W", "Web Dev", "Django ORM nâng cao: select_related, prefetch_related, annotate, aggregate",
     ["#django", "#orm", "#advanced"], ["django_orm"], UNIT_DAYS_DEFAULT),
    ("django_views", "W", "Web Dev", "Django Views: FBV, CBV, Mixins, Generic Views",
     ["#django", "#views"], ["django_basic"], UNIT_DAYS_DEFAULT),
    ("django_templates", "W", "Web Dev", "Django Templates: Template language, Inheritance, Tags, Filters",
     ["#django", "#templates"], ["django_basic"], UNIT_DAYS_DEFAULT),
    ("django_forms", "W", "Web Dev", "Django Forms: ModelForm, Validation, Widgets, Formsets, CSRF",
     ["#django", "#forms"], ["django_views"], UNIT_DAYS_DEFAULT),
    ("django_auth", "W", "Web Dev", "Django Auth: User model, Custom User, Permissions, Groups",
     ["#django", "#auth"], ["django_views"], UNIT_DAYS_DEFAULT),
    ("drf", "W", "Web Dev", "Django REST Framework (DRF): Serializers, ViewSets, Routers, Permissions",
     ["#drf", "#api"], ["django_orm", "django_views"], UNIT_DAYS_DEEP),
    ("drf_adv", "W", "Web Dev", "DRF nâng cao: Throttling, Pagination, Filtering, JWT với Simple JWT",
     ["#drf", "#jwt"], ["drf"], UNIT_DAYS_DEFAULT),
    ("django_channels", "W", "Web Dev", "Django Channels: WebSocket, ASGI, Layer, Consumer, Groups",
     ["#django", "#websocket", "#channels"], ["drf", "asyncio"], UNIT_DAYS_DEFAULT),
    ("django_celery", "W", "Web Dev", "Django Celery: Task queue, Beat scheduler, Redis broker, Flower",
     ["#celery", "#task_queue"], ["django_orm"], UNIT_DAYS_DEFAULT),
    ("django_testing", "W", "Web Dev", "Django Testing: TestCase, Client, Factory Boy, pytest-django",
     ["#django", "#testing"], ["django_orm", "pytest"], UNIT_DAYS_DEFAULT),
    ("django_production", "W", "Web Dev", "Django Production: Caching, Static/Media, Security, Scale",
     ["#django", "#production"], ["django_basic"], UNIT_DAYS_DEFAULT),
    ("flask", "W", "Web Dev", "Flask: Routes, Templates (Jinja2), Request/Response, Blueprints",
     ["#flask"], ["http"], UNIT_DAYS_DEFAULT),
    ("flask_adv", "W", "Web Dev", "Flask: SQLAlchemy integration, Flask-Login, Flask-WTF, Flask-Mail",
     ["#flask", "#extensions"], ["flask"], UNIT_DAYS_DEFAULT),
    ("bs4", "W", "Web Dev", "BeautifulSoup4: Parse HTML/XML, CSS selectors, Tag navigation",
     ["#beautifulsoup", "#scraping"], ["requests"], UNIT_DAYS_DEFAULT),
    ("scrapy", "W", "Web Dev", "Scrapy: Spider, Item, Pipeline, Middleware, CrawlSpider, Settings",
     ["#scrapy"], ["bs4"], UNIT_DAYS_DEFAULT),
    ("playwright", "W", "Web Dev", "Playwright Python: Browser automation, Page, Locator, Screenshot, Network",
     ["#playwright", "#automation"], ["bs4"], UNIT_DAYS_DEFAULT),
    ("selenium", "W", "Web Dev", "Selenium: WebDriver, Waits, Actions, Headless, Grid, Anti-detection",
     ["#selenium"], ["playwright"], UNIT_DAYS_DEFAULT),
    ("antibot", "W", "Web Dev", "Anti-bot: Proxy rotation, User-Agent, Captcha solving, Rate limiting",
     ["#scraping", "#antibot"], ["scrapy", "selenium"], UNIT_DAYS_DEFAULT),
    ("sql_adv", "W", "Web Dev", "SQL nâng cao: JOIN, Subquery, CTE, Window Functions, Index, Explain",
     ["#sql", "#advanced"], [], UNIT_DAYS_DEFAULT),
    ("sqlalchemy", "W", "Web Dev", "SQLAlchemy Core + ORM: Engine, Session, Relationship, Lazy/Eager",
     ["#sqlalchemy", "#orm"], ["sql_adv"], UNIT_DAYS_DEFAULT),
    ("alembic", "W", "Web Dev", "Alembic: Database Migration, Auto-generate, Upgrade/Downgrade",
     ["#alembic", "#migration"], ["sqlalchemy"], UNIT_DAYS_DEFAULT),
    ("sqlmodel", "W", "Web Dev", "SQLModel: FastAPI + SQLAlchemy unified (Pydantic + ORM)",
     ["#sqlmodel"], ["sqlalchemy", "pydantic"], UNIT_DAYS_DEFAULT),
    ("postgresql", "W", "Web Dev", "PostgreSQL nâng cao: JSONB, Full-text Search, pg_trgm, Partitioning",
     ["#postgresql"], ["sql_adv"], UNIT_DAYS_DEFAULT),
    ("mongodb", "W", "Web Dev", "MongoDB với PyMongo/Motor: CRUD, Aggregation pipeline, Index",
     ["#mongodb", "#motor"], [], UNIT_DAYS_DEFAULT),
    ("redis", "W", "Web Dev", "Redis với redis-py/aioredis: Cache, Pub/Sub, Stream, Sorted Set",
     ["#redis", "#cache"], [], UNIT_DAYS_DEFAULT),
    ("elasticsearch", "W", "Web Dev", "Elasticsearch với Python: Indexing, Query DSL, Aggregation, Vector Search",
     ["#elasticsearch"], [], UNIT_DAYS_DEFAULT),

    # ============ PHASE 4: DATA SCIENCE & ML/AI ============
    ("numpy", "D", "Data & AI", "NumPy: ndarray, Broadcasting, Vectorization, Advanced Indexing, Linear Algebra",
     ["#numpy"], [], UNIT_DAYS_DEFAULT),
    ("pandas", "D", "Data & AI", "Pandas: Series, DataFrame, IO (CSV/Excel/Parquet), Index, MultiIndex",
     ["#pandas"], ["numpy"], UNIT_DAYS_DEFAULT),
    ("pandas_adv", "D", "Data & AI", "Pandas nâng cao: groupby, merge/join, pivot_table, resample, apply, Styler",
     ["#pandas", "#advanced"], ["pandas"], UNIT_DAYS_DEFAULT),
    ("data_cleaning", "D", "Data & AI", "Data Cleaning: Missing values, Outlier detection, Dtype optimization",
     ["#data_cleaning"], ["pandas"], UNIT_DAYS_DEFAULT),
    ("eda", "D", "Data & AI", "EDA: Descriptive stats, Correlation, Distribution, Insight storytelling",
     ["#eda"], ["pandas_adv"], UNIT_DAYS_DEFAULT),
    ("matplotlib", "D", "Data & AI", "Matplotlib: Figure, Axes, subplots, line/bar/scatter/hist/pie",
     ["#matplotlib", "#visualization"], ["numpy"], UNIT_DAYS_DEFAULT),
    ("seaborn", "D", "Data & AI", "Seaborn: Statistical plots, heatmap, pairplot, FacetGrid, Theme",
     ["#seaborn"], ["matplotlib"], UNIT_DAYS_DEFAULT),
    ("plotly_dash", "D", "Data & AI", "Plotly & Dash: Interactive charts, Choropleth, 3D, Dashboard",
     ["#plotly", "#dash"], ["matplotlib"], UNIT_DAYS_DEFAULT),
    ("polars", "D", "Data & AI", "Polars: DataFrame nhanh hơn Pandas 10x — Lazy, Expressions, Streaming",
     ["#polars"], ["pandas"], UNIT_DAYS_DEFAULT),
    ("ml_fundamentals", "D", "Data & AI", "ML Fundamentals: Supervised/Unsupervised/RL, Bias-Variance, Overfitting",
     ["#ml", "#fundamentals"], ["numpy"], UNIT_DAYS_DEFAULT),
    ("sklearn", "D", "Data & AI", "Scikit-learn: API (fit/predict), Pipeline, ColumnTransformer, Cross-validation",
     ["#sklearn"], ["ml_fundamentals"], UNIT_DAYS_DEFAULT),
    ("classification", "D", "Data & AI", "Classification: Logistic Regression, SVM, KNN, Decision Tree, Random Forest",
     ["#sklearn", "#classification"], ["sklearn"], UNIT_DAYS_DEFAULT),
    ("regression", "D", "Data & AI", "Regression: Linear, Ridge, Lasso, ElasticNet, SVR, Polynomial",
     ["#sklearn", "#regression"], ["sklearn"], UNIT_DAYS_DEFAULT),
    ("ensemble", "D", "Data & AI", "Ensemble: Bagging, Boosting, Voting, Stacking, XGBoost, LightGBM, CatBoost",
     ["#ensemble", "#xgboost"], ["classification", "regression"], UNIT_DAYS_DEFAULT),
    ("clustering", "D", "Data & AI", "Clustering: KMeans, DBSCAN, Agglomerative, Gaussian Mixture Models",
     ["#clustering"], ["sklearn"], UNIT_DAYS_DEFAULT),
    ("dimensionality", "D", "Data & AI", "Dimensionality Reduction: PCA, t-SNE, UMAP, Feature Selection",
     ["#pca", "#umap"], ["sklearn"], UNIT_DAYS_DEFAULT),
    ("hyperparameter", "D", "Data & AI", "Hyperparameter Tuning: GridSearchCV, RandomizedSearchCV, Optuna, Ray Tune",
     ["#hyperparameter", "#optuna"], ["ensemble"], UNIT_DAYS_DEFAULT),
    ("feature_engineering", "D", "Data & AI", "Feature Engineering: Encoding, Scaling, Text/Time features, Target encoding",
     ["#feature_engineering"], ["sklearn"], UNIT_DAYS_DEFAULT),
    ("model_evaluation", "D", "Data & AI", "Model Evaluation: Metrics (AUC, F1, MAE, RMSE), Confusion Matrix, Calibration",
     ["#evaluation"], ["classification", "regression"], UNIT_DAYS_DEFAULT),
    ("time_series", "D", "Data & AI", "Time Series: statsmodels (ARIMA, SARIMA), Prophet, Sktime",
     ["#timeseries", "#arima"], ["pandas"], UNIT_DAYS_DEFAULT),
    ("anomaly", "D", "Data & AI", "Anomaly Detection: Isolation Forest, LOF, Autoencoder, One-class SVM",
     ["#anomaly_detection"], ["sklearn"], UNIT_DAYS_DEFAULT),
    ("neural_basics", "D", "Data & AI", "Neural Network Fundamentals: Perceptron, Activation, Backprop, Gradient Descent",
     ["#neural_network", "#deep_learning"], ["ml_fundamentals", "numpy"], UNIT_DAYS_DEFAULT),
    ("tensorflow", "D", "Data & AI", "TensorFlow 2 + Keras: Sequential, Functional API, Callbacks",
     ["#tensorflow", "#keras"], ["neural_basics"], UNIT_DAYS_DEFAULT),
    ("pytorch", "D", "Data & AI", "PyTorch: Tensor, Autograd, nn.Module, DataLoader, Training loop",
     ["#pytorch"], ["neural_basics"], UNIT_DAYS_DEFAULT),
    ("pytorch_lightning", "D", "Data & AI", "PyTorch Lightning & Fabric: Boilerplate-free training, TPU/GPU",
     ["#pytorch_lightning"], ["pytorch"], UNIT_DAYS_DEFAULT),
    ("cnn", "D", "Data & AI", "CNN: Convolution, Pooling, ResNet, VGG, EfficientNet — Image classification",
     ["#cnn", "#computer_vision"], ["pytorch", "tensorflow"], UNIT_DAYS_DEFAULT),
    ("rnn_lstm", "D", "Data & AI", "RNN, LSTM, GRU — Sequence modeling, NLP truyền thống",
     ["#rnn", "#lstm"], ["pytorch"], UNIT_DAYS_DEFAULT),
    ("transformer", "D", "Data & AI", "Transformer Architecture: Self-attention, Multi-head, Positional Encoding",
     ["#transformer", "#attention"], ["rnn_lstm"], UNIT_DAYS_DEEP),
    ("transfer_learning", "D", "Data & AI", "Transfer Learning: Fine-tuning pretrained, Feature extraction",
     ["#transfer_learning"], ["cnn", "transformer"], UNIT_DAYS_DEFAULT),
    ("onnx", "D", "Data & AI", "ONNX: Export model, Runtime, Optimize cho production inference",
     ["#onnx", "#inference"], ["pytorch", "tensorflow"], UNIT_DAYS_DEFAULT),
    ("nlp_basic", "D", "Data & AI", "NLP cơ bản: Tokenization, Stopwords, Lemmatization, TF-IDF, Word2Vec",
     ["#nlp"], ["pandas"], UNIT_DAYS_DEFAULT),
    ("huggingface", "D", "Data & AI", "HuggingFace: BERT, GPT, T5, pipeline(), Trainer, Dataset",
     ["#huggingface", "#bert"], ["transformer"], UNIT_DAYS_DEFAULT),
    ("llm_finetuning", "D", "Data & AI", "LLM Fine-tuning: LoRA, QLoRA, PEFT, Instruction tuning, SFT",
     ["#llm", "#lora", "#finetuning"], ["huggingface", "pytorch"], UNIT_DAYS_DEEP),
    ("langchain", "D", "Data & AI", "LangChain: Chain, Agent, Tool, Memory, RAG (Retrieval-Augmented Generation)",
     ["#langchain", "#rag"], ["huggingface"], UNIT_DAYS_DEFAULT),
    ("llamaindex", "D", "Data & AI", "LlamaIndex: Index, Query Engine, Node Parser, Vector Store",
     ["#llamaindex", "#rag"], ["langchain"], UNIT_DAYS_DEFAULT),
    ("openai_api", "D", "Data & AI", "OpenAI/Claude/Gemini/Groq API: Chat, Embeddings, Function Calling, Vision",
     ["#openai", "#gemini"], ["langchain"], UNIT_DAYS_DEFAULT),
    ("vector_db", "D", "Data & AI", "Vector Database: Chroma, Pinecone, Weaviate, Qdrant, pgvector",
     ["#vector_db", "#embeddings"], ["langchain"], UNIT_DAYS_DEFAULT),
    ("local_llm", "D", "Data & AI", "Ollama, LM Studio, vLLM: Chạy LLM local (Llama3, Mistral, Phi)",
     ["#ollama", "#local_llm"], ["vector_db"], UNIT_DAYS_DEFAULT),
    ("ai_agent", "D", "Data & AI", "AI Agent: ReAct, Plan-and-Execute, Multi-agent (AutoGen, CrewAI, LangGraph)",
     ["#ai_agent", "#langgraph"], ["langchain", "openai_api"], UNIT_DAYS_DEEP),
    ("opencv", "D", "Data & AI", "OpenCV: Image processing, Filters, Morphology, Contours, Geometric transforms",
     ["#opencv", "#computer_vision"], ["numpy"], UNIT_DAYS_DEFAULT),
    ("object_detection", "D", "Data & AI", "Object Detection: YOLO (v8/v11), Detectron2, DETR",
     ["#yolo", "#object_detection"], ["cnn", "opencv"], UNIT_DAYS_DEFAULT),
    ("segmentation", "D", "Data & AI", "Image Segmentation: Mask R-CNN, SAM (Segment Anything), Semantic",
     ["#segmentation", "#sam"], ["object_detection"], UNIT_DAYS_DEFAULT),
    ("generative_ai", "D", "Data & AI", "Generative AI: Stable Diffusion, ControlNet, Image-to-Image, Inpainting",
     ["#stable_diffusion", "#diffusers"], ["cnn"], UNIT_DAYS_DEFAULT),
    ("ocr", "D", "Data & AI", "OCR: Tesseract, EasyOCR, PaddleOCR, Doctr, Table extraction",
     ["#ocr", "#tesseract"], ["opencv"], UNIT_DAYS_DEFAULT),
    ("mlflow", "D", "Data & AI", "MLflow: Experiment tracking, Model Registry, Artifact logging, UI",
     ["#mlflow", "#mlops"], ["sklearn", "pytorch"], UNIT_DAYS_DEFAULT),
    ("dvc", "D", "Data & AI", "DVC: Data Versioning, Pipeline, Remote storage, Experiment tracking",
     ["#dvc", "#data_versioning"], ["mlflow"], UNIT_DAYS_DEFAULT),
    ("model_serving", "D", "Data & AI", "Model Serving: FastAPI + model, TorchServe, BentoML, Ray Serve",
     ["#model_serving"], ["mlflow", "fastapi_basic"], UNIT_DAYS_DEFAULT),
    ("ml_monitoring", "D", "Data & AI", "Monitoring ML: Evidently, Grafana, Prometheus, Data/Concept drift",
     ["#ml_monitoring"], ["model_serving"], UNIT_DAYS_DEFAULT),
    ("kubeflow", "D", "Data & AI", "Kubeflow, Vertex AI Pipelines: ML workflow orchestration trên cloud",
     ["#kubeflow", "#mlops"], ["mlflow"], UNIT_DAYS_DEFAULT),

    # ============ PHASE 5: DEVOPS, CLOUD & INFRASTRUCTURE ============
    ("docker", "O", "DevOps & Cloud", "Docker: Dockerfile, Image, Container, Volumes, Networks, Multi-stage build",
     ["#docker"], [], UNIT_DAYS_DEFAULT),
    ("docker_compose", "O", "DevOps & Cloud", "Docker Compose: Services, Dependencies, Env, Healthcheck, Profiles",
     ["#docker_compose"], ["docker"], UNIT_DAYS_DEFAULT),
    ("kubernetes", "O", "DevOps & Cloud", "Kubernetes: Pod, Deployment, Service, Ingress, ConfigMap, Secret",
     ["#kubernetes", "#k8s"], ["docker_compose"], UNIT_DAYS_DEFAULT),
    ("k8s_adv", "O", "DevOps & Cloud", "Kubernetes nâng cao: HPA, StatefulSet, Helm, ArgoCD, Kustomize",
     ["#kubernetes", "#helm", "#argocd"], ["kubernetes"], UNIT_DAYS_DEFAULT),
    ("cicd", "O", "DevOps & Cloud", "CI/CD: GitHub Actions, GitLab CI, Jenkins — Build, Test, Deploy",
     ["#ci_cd", "#github_actions"], ["docker"], UNIT_DAYS_DEFAULT),
    ("terraform", "O", "DevOps & Cloud", "Terraform: IaC — Provision AWS/GCP/Azure resources",
     ["#terraform", "#iac"], ["cicd"], UNIT_DAYS_DEFAULT),
    ("ansible", "O", "DevOps & Cloud", "Ansible: Playbook, Role, Inventory, Modules — Configuration management",
     ["#ansible"], ["terraform"], UNIT_DAYS_DEFAULT),
    ("aws", "O", "DevOps & Cloud", "AWS Core: EC2, S3, RDS, VPC, IAM, Lambda, API Gateway, SQS, SNS",
     ["#aws"], ["docker"], UNIT_DAYS_DEFAULT),
    ("boto3", "O", "DevOps & Cloud", "AWS SDK: boto3 — S3, DynamoDB, Lambda, SES, Rekognition, Textract",
     ["#boto3", "#aws"], ["aws"], UNIT_DAYS_DEFAULT),
    ("gcp", "O", "DevOps & Cloud", "GCP: Cloud Run, BigQuery, Vertex AI, Cloud Functions, Pub/Sub",
     ["#gcp"], ["aws"], UNIT_DAYS_DEFAULT),
    ("azure", "O", "DevOps & Cloud", "Azure: Azure Functions, AKS, Azure ML, Cosmos DB, Service Bus",
     ["#azure"], ["aws"], UNIT_DAYS_DEFAULT),
    ("serverless", "O", "DevOps & Cloud", "Serverless: AWS Lambda + Python, Cold start, Layers, Mangum",
     ["#serverless", "#lambda"], ["aws", "fastapi_advanced"], UNIT_DAYS_DEFAULT),
    ("kafka", "O", "DevOps & Cloud", "Kafka với Python: Producer, Consumer, Avro, Schema Registry, Faust",
     ["#kafka"], [], UNIT_DAYS_DEFAULT),
    ("rabbitmq", "O", "DevOps & Cloud", "RabbitMQ với pika/aio-pika: Exchange, Queue, Routing key, Dead letter",
     ["#rabbitmq"], ["kafka"], UNIT_DAYS_DEFAULT),
    ("event_driven", "O", "DevOps & Cloud", "Event-driven Architecture: CQRS, Event Sourcing, Saga, Outbox",
     ["#event_driven", "#cqrs"], ["kafka", "rabbitmq"], UNIT_DAYS_DEFAULT),
    ("logging", "O", "DevOps & Cloud", "Logging: logging module, structlog, JSON logging, ELK, Loki",
     ["#logging", "#observability"], [], UNIT_DAYS_DEFAULT),
    ("tracing", "O", "DevOps & Cloud", "Tracing: OpenTelemetry Python, Jaeger, Zipkin, Datadog, Sentry",
     ["#opentelemetry", "#tracing"], ["logging"], UNIT_DAYS_DEFAULT),
    ("metrics", "O", "DevOps & Cloud", "Metrics: Prometheus client_python, Grafana dashboard, Alertmanager",
     ["#prometheus", "#grafana"], ["logging"], UNIT_DAYS_DEFAULT),
    ("security", "O", "DevOps & Cloud", "Python Security: OWASP Top 10, SQL Injection, XSS, CSRF, SSRF",
     ["#security", "#owasp"], ["http"], UNIT_DAYS_DEFAULT),
    ("cryptography", "O", "DevOps & Cloud", "Cryptography: hashlib, secrets, cryptography, JWT, OAuth2",
     ["#cryptography", "#jwt"], ["security"], UNIT_DAYS_DEFAULT),
    ("pentest", "O", "DevOps & Cloud", "Penetration Testing: scapy, paramiko, ldap3, impacket",
     ["#pentest", "#security"], ["cryptography"], UNIT_DAYS_DEFAULT),

    # ============ PHASE 6: SPECIALIZED & EMERGING ============
    ("pyspark", "S", "Specialized", "Apache Spark với PySpark: RDD, DataFrame, SQL, MLlib, Streaming",
     ["#pyspark", "#spark"], ["pandas"], UNIT_DAYS_DEFAULT),
    ("airflow", "S", "Specialized", "Apache Airflow: DAG, Operator, Sensor, XCom, Connections, Plugins",
     ["#airflow", "#data_pipeline"], ["pandas"], UNIT_DAYS_DEFAULT),
    ("prefect_dagster", "S", "Specialized", "Prefect & Dagster: Modern data orchestration — Flow, Task, Asset",
     ["#prefect", "#dagster"], ["airflow"], UNIT_DAYS_DEFAULT),
    ("data_lake", "S", "Specialized", "Data Lake: Delta Lake, Apache Iceberg, Hudi, dbt",
     ["#datalake", "#dbt"], ["pyspark"], UNIT_DAYS_DEFAULT),
    ("streaming", "S", "Specialized", "Streaming: Kafka Streams, Spark Structured Streaming, PyFlink",
     ["#streaming", "#flink"], ["kafka", "pyspark"], UNIT_DAYS_DEFAULT),
    ("tkinter", "S", "Specialized", "Tkinter: Widget, Layout, Event handling, Custom widget, ttk",
     ["#tkinter", "#gui"], [], UNIT_DAYS_DEFAULT),
    ("pyqt", "S", "Specialized", "PyQt6/PySide6: QWidget, Signal/Slot, Model/View, Thread worker, QML",
     ["#pyqt", "#gui"], ["tkinter"], UNIT_DAYS_DEFAULT),
    ("kivy", "S", "Specialized", "Kivy: Cross-platform (Mobile + Desktop), KV Language, Gestures",
     ["#kivy", "#mobile"], ["tkinter"], UNIT_DAYS_DEFAULT),
    ("packaging_exe", "S", "Specialized", "PyInstaller, cx_Freeze, Nuitka: Đóng gói Python thành EXE/app",
     ["#packaging", "#exe"], [], UNIT_DAYS_DEFAULT),
    ("system_automation", "S", "Specialized", "System Automation: psutil, subprocess, watchdog, schedule, crontab",
     ["#automation", "#system"], [], UNIT_DAYS_DEFAULT),
    ("office_automation", "S", "Specialized", "Office Automation: openpyxl, xlrd, python-docx, pptx, PDF",
     ["#office_automation"], [], UNIT_DAYS_DEFAULT),
    ("email_notification", "S", "Specialized", "Email & Notification: smtplib, email, imaplib, slack_sdk, telegram",
     ["#email", "#notification"], [], UNIT_DAYS_DEFAULT),
    ("win32_automation", "S", "Specialized", "Win32 Automation: pywin32, pyautogui, keyboard, mouse",
     ["#win32", "#automation"], ["system_automation"], UNIT_DAYS_DEFAULT),
    ("socket", "S", "Specialized", "Socket Programming: TCP/UDP Server/Client, Non-blocking, asyncio streams",
     ["#socket", "#networking"], [], UNIT_DAYS_DEFAULT),
    ("network_tools", "S", "Specialized", "Network Tools: Scapy, python-nmap, netmiko (SSH)",
     ["#scapy", "#netmiko"], ["socket"], UNIT_DAYS_DEFAULT),
    ("faststream", "S", "Specialized", "FastStream: Kafka/RabbitMQ/SQS handler theo phong cách FastAPI",
     ["#faststream", "#messaging"], ["asyncio_adv", "kafka"], UNIT_DAYS_DEFAULT),
    ("pygame", "S", "Specialized", "Pygame: Surface, Sprite, Event, Collision, Sound, Game loop",
     ["#pygame", "#gamedev"], [], UNIT_DAYS_DEFAULT),
    ("arcade", "S", "Specialized", "Arcade: Modern game engine, Sprite, TileMap, Physics, Shader",
     ["#arcade", "#gamedev"], ["pygame"], UNIT_DAYS_DEFAULT),
    ("godot_renpy", "S", "Specialized", "Python + Godot (GDScript fallback), Ren'Py (Visual Novel)",
     ["#godot", "#renpy"], ["pygame"], UNIT_DAYS_DEFAULT),
    ("micropython", "S", "Specialized", "MicroPython: ESP32/ESP8266, GPIO, PWM, I2C, SPI, MQTT, BLE",
     ["#micropython", "#iot"], [], UNIT_DAYS_DEFAULT),
    ("circuitpython", "S", "Specialized", "CircuitPython: Adafruit boards, Sensors, NeoPixel, USB HID",
     ["#circuitpython"], ["micropython"], UNIT_DAYS_DEFAULT),
    ("raspberrypi", "S", "Specialized", "Raspberry Pi với Python: GPIO, Camera, UART — Home Automation",
     ["#raspberrypi"], ["micropython"], UNIT_DAYS_DEFAULT),
    ("web3", "S", "Specialized", "Web3.py: Ethereum, Smart Contract interaction, ABI, Transaction signing",
     ["#web3", "#ethereum"], [], UNIT_DAYS_DEFAULT),
    ("solana", "S", "Specialized", "Solana với Python: solders, solana-py, SPL Token, NFT minting",
     ["#solana", "#web3"], ["web3"], UNIT_DAYS_DEFAULT),
    ("scipy", "S", "Specialized", "SciPy: Optimization, Integration, Signal processing, Linear algebra",
     ["#scipy"], ["numpy"], UNIT_DAYS_DEFAULT),
    ("sympy", "S", "Specialized", "SymPy: Symbolic math, Calculus, Equation solving, Code generation",
     ["#sympy", "#math"], ["numpy"], UNIT_DAYS_DEFAULT),
    ("quantum", "S", "Specialized", "Quantum Computing: Qiskit (IBM), PennyLane — Quantum circuits",
     ["#quantum", "#qiskit"], ["numpy"], UNIT_DAYS_DEFAULT),
    ("clean_architecture", "S", "Specialized", "Clean Architecture: Domain, Application, Infrastructure layers",
     ["#clean_architecture"], ["solid", "repository_di"], UNIT_DAYS_DEFAULT),
    ("hexagonal", "S", "Specialized", "Hexagonal Architecture (Ports & Adapters) trong Python",
     ["#hexagonal", "#architecture"], ["clean_architecture"], UNIT_DAYS_DEFAULT),
    ("microservices", "S", "Specialized", "Microservices với Python: Service mesh, API gateway, Discovery",
     ["#microservices"], ["event_driven", "docker"], UNIT_DAYS_DEFAULT),
    ("ddd", "S", "Specialized", "Event Sourcing & DDD (Domain-Driven Design) trong Python",
     ["#ddd", "#event_sourcing"], ["clean_architecture"], UNIT_DAYS_DEFAULT),
    ("pypi_publish", "S", "Specialized", "Python Package Publishing: pyproject.toml, hatch, poetry, PyPI, versioning",
     ["#packaging", "#pypi"], ["modules_packages"], UNIT_DAYS_DEFAULT),
    ("opensource", "S", "Specialized", "Open Source Contribution: Git flow, PR etiquette, Code review",
     ["#opensource", "#contribution"], ["pypi_publish"], UNIT_DAYS_DEFAULT),
]

SECTIONS = {
    "F": "Phase 1 - Foundation",
    "A": "Phase 2 - Advanced",
    "W": "Phase 3 - Web Dev",
    "D": "Phase 4 - Data & AI",
    "O": "Phase 5 - DevOps & Cloud",
    "S": "Phase 6 - Specialized",
}

# 45 focus areas — đủ cho chu kỳ 30 và 45 ngày
FOCUS_AREAS = [
    "Core Concept: Bản chất cốt lõi, tại sao công nghệ này tồn tại, và ví dụ 'Hello World' cơ bản nhất.",
    "Basic Syntax & Usage: Cú pháp nền tảng phổ biến nhất và cách dùng thông thường.",
    "Advanced Syntax & Tricks: Tham số ẩn, cú pháp rút gọn (syntax sugar) và các thủ thuật nâng cao.",
    "Under the hood: Kiến trúc tầng thấp (Memory, Compiler/Interpreter, cách máy tính hiểu code này).",
    "Execution Lifecycle: Thứ tự chạy, Event Loop, Call Stack và luồng thực thi (execution flow) thực tế.",
    "Hidden Gems: Các phương thức/tính năng cực kỳ hữu ích nhưng ít tài liệu nhắc tới.",
    "Basic Error Handling: Bắt lỗi thông thường, try/catch, và các mã lỗi thường gặp.",
    "Gotchas & Edge Cases: Các trường hợp dị biệt, góc khuất dễ gây bug nghiêm trọng khó tìm.",
    "Speed Performance: Tối ưu CPU, giảm thiểu vòng lặp thừa, cách viết code chạy nhanh nhất.",
    "Memory Optimization: Quản lý bộ nhớ, ngăn chặn Memory Leak, và Garbage Collection profiling.",
    "Scalability: Cấu trúc code thế nào để dễ dàng mở rộng (scale) khi dự án phình to hàng triệu dòng code.",
    "Security: Các lỗ hổng bảo mật tiềm ẩn (Injection, Deserialization, DoS...) và cách phòng chống.",
    "Structural Design Patterns: Áp dụng các Design Pattern về mặt cấu trúc (Structural) cho chủ đề này.",
    "Behavioral Design Patterns: Áp dụng các Design Pattern về mặt hành vi (Behavioral) để quản lý luồng.",
    "Anti-patterns: Những cách viết TỒI TỆ NHẤT, những 'red flags' tuyệt đối phải tránh khi dùng công nghệ này.",
    "Unit Testing: Cách mock/stub và viết bài test cục bộ (Unit Test) cho tính năng này.",
    "Integration Testing: Viết test tích hợp luồng dữ liệu hoặc E2E test.",
    "Deep Debugging: Kỹ thuật gỡ lỗi chuyên sâu dùng DevTools, breakpoints, và Profiler.",
    "Compatibility & Versioning: Xử lý tương thích đa phiên bản, deprecation, migration path.",
    "Ecosystem Integration: Best practices khi kết hợp với thư viện/framework/công cụ thứ 3.",
    "Config & Tooling: Tương tác và cấu hình với các công cụ build/package/quản lý môi trường.",
    "CI/CD Automation: Cách tự động hóa kiểm tra tính năng này trên pipeline (GitHub Actions, Jenkins).",
    "Open Source Analysis: Mổ xẻ đọc code thực tế của dự án lớn xem họ triển khai chủ đề này ra sao.",
    "Interview Prep (Junior/Mid): Trả lời lý thuyết cốt lõi và giải quyết bài tập nhỏ thường gặp khi phỏng vấn.",
    "Interview Prep (Senior): System Design, trade-offs, và trả lời các câu hỏi kiến trúc hóc búa.",
    "Reinvent the wheel (Phase 1): Tự code lại công nghệ này từ con số 0 - Phân tích và Khởi tạo cấu trúc.",
    "Reinvent the wheel (Phase 2): Tự code lại - Triển khai Core Logic cốt lõi.",
    "Reinvent the wheel (Phase 3): Tự code lại - Hoàn thiện, test và so sánh với bản gốc.",
    "Mini-Project (Phase 1): Áp dụng vào dự án thực tế - Lên ý tưởng & Thiết kế kiến trúc.",
    "Mini-Project (Phase 2): Áp dụng vào dự án - Code nghiệp vụ chính và luồng dữ liệu.",
    "Mini-Project (Phase 3): Áp dụng vào dự án - Hoàn thiện, Review, Refactor và Đóng gói.",
    "Performance Profiling: Benchmark, profiling chi tiết, so sánh hiệu năng ở mức thấp nhất.",
    "Security Hardening: Bảo mật sâu hơn, attack surface, threat modeling cho tính năng này.",
    "Concurrency & Parallelism: Biến tính năng này chạy song song, lock, race condition, async.",
    "Data Modeling: Thiết kế schema/dữ liệu đúng chuẩn, normalized, index, truy vấn tối ưu.",
    "API Design: Thiết kế API rõ ràng, versioning, error contract, document chuẩn.",
    "Observability: Log, metric, trace để vận hành tính năng này trong production.",
    "Disaster Recovery & Fault Tolerance: Retry, timeout, circuit breaker, graceful degradation.",
    "Monitoring & Alerting: Theo dõi health, alert khi hỏng, dashboard vận hành.",
    "Internationalization: i18n, Unicode, encoding, xử lý đa ngôn ngữ cho tính năng này.",
    "Performance Optimization Deep: Cache, memoize, lazy, batching, connection pooling.",
    "Case Study: Đọc/phân tích 1 dự án thực tế nổi tiếng dùng tính năng này trong production.",
    "Best Practices Final: Tổng hợp toàn bộ best practices, conventions, coding standard.",
    "Code Review: Review code của người khác và tự review, tìm bug, đề xuất cải tiến.",
    "Capstone Mini-Project: Tích hợp kiến thức toàn phần vào sản phẩm hoàn chỉnh.",
]

# Các focus là ngày thực hành/test -> bắt buộc Non-Interactive warning
PRACTICE_INDEX = {14, 15, 16, 17, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 38, 40, 41, 42, 43, 44}

REVIEW_EVERY = 5  # cứ 5 topic -> 1 Cumulative Review Day
CAPSTONE_DAYS = UNIT_DAYS_DEFAULT  # 30 ngày capstone cuối

NON_INTERACTIVE = (
    "(⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. "
    "HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)"
)

VIETNAMESE_REQ = "YÊU CẦU BẮT BUỘC: LUÔN TRẢ LỜI BẰNG TIẾNG VIỆT."


def topological_sort(topics):
    """Sắp xếp topo theo prerequisites, giữ thứ tự phase (section) và thứ tự khai báo."""
    by_id = {t[0]: t for t in topics}
    order = []
    tmp_mark = set()
    perm_mark = set()

    def visit(tid, chain):
        if tid in perm_mark:
            return
        if tid in tmp_mark:
            raise RuntimeError("Prerequisite cycle: " + " -> ".join(chain + [tid]))
        tmp_mark.add(tid)
        for pre in by_id[tid][5]:
            visit(pre, chain + [tid])
        tmp_mark.discard(tid)
        perm_mark.add(tid)
        order.append(tid)

    for t in topics:
        visit(t[0], [])
    return [by_id[tid] for tid in order]


def build_roadmap():
    sorted_topics = topological_sort(TOPICS)
    day_counter = [0]
    roadmap = []  # (day, kind, section, title, tags, part, total_parts, focus, review_ids)

    def add_days(kind, section, title, tags, total, focus_base=None, review_ids=None):
        for i in range(1, total + 1):
            focus = focus_base[(i - 1) % len(focus_base)] if focus_base else None
            roadmap.append((day_counter[0] + 1, kind, section, title, tags, i, total, focus, review_ids))
            day_counter[0] += 1

    topic_count = 0
    for t in sorted_topics:
        tid, sec, short, title, tags, prereqs, days = t
        topic_count += 1
        add_days("topic", sec, title, tags, days, focus_base=FOCUS_AREAS)
        if topic_count % REVIEW_EVERY == 0:
            recent = [x[3] for x in sorted_topics[max(0, topic_count - REVIEW_EVERY):topic_count]]
            add_days("review", sec, f"Ôn tập tích lũy {REVIEW_EVERY} topic gần nhất",
                     ["#review", "#ontap"], 5, focus_base=[
                         "Tổng hợp kiến thức 5 topic gần nhất thành sơ đồ tư duy thống nhất.",
                         "Giải 10 bài tập tổng hợp đan xen kiến thức của 5 topic.",
                         "Tự viết 1 project mini kết hợp ít nhất 3 trong 5 topic.",
                         "Self-test 20 câu hỏi lý thuyết + giải thích (không tương tác, in đáp án).",
                         "Xác định lỗ hổng kiến thức và ôn lại điểm yếu nhất.",
                     ], review_ids=recent)

    add_days("capstone", "S", "Capstone Tổng Hợp Toàn Roadmap — sản phẩm tích hợp đa Phase",
             ["#capstone", "#portfolio"], CAPSTONE_DAYS,
             focus_base=FOCUS_AREAS[25:45] + FOCUS_AREAS[:10])
    return roadmap


def generate_markdown(roadmap):
    md_lines = [
        "# Python RoadMap Full — Từ 0 Đến Master Toàn Diện Hệ Sinh Thái Python",
        "",
        "> Mục tiêu: Nắm vững Python TỪ CON SỐ 0 đến trình độ PRO cực kỳ sâu, bao phủ TOÀN BỘ "
        "các công nghệ và lĩnh vực Python có thể làm được.",
        "> Thời lượng: Mỗi Day = 1 buổi học 60 phút (1 tiếng/ngày).",
        f"> Tổng: {len(roadmap)} Day. Trình tự: Foundation -> Advanced -> Web Dev -> Data/ML/AI -> DevOps/Cloud -> Specialized.",
        "> Chu kỳ Ultimate: mỗi topic học sâu 30 ngày (topic lớn 45 ngày), Review Day mỗi 5 topic, Capstone 30 ngày cuối.",
        "",
        "> Ký hiệu: Foundation | Advanced | Web Dev | Data+AI | DevOps+Cloud | Specialized",
        "",
    ]

    for (day, kind, section, title, tags, part, total_parts, focus, review_ids) in roadmap:
        short_section = SECTIONS.get(section, section).split(" - ")[1]
        progress = f"(Phan {part}/{total_parts})"
        md_lines.append(f"## Day {day} — [{short_section}] {title} {progress}")
        md_lines.append("**Prompt:**")

        if kind == "review":
            md_lines.append(f"Day này là CUMULATIVE REVIEW sau {len(review_ids or [])} topic: {', '.join(review_ids or [])}.")
            md_lines.append(VIETNAMESE_REQ)
            md_lines.append(f"Trọng tâm hôm nay: {focus}")
            md_lines.append("Yêu cầu: Hệ thống lại toàn bộ kiến thức, nối liền các chủ đề với nhau thay vì học rời rạc.")
            md_lines.append(NON_INTERACTIVE)
            md_lines.append("")
        else:
            md_lines.append(f"Day {day} trong lộ trình Python RoadMap Full.")
            md_lines.append(f"Chuyên đề: [{SECTIONS.get(section, section)}] — {title} {progress}.")
            md_lines.append(VIETNAMESE_REQ)
            md_lines.append("")
            md_lines.append(f"**Yêu cầu ĐẶC BIỆT cho {progress}:**")
            md_lines.append(f"Hôm nay, BẮT BUỘC tập trung 100% vào khía cạnh: **[ {focus} ]**")
            md_lines.append("Hãy viết giáo trình, code mẫu và giải thích ĐÚNG trọng tâm vào khía cạnh này.")
            md_lines.append("")
            if (part - 1) % len(FOCUS_AREAS) in PRACTICE_INDEX:
                md_lines.append(NON_INTERACTIVE)
                md_lines.append("")

            md_lines.append("Yêu cầu buổi học 60 phút (1 tiếng):")
            md_lines.append("- 15 phút: Đọc lý thuyết & hiểu bản chất của khía cạnh được yêu cầu hôm nay.")
            md_lines.append("- 30 phút: Viết code mẫu chuyên sâu + chạy thử + thử biến thể.")
            md_lines.append("- 15 phút: Làm bài tập, tự kiểm tra lại kiến thức.")
            md_lines.append("")

        md_lines.append("**Bài tập:**")
        if kind == "review":
            md_lines.append("- Bài 1 (Tổng hợp): Vẽ bản đồ kiến thức nối 5 topic gần nhất.")
            md_lines.append("- Bài 2 (Đan xen): Giải bài tập yêu cầu kết hợp ≥3 topic trong 5 topic đó.")
            md_lines.append("- Bài 3 (Tự đánh giá): 20 câu hỏi trắc nghiệm + đáp án chi tiết, tự chấm điểm.")
        else:
            focus_name = focus.split(":")[0].strip()
            md_lines.append(f"- Bài 1 (Cơ bản): Hoàn thành ví dụ cơ bản về [{focus_name}].")
            md_lines.append(f"- Bài 2 (Trung cấp): Mở rộng code, xử lý edge cases của [{focus_name}].")
            md_lines.append(f"- Bài 3 (Nâng cao): Áp dụng [{focus_name}] vào mini-tool/dự án thực tế.")
        md_lines.append("")
        tags_str = " ".join(tags) if isinstance(tags, list) else str(tags)
        all_tags = f"#python #day{day} {tags_str} #{short_section.lower().replace(' ', '_')}"
        deduped = []
        for t in all_tags.split():
            if t not in deduped:
                deduped.append(t)
        md_lines.append(f"**Tags:** {' '.join(deduped)}")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    with open(OUTPUT_FILEPATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    return len(roadmap)


if __name__ == "__main__":
    data = build_roadmap()
    generated = generate_markdown(data)
    print("Done! Generated: " + OUTPUT_FILEPATH)
    print("Total days: " + str(generated))
    counts = {}
    for (day, kind, section, title, tags, part, tp, focus, rid) in data:
        s = SECTIONS.get(section, section)
        counts.setdefault(s, [0, 0])
        counts[s][0] += 1
        if part == 1 and kind == "topic":
            counts[s][1] += 1
    for s, (days, topics) in counts.items():
        print(f"  {s}: {days} Day / {topics} topic")
    ids = [t[0] for t in TOPICS]
    print("  Topics:", len(ids), "| unique ids:", len(set(ids)))
    print("  Review Days:", sum(1 for r in data if r[1] == "review"))
    print("  Capstone Days:", sum(1 for r in data if r[1] == "capstone"))
    print("  Day sequence continuous:", [x[0] for x in data] == list(range(1, len(data) + 1)))