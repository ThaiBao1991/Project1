# Generate Python Roadmap - 3000 Days (~8 Years, Full Python Ecosystem 2025)
# Bao phu: Foundation -> Advanced -> Web -> Data/ML/AI -> DevOps -> Specialized
# Moi Day: 1 buoi 30-60 phut hoc tap, code vi du + 3 bai tap

filepath = r"c:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\Download\AskCpl\roadmap_python_3000.md"

def build_roadmap():
    roadmap = []
    day = 1

    def add_topic(section, topic, tags, days):
        nonlocal day
        for i in range(1, days + 1):
            roadmap.append((day, section, topic, tags, i, days))
            day += 1

    # =====================================================================
    # PHASE 1: PYTHON FOUNDATION (Day 1 - ~450)
    # =====================================================================

    # -- 1.1 Setup & Mindset
    add_topic("Phase 1 - Foundation", "Cai dat Python, VS Code, Git co ban & Mindset lap trinh vien", "#setup #python #git", 15)
    add_topic("Phase 1 - Foundation", "Python Interpreter, REPL, Jupyter Notebook, IPython", "#setup #repl", 15)

    # -- 1.2 Syntax Co Ban
    add_topic("Phase 1 - Foundation", "Bien va Kieu du lieu: int, float, str, bool, None", "#syntax #datatypes", 15)
    add_topic("Phase 1 - Foundation", "Phep tinh so hoc, Toan tu so sanh, Toan tu logic", "#syntax #operators", 15)
    add_topic("Phase 1 - Foundation", "Strings: Index, Slice, f-string, format, join, split, replace", "#strings", 30)
    add_topic("Phase 1 - Foundation", "Input/Output: print, input, sep/end, repr vs str", "#io #print", 15)
    add_topic("Phase 1 - Foundation", "Cau lenh dieu kien: if, elif, else, Ternary Operator", "#control #if", 15)
    add_topic("Phase 1 - Foundation", "Vong lap for: range, enumerate, zip, List Comprehension", "#loops #for", 30)
    add_topic("Phase 1 - Foundation", "Vong lap while: break, continue, else trong vong lap", "#loops #while", 15)
    add_topic("Phase 1 - Foundation", "Ham (Functions): def, return, Default/Keyword/Positional args", "#functions", 30)
    add_topic("Phase 1 - Foundation", "Ham nang cao: *args, **kwargs, Lambda, map, filter, reduce", "#functions #lambda", 30)
    add_topic("Phase 1 - Foundation", "Pham vi bien: Local, Enclosing, Global, Built-in (LEGB rule)", "#scope #legb", 15)

    # -- 1.3 Cau truc du lieu built-in
    add_topic("Phase 1 - Foundation", "List: Methods, Slicing, Nested List, Copy vs Reference", "#list", 30)
    add_topic("Phase 1 - Foundation", "Tuple: Immutability, Packing/Unpacking, Named Tuple", "#tuple", 15)
    add_topic("Phase 1 - Foundation", "Dictionary: CRUD, dict comprehension, defaultdict, Counter, OrderedDict", "#dict", 30)
    add_topic("Phase 1 - Foundation", "Set: union, intersection, difference, frozenset", "#set", 15)
    add_topic("Phase 1 - Foundation", "Cac cau truc du lieu nang cao: deque, heap, stack voi list", "#collections #heapq", 30)

    # -- 1.4 OOP
    add_topic("Phase 1 - Foundation", "OOP: Class, Object, __init__, Attributes, Methods, self", "#oop #class", 30)
    add_topic("Phase 1 - Foundation", "OOP: Ke thua (Inheritance), super(), Da ke thua (MRO)", "#oop #inheritance", 30)
    add_topic("Phase 1 - Foundation", "OOP: Encapsulation, Tinh dong (Polymorphism), Duck Typing", "#oop #polymorphism", 30)
    add_topic("Phase 1 - Foundation", "OOP: Dunder methods: __str__, __repr__, __len__, __eq__, __lt__...", "#oop #dunder", 30)
    add_topic("Phase 1 - Foundation", "OOP: @property, @classmethod, @staticmethod, Slots", "#oop #property", 15)
    add_topic("Phase 1 - Foundation", "Abstract Base Class (ABC), Protocol (Structural Subtyping)", "#oop #abc #protocol", 15)
    add_topic("Phase 1 - Foundation", "Dataclass: @dataclass, field(), frozen=True, post_init", "#dataclass", 15)

    # -- 1.5 Xu ly loi & File I/O
    add_topic("Phase 1 - Foundation", "Exception Handling: try, except, else, finally, raise, custom Exception", "#exception", 30)
    add_topic("Phase 1 - Foundation", "File I/O: open, read, write, with statement, pathlib.Path", "#file #io #pathlib", 30)
    add_topic("Phase 1 - Foundation", "JSON, CSV, YAML: doc, ghi, parse voi json, csv, pyyaml", "#json #csv #yaml", 30)

    # -- 1.6 Module & Package
    add_topic("Phase 1 - Foundation", "Module: import, from, as, __name__, __all__, Relative import", "#modules", 15)
    add_topic("Phase 1 - Foundation", "Package: __init__.py, pip, venv, virtualenv, pyproject.toml", "#packages #pip #venv", 15)
    add_topic("Phase 1 - Foundation", "Thu vien chuan: os, sys, shutil, glob, re (Regex), datetime, math", "#stdlib", 30)
    add_topic("Phase 1 - Foundation", "Thu vien chuan nang cao: itertools, functools, contextlib, abc", "#stdlib #itertools", 30)

    # =====================================================================
    # PHASE 2: PYTHON ADVANCED & PATTERNS (Day ~550 - ~1100)
    # =====================================================================

    add_topic("Phase 2 - Advanced", "Decorator: Function Decorator, Class Decorator, Stacking, wraps", "#decorator", 30)
    add_topic("Phase 2 - Advanced", "Generator: yield, Generator Expression, send(), Lazy Evaluation", "#generator #yield", 30)
    add_topic("Phase 2 - Advanced", "Iterator Protocol: __iter__, __next__, StopIteration", "#iterator", 15)
    add_topic("Phase 2 - Advanced", "Context Manager: with, __enter__, __exit__, contextmanager", "#context_manager", 15)
    add_topic("Phase 2 - Advanced", "Metaclass: type, __new__, __init_subclass__, ABC internals", "#metaclass", 15)
    add_topic("Phase 2 - Advanced", "Descriptor Protocol: __get__, __set__, __delete__ — How @property works", "#descriptor", 15)
    add_topic("Phase 2 - Advanced", "Type Hints & Typing module: Any, Union, Optional, TypeVar, Generic, Literal, TypedDict", "#typing #type_hints", 30)
    add_topic("Phase 2 - Advanced", "Mypy: Static Type Checking, Strict mode, Type narrowing", "#mypy #static_typing", 15)
    add_topic("Phase 2 - Advanced", "Functional Programming: Immutability, pure functions, partial, compose", "#functional", 15)
    add_topic("Phase 2 - Advanced", "Memory Management: Reference Counting, GC, __slots__, weakref, sys.getsizeof", "#memory #gc", 15)
    add_topic("Phase 2 - Advanced", "Python Internals: CPython, Bytecode, dis module, PVM, GIL", "#cpython #gil #bytecode", 15)
    add_topic("Phase 2 - Advanced", "Walrus Operator (:=), Structural Pattern Matching (match/case Python 3.10+)", "#python310 #pattern_matching", 15)

    add_topic("Phase 2 - Advanced", "Threading: Thread, Lock, Event, Semaphore, RLock, Thread-safe", "#threading", 15)
    add_topic("Phase 2 - Advanced", "Multiprocessing: Process, Pool, Queue, Pipe, Manager, shared memory", "#multiprocessing", 15)
    add_topic("Phase 2 - Advanced", "concurrent.futures: ThreadPoolExecutor, ProcessPoolExecutor, as_completed", "#concurrent_futures", 15)
    add_topic("Phase 2 - Advanced", "AsyncIO: event loop, async/await, coroutine, Task, gather, asyncio.run", "#asyncio", 30)
    add_topic("Phase 2 - Advanced", "AsyncIO nang cao: asyncio.Queue, Semaphore, timeout, shield, TaskGroup", "#asyncio #advanced", 15)
    add_topic("Phase 2 - Advanced", "aiohttp: Async HTTP client/server, Session, WebSocket async", "#aiohttp #async", 15)

    add_topic("Phase 2 - Advanced", "SOLID Principles trong Python — Viet code sach, de mo rong", "#solid #clean_code", 15)
    add_topic("Phase 2 - Advanced", "Creational Patterns: Singleton, Factory, Abstract Factory, Builder, Prototype", "#patterns #creational", 30)
    add_topic("Phase 2 - Advanced", "Structural Patterns: Adapter, Bridge, Composite, Decorator, Facade, Proxy", "#patterns #structural", 30)
    add_topic("Phase 2 - Advanced", "Behavioral Patterns: Observer, Strategy, Command, Iterator, State, Template Method", "#patterns #behavioral", 30)
    add_topic("Phase 2 - Advanced", "Repository Pattern, Unit of Work, Dependency Injection trong Python", "#patterns #di #repository", 15)

    add_topic("Phase 2 - Advanced", "Unit Testing: unittest, assertions, setUp/tearDown, TestCase", "#testing #unittest", 15)
    add_topic("Phase 2 - Advanced", "pytest: fixtures, conftest, parametrize, marks, plugins", "#pytest", 30)
    add_topic("Phase 2 - Advanced", "Mocking: unittest.mock, MagicMock, patch, side_effect, Mock trong pytest", "#mock #testing", 15)
    add_topic("Phase 2 - Advanced", "TDD: Test-Driven Development — Red, Green, Refactor workflow trong Python", "#tdd", 15)
    add_topic("Phase 2 - Advanced", "Coverage: coverage.py, pytest-cov, Branch coverage, CI integration", "#coverage", 15)
    add_topic("Phase 2 - Advanced", "Integration Testing, E2E Testing voi pytest + Docker", "#integration_testing", 15)

    add_topic("Phase 2 - Advanced", "Profiling: cProfile, line_profiler, memory_profiler, Py-Spy", "#profiling #performance", 15)
    add_topic("Phase 2 - Advanced", "Toi uu Python: List vs Generator, local variable lookup, cache", "#optimization", 15)
    add_topic("Phase 2 - Advanced", "Cython: Bien dich Python sang C — Toc do nhu C", "#cython", 15)
    add_topic("Phase 2 - Advanced", "Numba: JIT compilation, @jit, @njit, Parallel, GPU (CUDA)", "#numba #jit", 15)
    add_topic("Phase 2 - Advanced", "ctypes, cffi: Goi ham C tu Python — Tich hop C extension", "#ctypes #cffi", 15)
    add_topic("Phase 2 - Advanced", "PyPy: Python nhanh hon voi JIT — When to use PyPy vs CPython", "#pypy", 15)

    # =====================================================================
    # PHASE 3: WEB DEVELOPMENT (Day ~1101 - ~1700)
    # =====================================================================

    add_topic("Phase 3 - Web Dev", "HTTP Protocol: Methods, Status codes, Headers, REST vs GraphQL vs gRPC", "#http #rest", 15)
    add_topic("Phase 3 - Web Dev", "requests: GET/POST/PUT/DELETE, Session, Auth, Retry, Timeout, SSL", "#requests #http_client", 15)
    add_topic("Phase 3 - Web Dev", "httpx: Async HTTP client, HTTP/2, retry middleware", "#httpx #async", 15)

    add_topic("Phase 3 - Web Dev", "FastAPI: Setup, Path/Query params, Request Body, Response Model", "#fastapi", 15)
    add_topic("Phase 3 - Web Dev", "FastAPI: Pydantic v2 validation, BaseModel, Field, model_validator", "#fastapi #pydantic", 15)
    add_topic("Phase 3 - Web Dev", "FastAPI: Dependency Injection, Security (OAuth2, JWT, API Key)", "#fastapi #security #jwt", 15)
    add_topic("Phase 3 - Web Dev", "FastAPI: BackgroundTask, Middleware, CORS, Static Files, Lifespan", "#fastapi #middleware", 15)
    add_topic("Phase 3 - Web Dev", "FastAPI: WebSocket real-time, Server-Sent Events (SSE)", "#fastapi #websocket", 15)
    add_topic("Phase 3 - Web Dev", "FastAPI: Testing voi TestClient, pytest, Mock dependencies", "#fastapi #testing", 15)
    add_topic("Phase 3 - Web Dev", "FastAPI: Deploy: Uvicorn, Gunicorn, Docker, Nginx reverse proxy", "#fastapi #deploy", 15)

    add_topic("Phase 3 - Web Dev", "Django: MTV Architecture, settings, URL routing, Apps", "#django", 15)
    add_topic("Phase 3 - Web Dev", "Django ORM: Models, Field types, Migrations, queryset, F/Q objects", "#django #orm", 30)
    add_topic("Phase 3 - Web Dev", "Django ORM nang cao: select_related, prefetch_related, annotate, aggregate", "#django #orm #advanced", 15)
    add_topic("Phase 3 - Web Dev", "Django Views: FBV, CBV, Mixins, Generic Views", "#django #views", 15)
    add_topic("Phase 3 - Web Dev", "Django Templates: Template language, Inheritance, Tags, Filters, Context", "#django #templates", 15)
    add_topic("Phase 3 - Web Dev", "Django Forms: ModelForm, Validation, Widgets, Formsets, CSRF", "#django #forms", 15)
    add_topic("Phase 3 - Web Dev", "Django Auth: User model, Custom User, Permissions, Groups, Decorators", "#django #auth", 15)
    add_topic("Phase 3 - Web Dev", "Django REST Framework (DRF): Serializers, ViewSets, Routers, Permissions", "#drf #api", 30)
    add_topic("Phase 3 - Web Dev", "DRF nang cao: Throttling, Pagination, Filtering, JWT voi Simple JWT", "#drf #jwt", 15)
    add_topic("Phase 3 - Web Dev", "Django Channels: WebSocket, ASGI, Layer, Consumer, Groups", "#django #websocket #channels", 15)
    add_topic("Phase 3 - Web Dev", "Django Celery: Task queue, Beat scheduler, Redis broker, Monitoring Flower", "#celery #task_queue", 15)
    add_topic("Phase 3 - Web Dev", "Django Testing: TestCase, Client, Factory Boy, pytest-django", "#django #testing", 15)
    add_topic("Phase 3 - Web Dev", "Django Production: Caching (Redis/Memcached), Static/Media files, Security", "#django #production", 15)

    add_topic("Phase 3 - Web Dev", "Flask: Routes, Templates (Jinja2), Request/Response, Blueprints", "#flask", 15)
    add_topic("Phase 3 - Web Dev", "Flask: SQLAlchemy integration, Flask-Login, Flask-WTF, Flask-Mail", "#flask #extensions", 15)
    add_topic("Phase 3 - Web Dev", "Flask: Testing, Application factory pattern, Config management", "#flask #testing", 15)

    add_topic("Phase 3 - Web Dev", "BeautifulSoup4: Parse HTML/XML, CSS selectors, Tag navigation", "#beautifulsoup #scraping", 15)
    add_topic("Phase 3 - Web Dev", "Scrapy: Spider, Item, Pipeline, Middleware, CrawlSpider, Settings", "#scrapy", 30)
    add_topic("Phase 3 - Web Dev", "Playwright Python: Browser automation, Page, Locator, Screenshot, Network", "#playwright #automation", 30)
    add_topic("Phase 3 - Web Dev", "Selenium: WebDriver, Waits, Actions, Headless, Grid, Anti-detection", "#selenium", 15)
    add_topic("Phase 3 - Web Dev", "Anti-bot: Proxy rotation, User-Agent, Captcha solving, Rate limiting", "#scraping #antibot", 15)

    add_topic("Phase 3 - Web Dev", "SQL nang cao: JOIN, Subquery, CTE, Window Functions, Index, Explain", "#sql #advanced", 30)
    add_topic("Phase 3 - Web Dev", "SQLAlchemy Core: Engine, Connection, Table, Insert/Select/Update/Delete", "#sqlalchemy #orm", 15)
    add_topic("Phase 3 - Web Dev", "SQLAlchemy ORM: Session, Relationship, Lazy/Eager loading, Events", "#sqlalchemy #orm", 15)
    add_topic("Phase 3 - Web Dev", "Alembic: Database Migration, Auto-generate, Upgrade/Downgrade", "#alembic #migration", 15)
    add_topic("Phase 3 - Web Dev", "SQLModel: FastAPI + SQLAlchemy unified (Pydantic + ORM)", "#sqlmodel", 15)
    add_topic("Phase 3 - Web Dev", "PostgreSQL nang cao: JSONB, Full-text Search, pg_trgm, Partitioning", "#postgresql", 15)
    add_topic("Phase 3 - Web Dev", "MongoDB voi PyMongo / Motor (async): CRUD, Aggregation pipeline, Index", "#mongodb #motor", 15)
    add_topic("Phase 3 - Web Dev", "Redis voi redis-py / aioredis: Cache, Pub/Sub, Stream, Sorted Set", "#redis #cache", 15)
    add_topic("Phase 3 - Web Dev", "Elasticsearch voi Python: Indexing, Query DSL, Aggregation, Vector Search", "#elasticsearch", 15)

    # =====================================================================
    # PHASE 4: DATA SCIENCE & MACHINE LEARNING (Day ~1701 - ~2300)
    # =====================================================================

    add_topic("Phase 4 - Data Science & ML", "NumPy: ndarray, Broadcasting, Vectorization, Advanced Indexing, Linear Algebra", "#numpy", 30)
    add_topic("Phase 4 - Data Science & ML", "Pandas: Series, DataFrame, IO (CSV/Excel/Parquet), Index, MultiIndex", "#pandas", 30)
    add_topic("Phase 4 - Data Science & ML", "Pandas nang cao: groupby, merge/join, pivot_table, resample, apply, Styler", "#pandas #advanced", 30)
    add_topic("Phase 4 - Data Science & ML", "Data Cleaning: Missing values, Outlier detection, Dtype optimization", "#data_cleaning", 15)
    add_topic("Phase 4 - Data Science & ML", "Exploratory Data Analysis (EDA): Descriptive stats, Correlation, Distribution", "#eda", 15)
    add_topic("Phase 4 - Data Science & ML", "Matplotlib: Figure, Axes, subplots, Plots (line, bar, scatter, hist, pie)", "#matplotlib #visualization", 15)
    add_topic("Phase 4 - Data Science & ML", "Seaborn: Statistical plots, heatmap, pairplot, FacetGrid, Theme", "#seaborn", 15)
    add_topic("Phase 4 - Data Science & ML", "Plotly & Dash: Interactive charts, Choropleth, 3D plots, Dashboard", "#plotly #dash", 15)
    add_topic("Phase 4 - Data Science & ML", "Polars: DataFrame nhanh hon Pandas 10x — Lazy, Expressions, Streaming", "#polars", 15)

    add_topic("Phase 4 - Data Science & ML", "ML Fundamentals: Supervised/Unsupervised/RL, Bias-Variance, Overfitting", "#ml #fundamentals", 15)
    add_topic("Phase 4 - Data Science & ML", "Scikit-learn: API (fit/predict), Pipeline, ColumnTransformer, Cross-validation", "#sklearn", 15)
    add_topic("Phase 4 - Data Science & ML", "Classification: Logistic Regression, SVM, KNN, Decision Tree, Random Forest", "#sklearn #classification", 15)
    add_topic("Phase 4 - Data Science & ML", "Regression: Linear, Ridge, Lasso, ElasticNet, SVR, Polynomial Regression", "#sklearn #regression", 15)
    add_topic("Phase 4 - Data Science & ML", "Ensemble: Bagging, Boosting, Voting, Stacking, XGBoost, LightGBM, CatBoost", "#ensemble #xgboost", 30)
    add_topic("Phase 4 - Data Science & ML", "Clustering: KMeans, DBSCAN, Agglomerative, Gaussian Mixture Models", "#clustering", 15)
    add_topic("Phase 4 - Data Science & ML", "Dimensionality Reduction: PCA, t-SNE, UMAP, Feature Selection", "#pca #umap", 15)
    add_topic("Phase 4 - Data Science & ML", "Hyperparameter Tuning: GridSearchCV, RandomizedSearchCV, Optuna, Ray Tune", "#hyperparameter #optuna", 15)
    add_topic("Phase 4 - Data Science & ML", "Feature Engineering: Encoding, Scaling, Text features, Time features, Target encoding", "#feature_engineering", 15)
    add_topic("Phase 4 - Data Science & ML", "Model Evaluation: Metrics (AUC, F1, MAE, RMSE), Confusion Matrix, Calibration", "#evaluation", 15)
    add_topic("Phase 4 - Data Science & ML", "Time Series: statsmodels (ARIMA, SARIMA), Prophet, Sktime", "#timeseries #arima", 15)
    add_topic("Phase 4 - Data Science & ML", "Anomaly Detection: Isolation Forest, LOF, Autoencoder, One-class SVM", "#anomaly_detection", 15)

    add_topic("Phase 4 - Data Science & ML", "Neural Network Fundamentals: Perceptron, Activation, Backprop, Gradient Descent", "#neural_network #deep_learning", 15)
    add_topic("Phase 4 - Data Science & ML", "TensorFlow 2 + Keras: Sequential, Functional API, Model subclassing, Callbacks", "#tensorflow #keras", 30)
    add_topic("Phase 4 - Data Science & ML", "PyTorch: Tensor, Autograd, nn.Module, DataLoader, Training loop", "#pytorch", 30)
    add_topic("Phase 4 - Data Science & ML", "PyTorch Lightning & Fabric: Boilerplate-free training, TPU/GPU support", "#pytorch_lightning", 15)
    add_topic("Phase 4 - Data Science & ML", "CNN: Convolution, Pooling, ResNet, VGG, EfficientNet — Image classification", "#cnn #computer_vision", 15)
    add_topic("Phase 4 - Data Science & ML", "RNN, LSTM, GRU — Sequence modeling, NLP truyen thong", "#rnn #lstm", 15)
    add_topic("Phase 4 - Data Science & ML", "Transformer Architecture: Self-attention, Multi-head, Positional Encoding", "#transformer #attention", 30)
    add_topic("Phase 4 - Data Science & ML", "Transfer Learning: Fine-tuning pretrained models, Feature extraction", "#transfer_learning", 15)
    add_topic("Phase 4 - Data Science & ML", "ONNX: Export model, Runtime, Optimize cho production inference", "#onnx #inference", 15)

    add_topic("Phase 4 - Data Science & ML", "NLP Co ban: Tokenization, Stopwords, Lemmatization, TF-IDF, Word2Vec", "#nlp", 15)
    add_topic("Phase 4 - Data Science & ML", "HuggingFace Transformers: BERT, GPT, T5, pipeline(), Trainer, Dataset", "#huggingface #bert", 30)
    add_topic("Phase 4 - Data Science & ML", "LLM Fine-tuning: LoRA, QLoRA, PEFT, Instruction tuning, SFT", "#llm #lora #finetuning", 30)
    add_topic("Phase 4 - Data Science & ML", "LangChain: Chain, Agent, Tool, Memory, RAG (Retrieval-Augmented Generation)", "#langchain #rag", 30)
    add_topic("Phase 4 - Data Science & ML", "LlamaIndex: Index, Query Engine, Node Parser, Vector Store, Observability", "#llamaindex #rag", 15)
    add_topic("Phase 4 - Data Science & ML", "OpenAI API: Chat Completion, Embeddings, Function Calling, Vision, Batch API", "#openai #gpt", 15)
    add_topic("Phase 4 - Data Science & ML", "Anthropic Claude API, Google Gemini API, Groq API — Multi-provider LLM", "#claude #gemini #groq", 15)
    add_topic("Phase 4 - Data Science & ML", "Vector Database: Chroma, Pinecone, Weaviate, Qdrant, pgvector", "#vector_db #embeddings", 15)
    add_topic("Phase 4 - Data Science & ML", "Ollama, LM Studio, vLLM: Chay LLM local (Llama3, Mistral, Phi-4)", "#ollama #local_llm", 15)
    add_topic("Phase 4 - Data Science & ML", "AI Agent: ReAct, Plan-and-Execute, Multi-agent (AutoGen, CrewAI, LangGraph)", "#ai_agent #autogen #crewai", 30)

    add_topic("Phase 4 - Data Science & ML", "OpenCV: Image processing, Filters, Morphology, Contours, Geometric transform", "#opencv #computer_vision", 15)
    add_topic("Phase 4 - Data Science & ML", "Object Detection: YOLO (v8, v11), Detectron2, DETR — Training & Inference", "#yolo #object_detection", 15)
    add_topic("Phase 4 - Data Science & ML", "Image Segmentation: Mask R-CNN, SAM (Segment Anything), Semantic Segmentation", "#segmentation #sam", 15)
    add_topic("Phase 4 - Data Science & ML", "Generative AI: Stable Diffusion, ControlNet, Image-to-Image, Inpainting (Diffusers)", "#stable_diffusion #diffusers", 15)
    add_topic("Phase 4 - Data Science & ML", "OCR: Tesseract, EasyOCR, PaddleOCR, Doctr, Table extraction", "#ocr #tesseract", 15)

    add_topic("Phase 4 - Data Science & ML", "MLflow: Experiment tracking, Model Registry, Artifact logging, UI", "#mlflow #mlops", 15)
    add_topic("Phase 4 - Data Science & ML", "DVC: Data Versioning, Pipeline, Remote storage, Experiment tracking", "#dvc #data_versioning", 15)
    add_topic("Phase 4 - Data Science & ML", "Model Serving: FastAPI + model, TorchServe, TF Serving, BentoML, Ray Serve", "#model_serving", 15)
    add_topic("Phase 4 - Data Science & ML", "Monitoring ML: Evidently, Grafana, Prometheus, Data drift, Concept drift", "#ml_monitoring", 15)
    add_topic("Phase 4 - Data Science & ML", "Kubeflow, Vertex AI Pipelines: ML workflow orchestration tren cloud", "#kubeflow #mlops", 15)

    # =====================================================================
    # PHASE 5: DEVOPS, CLOUD & INFRASTRUCTURE (Day ~2301 - ~2700)
    # =====================================================================

    add_topic("Phase 5 - DevOps & Cloud", "Docker: Dockerfile, Image, Container, Volumes, Networks, Multi-stage build", "#docker", 15)
    add_topic("Phase 5 - DevOps & Cloud", "Docker Compose: Services, Dependencies, Env, Healthcheck, Profiles", "#docker_compose", 15)
    add_topic("Phase 5 - DevOps & Cloud", "Kubernetes (K8s): Pod, Deployment, Service, Ingress, ConfigMap, Secret", "#kubernetes #k8s", 30)
    add_topic("Phase 5 - DevOps & Cloud", "Kubernetes nang cao: HPA, StatefulSet, Helm, ArgoCD, Kustomize", "#kubernetes #helm #argocd", 15)
    add_topic("Phase 5 - DevOps & Cloud", "CI/CD: GitHub Actions, GitLab CI, Jenkins — Build, Test, Deploy pipeline", "#ci_cd #github_actions", 15)
    add_topic("Phase 5 - DevOps & Cloud", "Infrastructure as Code: Terraform — Provision AWS/GCP/Azure resources", "#terraform #iac", 15)
    add_topic("Phase 5 - DevOps & Cloud", "Ansible: Playbook, Role, Inventory, Modules — Configuration management", "#ansible", 15)

    add_topic("Phase 5 - DevOps & Cloud", "AWS Core: EC2, S3, RDS, VPC, IAM, Lambda, API Gateway, SQS, SNS", "#aws", 30)
    add_topic("Phase 5 - DevOps & Cloud", "AWS SDK: boto3 — S3, DynamoDB, Lambda, SES, Rekognition, Textract", "#boto3 #aws", 15)
    add_topic("Phase 5 - DevOps & Cloud", "GCP: Cloud Run, BigQuery, Vertex AI, Cloud Functions, Pub/Sub", "#gcp", 15)
    add_topic("Phase 5 - DevOps & Cloud", "Azure: Azure Functions, AKS, Azure ML, Cosmos DB, Service Bus", "#azure", 15)
    add_topic("Phase 5 - DevOps & Cloud", "Serverless: AWS Lambda + Python, Cold start, Layers, Mangum (FastAPI on Lambda)", "#serverless #lambda", 15)

    add_topic("Phase 5 - DevOps & Cloud", "Kafka voi Python: Producer, Consumer, Avro, Schema Registry, Faust stream", "#kafka", 15)
    add_topic("Phase 5 - DevOps & Cloud", "RabbitMQ voi pika/aio-pika: Exchange, Queue, Routing key, Dead letter", "#rabbitmq", 15)
    add_topic("Phase 5 - DevOps & Cloud", "Event-driven Architecture: CQRS, Event Sourcing, Saga, Outbox Pattern", "#event_driven #cqrs", 15)

    add_topic("Phase 5 - DevOps & Cloud", "Logging: logging module, structlog, JSON logging, Log aggregation (ELK, Loki)", "#logging #observability", 15)
    add_topic("Phase 5 - DevOps & Cloud", "Tracing: OpenTelemetry Python, Jaeger, Zipkin, Datadog, Sentry", "#opentelemetry #tracing", 15)
    add_topic("Phase 5 - DevOps & Cloud", "Metrics: Prometheus client_python, Grafana dashboard, Alertmanager", "#prometheus #grafana", 15)

    add_topic("Phase 5 - DevOps & Cloud", "Python Security: OWASP Top 10, SQL Injection, XSS, CSRF, SSRF prevention", "#security #owasp", 15)
    add_topic("Phase 5 - DevOps & Cloud", "Cryptography: hashlib, secrets, cryptography library, JWT, OAuth2 implementation", "#cryptography #jwt", 15)
    add_topic("Phase 5 - DevOps & Cloud", "Penetration Testing: scapy, paramiko, ldap3, impacket — Ethical hacking tools", "#pentest #security", 15)

    # =====================================================================
    # PHASE 6: SPECIALIZED & EMERGING (Day ~2701 - 3000)
    # =====================================================================

    add_topic("Phase 6 - Specialized", "Apache Spark voi PySpark: RDD, DataFrame, SQL, MLlib, Streaming", "#pyspark #spark", 15)
    add_topic("Phase 6 - Specialized", "Apache Airflow: DAG, Operator, Sensor, XCom, Connections, Plugins", "#airflow #data_pipeline", 15)
    add_topic("Phase 6 - Specialized", "Prefect & Dagster: Modern data orchestration — Flow, Task, Asset", "#prefect #dagster", 15)
    add_topic("Phase 6 - Specialized", "Data Lake: Delta Lake, Apache Iceberg, Hudi, dbt (Data Build Tool)", "#datalake #dbt", 15)
    add_topic("Phase 6 - Specialized", "Streaming: Kafka Streams, Spark Structured Streaming, Flink voi PyFlink", "#streaming #flink", 15)

    add_topic("Phase 6 - Specialized", "Tkinter: Widget, Layout, Event handling, Custom widget, ttk", "#tkinter #gui", 15)
    add_topic("Phase 6 - Specialized", "PyQt6 / PySide6: QWidget, Signal/Slot, Model/View, Thread worker, QML", "#pyqt #gui", 15)
    add_topic("Phase 6 - Specialized", "Kivy: Cross-platform (Mobile + Desktop), KV Language, Gestures", "#kivy #mobile", 15)
    add_topic("Phase 6 - Specialized", "PyInstaller, cx_Freeze, Nuitka: Dong goi Python thanh EXE / app", "#packaging #exe", 15)

    add_topic("Phase 6 - Specialized", "System Automation: psutil, subprocess, watchdog, schedule, crontab", "#automation #system", 15)
    add_topic("Phase 6 - Specialized", "Office Automation: openpyxl, xlrd, python-docx, pptx, PDF (pypdf, pdfplumber)", "#office_automation", 15)
    add_topic("Phase 6 - Specialized", "Email & Notification: smtplib, email, imaplib, slack_sdk, telegram.ext", "#email #notification", 15)
    add_topic("Phase 6 - Specialized", "Win32 Automation: pywin32, pyautogui, keyboard, mouse — Windows scripting", "#win32 #automation", 15)

    add_topic("Phase 6 - Specialized", "Socket Programming: TCP/UDP Server/Client, Non-blocking, asyncio streams", "#socket #networking", 15)
    add_topic("Phase 6 - Specialized", "Network Tools: Scapy (packet crafting), nmap (python-nmap), netmiko (SSH)", "#scapy #netmiko", 15)
    add_topic("Phase 6 - Specialized", "FastStream: Kafka/RabbitMQ/SQS handler theo phong cach FastAPI", "#faststream #messaging", 15)

    add_topic("Phase 6 - Specialized", "Pygame: Surface, Sprite, Event, Collision, Sound, Game loop", "#pygame #gamedev", 15)
    add_topic("Phase 6 - Specialized", "Arcade: Modern game engine, Sprite, TileMap, Physics, Shader", "#arcade #gamedev", 15)
    add_topic("Phase 6 - Specialized", "Python + Godot (GDScript fallback), Ren'Py (Visual Novel)", "#godot #renpy", 15)

    add_topic("Phase 6 - Specialized", "MicroPython: ESP32/ESP8266, GPIO, PWM, I2C, SPI, MQTT, BLE", "#micropython #iot", 15)
    add_topic("Phase 6 - Specialized", "CircuitPython: Adafruit boards, Sensors, NeoPixel, USB HID", "#circuitpython", 15)
    add_topic("Phase 6 - Specialized", "Raspberry Pi voi Python: GPIO, Camera, UART, SPI, I2C — Home Automation", "#raspberrypi", 15)

    add_topic("Phase 6 - Specialized", "Web3.py: Ethereum, Smart Contract interaction, ABI, Transaction signing", "#web3 #ethereum", 15)
    add_topic("Phase 6 - Specialized", "Solana voi Python: solders, solana-py, SPL Token, NFT minting", "#solana #web3", 15)

    add_topic("Phase 6 - Specialized", "SciPy: Optimization, Integration, Signal processing, Linear algebra", "#scipy", 15)
    add_topic("Phase 6 - Specialized", "SymPy: Symbolic math, Calculus, Equation solving, Code generation", "#sympy #math", 15)
    add_topic("Phase 6 - Specialized", "Quantum Computing: Qiskit (IBM), PennyLane — Quantum circuits voi Python", "#quantum #qiskit", 15)

    add_topic("Phase 6 - Specialized", "Clean Architecture: Domain, Application, Infrastructure layers trong Python", "#clean_architecture", 15)
    add_topic("Phase 6 - Specialized", "Hexagonal Architecture (Ports & Adapters) trong Python projects", "#hexagonal #architecture", 15)
    add_topic("Phase 6 - Specialized", "Microservices voi Python: Service mesh, API gateway, Service discovery", "#microservices", 15)
    add_topic("Phase 6 - Specialized", "Event Sourcing & DDD (Domain-Driven Design) trong Python", "#ddd #event_sourcing", 15)
    add_topic("Phase 6 - Specialized", "Python Package Publishing: pyproject.toml, hatch, poetry, PyPI, versioning", "#packaging #pypi", 15)
    add_topic("Phase 6 - Specialized", "Open Source Contribution: Git flow, PR etiquette, Code review, Documentation", "#opensource #contribution", 15)
    
    # Pad den dung 3000 ngay neu thieu hoac thua xiu
    while day <= 3000:
        add_topic("Phase 6 - Specialized", "Tong ket & Portfolio: Tao 5 du an Python thuc te tu dau den cuoi", "#portfolio #project", 15)

    return roadmap[:3000] # Dam bao dung 3000


