# Factory Pattern Implementation for RAG API

## Overview

We've successfully implemented a comprehensive factory pattern for the RAG API, creating a modular and extensible architecture for both inference managers and LLM providers.

## New Directory Structure

```
apis/rag/
├── inference/                          # NEW: Inference managers package
│   ├── __init__.py                    # Public API exports
│   ├── base.py                        # Abstract InferenceManagerBase
│   ├── factory.py                     # InferenceManagerFactory
│   └── langchain_manager.py           # LangChainInferenceManager (moved from root)
├── providers/                         # EXISTING: LLM providers package
│   ├── __init__.py
│   ├── base.py
│   ├── bedrock.py
│   ├── factory.py
│   └── local_llamacpp.py
└── handlers/
    └── factory_info.py                # NEW: Factory information endpoints
```

## Key Components

### 1. Inference Manager Factory (`inference/factory.py`)

```python
from apis.rag.inference import InferenceManagerFactory

# Get specific manager type
manager = InferenceManagerFactory.get_manager('langchain')

# Get first available manager with fallback
manager = InferenceManagerFactory.get_available_manager()

# Get factory information
info = InferenceManagerFactory.get_manager_info()
```

**Supported Manager Types:**
- `langchain` - LangChain-based inference (default)
- `direct` - Direct HTTP calls (future implementation)

### 2. Inference Manager Base (`inference/base.py`)

Abstract interface that all inference managers must implement:

```python
class InferenceManagerBase(ABC):
    @property
    @abstractmethod
    def is_available(self) -> bool: ...
    
    @property
    @abstractmethod
    def is_loaded(self) -> bool: ...
    
    @abstractmethod
    def load_model(self, model_id: str) -> dict: ...
    
    @abstractmethod
    def stream_generate(self, prompt: str, **kwargs) -> Generator[str, None, None]: ...
```

### 3. LangChain Manager (`inference/langchain_manager.py`)

Enhanced LangChain inference manager with:
- Flask app context graceful handling
- Automatic provider selection via `LLMProviderFactory`
- LangSmith tracing support
- Interface compatibility with existing `ModelManager`

### 4. New Factory Information Endpoints

- `GET /rag/factory/info` - Complete factory status
- `GET /rag/factory/managers` - Inference manager details
- `GET /rag/factory/providers` - LLM provider details

### 5. Enhanced Health Endpoint

Updated `/rag/health` endpoint now includes:

```json
{
  "inference_manager": {
    "type": "LangChainInferenceManager",
    "status": "healthy",
    "manager_type": "langchain"
  },
  "llm_provider": {
    "status": "healthy", 
    "type": "LocalLlamaCppProvider",
    "environment": "local"
  }
}
```

## Configuration

### Environment Variables

```bash
# Inference manager selection
INFERENCE_MANAGER_TYPE=langchain    # langchain|direct

# LLM provider environment
DEPLOYMENT_ENV=local                # local|staging|production

# LangSmith tracing (optional)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_key
LANGSMITH_PROJECT=landuse-rag
```

## Integration Points

### RAG Engine Integration

The RAG engine now uses the factory pattern:

```python
# OLD:
from .langchain_inference import LangChainInferenceManager
self.model_mgr = LangChainInferenceManager()

# NEW:
from .inference import InferenceManagerFactory
self.model_mgr = InferenceManagerFactory.get_available_manager()
```

### Backward Compatibility

All existing interfaces are preserved:
- `model_mgr.is_available`
- `model_mgr.is_loaded`
- `model_mgr.load_model(model_id)`
- `model_mgr.stream_generate(prompt, **kwargs)`

## Benefits

### 1. **Modular Architecture**
- Clean separation between inference strategies and LLM providers
- Easy to add new manager types (direct HTTP, other frameworks)
- Professional package structure

### 2. **Automatic Fallback**
- Graceful degradation when preferred managers unavailable
- Comprehensive error handling and logging
- Environment-aware selection

### 3. **Enhanced Observability**
- Factory status endpoints for debugging
- Enhanced health checks with manager/provider details
- Comprehensive logging with Flask context handling

### 4. **Developer Experience**
- Clear interfaces and documentation
- Type hints throughout
- Standalone testing capabilities

### 5. **Future Extensibility**
- Ready for new inference manager implementations
- Prepared for additional LLM provider types
- Scalable configuration management

## Testing

### Standalone Validation
```bash
python apis/rag/test_factory_structure.py
```

### Factory Information
```bash
curl http://localhost:8001/rag/factory/info
curl http://localhost:8001/rag/factory/managers
curl http://localhost:8001/rag/factory/providers
```

### Health Check
```bash
curl http://localhost:8001/rag/health
```

## Migration Summary

✅ **Completed:**
- Created `inference/` package with factory pattern
- Moved `LangChainInferenceManager` to proper location
- Added abstract base class for inference managers
- Enhanced health endpoints with factory information
- Added comprehensive factory information endpoints
- Updated RAG engine to use factory pattern
- Maintained full backward compatibility
- Added graceful Flask context handling
- Created validation tests

🚀 **Ready for Future Extensions:**
- Direct HTTP inference manager
- Alternative LLM frameworks (Hugging Face, OpenAI, etc.)
- Custom inference strategies
- Enhanced monitoring and metrics

The factory pattern implementation provides a robust, scalable foundation for the RAG API while maintaining all existing functionality and preparing for future enhancements.