def generate_markdown(roadmap):
    total = len(roadmap)
    md_lines = [
        "# Python — Lo Trinh Tu 0 Den Master Toan Bo He Sinh Thai (3000 Ngay / ~8 Nam)",
        "",
        "> Muc tieu: Nam vung Python tu nen tang den chuyen gia, bao phu TOAN BO cac cong nghe va linh vuc Python co the lam duoc nam 2025 va tuong lai.",
        "> Thoi luong: 30-60 phut/ngay cho moi buoi hoc. 3000 'Day' = 3000 Don vi noi dung, khong phai so ngay lich.",
        "> Trinh tu: Foundation -> Advanced -> Web Dev -> Data/ML/AI/LLM -> DevOps/Cloud -> Specialized (GUI, IoT, Game, Blockchain, Quantum...)",
        "",
        "> Ky hieu: Foundation | Advanced | Web Dev | Data+ML+AI | DevOps+Cloud | Specialized",
        "",
    ]
    
    focus_areas = [
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
        "Security: Các lỗ hổng bảo mật tiềm ẩn (XSS, Injection, Prototype Pollution...) và cách phòng chống.",
        "Structural Design Patterns: Áp dụng các Design Pattern về mặt cấu trúc (Structural) cho chủ đề này.",
        "Behavioral Design Patterns: Áp dụng các Design Pattern về mặt hành vi (Behavioral) để quản lý luồng.",
        "Anti-patterns: Những cách viết TỒI TỆ NHẤT, những 'red flags' tuyệt đối phải tránh khi dùng công nghệ này.",
        "Unit Testing: Cách mock/stub và viết bài test cục bộ (Unit Test) cho tính năng này.",
        "Integration Testing: Viết test tích hợp luồng dữ liệu hoặc E2E test.",
        "Deep Debugging: Kỹ thuật gỡ lỗi chuyên sâu dùng DevTools, breakpoints, và Profiler.",
        "Polyfill & Compatibility: Xử lý tương thích đa môi trường (Cross-browser, phiên bản cũ, fallback).",
        "Ecosystem Integration: Best practices khi kết hợp với thư viện/framework/công cụ thứ 3.",
        "Config & Bundling: Tương tác và cấu hình với các công cụ build (Webpack, Vite, Rollup...).",
        "CI/CD Automation: Cách tự động hóa kiểm tra tính năng này trên pipeline (GitHub Actions, Jenkins).",
        "Open Source Analysis: Mổ xẻ đọc code thực tế của dự án lớn xem họ triển khai chủ đề này ra sao.",
        "Interview Prep (Junior/Mid): Trả lời lý thuyết cốt lõi và giải quyết bài tập nhỏ thường gặp khi phỏng vấn.",
        "Interview Prep (Senior): System Design, trade-offs, và trả lời các câu hỏi kiến trúc hóc búa.",
        "Reinvent the wheel (Phase 1): Tự code lại công nghệ này từ con số 0 - Phân tích và Khởi tạo cấu trúc.",
        "Reinvent the wheel (Phase 2): Tự code lại - Triển khai Core Logic cốt lõi.",
        "Capstone Phase 1: Áp dụng vào Mini-Project thực tế - Lên ý tưởng & Thiết kế kiến trúc.",
        "Capstone Phase 2: Áp dụng vào Mini-Project - Code nghiệp vụ chính và luồng dữ liệu.",
        "Capstone Phase 3: Áp dụng vào Mini-Project - Hoàn thiện, Review, Refactor và Đóng gói."
    ]

    for (day, section, topic, tags, part, total_parts) in roadmap:
        progress = f"(Phan {part}/{total_parts})"
        short_section = section.split(" - ")[1] if " - " in section else section

        md_lines.append(f"## Day {day} — [{short_section}] {topic} {progress}")
        md_lines.append("**Prompt:**")
        md_lines.append(f"Day {day} trong lo trinh Python 3000 ngay / 8 nam.")
        md_lines.append(f"Chuyen de: [{section}] — {topic} {progress}.")
        md_lines.append(f"Trinh do hien tai: Xem cac ngay truoc de biet nguoi hoc dang o dau trong lo trinh.")
        md_lines.append("")
        
        focus = focus_areas[(part - 1) % len(focus_areas)]
        md_lines.append(f"**Yêu cầu ĐẶC BIỆT cho {progress}:**")
        md_lines.append(f"Hôm nay, BẮT BUỘC bỏ qua các phần lý thuyết chung chung đã học. Hãy tập trung 100% vào khía cạnh sau: **[{focus}]**")
        md_lines.append("Hãy viết giáo trình, code mẫu và giải thích ĐÚNG trọng tâm vào khía cạnh này.")
        md_lines.append("")
        
        if part in [13, 14, 15]:
            md_lines.append("(⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)")
            md_lines.append("")

        md_lines.append("Yeu cau day hoc (30-60 phut):")
        md_lines.append("1. GIAI THICH TRỌNG TÂM: Giải thích ngắn gọn nhưng ĐÚNG vào khía cạnh được yêu cầu.")
        md_lines.append("2. CODE MẪU CHUYÊN SÂU: Đoạn code ví dụ tập trung trực tiếp vào khía cạnh hôm nay, comment từng dòng.")
        md_lines.append("3. ÁP DỤNG THỰC TẾ: Khía cạnh này được sử dụng thế nào trong dự án production?")
        md_lines.append("")
        md_lines.append("Bai tap (3 cap do, tu lam truoc khi xem dap an):")
        md_lines.append("- Bai 1 (Co ban): Hieu va go lai vi du co ban theo huong tiep can hom nay.")
        md_lines.append("- Bai 2 (Trung cap): Mo rong tinh nang hoac toi uu code.")
        md_lines.append("- Bai 3 (Nang cao): Ap dung vao 1 mini-project/script thu nghiem.")
        md_lines.append("")
        md_lines.append("**Bài tập:**")
        md_lines.append(f"- Bài 1 (Cơ bản): Hoàn thành ví dụ cơ bản về [{focus}].")
        md_lines.append(f"- Bài 2 (Trung cấp): Mở rộng code và xử lý edge cases cho [{focus}].")
        md_lines.append(f"- Bài 3 (Nâng cao): Áp dụng [{focus}] vào mini-tool thực tế.")
        md_lines.append("")
        md_lines.append(f"**Tags:** #python #day{day} {tags} #{short_section.lower().replace(' ', '_')}")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))


if __name__ == "__main__":
    data = build_roadmap()
    generate_markdown(data)
    total = len(data)
    print("Done! Generated: " + filepath)
    print("Total days: " + str(total))
    sections = {}
    for (day, section, topic, tags, part, total_parts) in data:
        s = section.split(" - ")[1] if " - " in section else section
        if s not in sections:
            sections[s] = (day, day)
        else:
            sections[s] = (sections[s][0], day)
    for s, (start, end) in sections.items():
        print(f"  {s}: Day {start} - {end}")
