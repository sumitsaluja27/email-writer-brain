apple@007s-Mac email_writer % python3 src/query_rag.py "What are the main features of Rapidise's telematics solutions?"
/Users/apple/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(

A module that was compiled using NumPy 1.x cannot be run in
NumPy 2.0.2 as it may crash. To support both 1.x and 2.x
versions of NumPy, modules must be compiled with NumPy 2.0.
Some module may need to rebuild instead e.g. with 'pybind11>=2.12'.

If you are a user of the module, the easiest solution will be to
downgrade to 'numpy<2' or try to upgrade the affected module.
We expect that some modules will need time to support NumPy 2.

Traceback (most recent call last):  File "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/src/query_rag.py", line 5, in <module>
    from langchain_community.llms import Ollama
  File "/Users/apple/Library/Python/3.9/lib/python/site-packages/langchain_community/llms/__init__.py", line 24, in <module>
    from langchain_core.language_models.llms import BaseLLM
  File "/Users/apple/Library/Python/3.9/lib/python/site-packages/langchain_core/language_models/llms.py", line 47, in <module>
    from langchain_core.language_models.base import (
  File "/Users/apple/Library/Python/3.9/lib/python/site-packages/langchain_core/language_models/base.py", line 44, in <module>
    from transformers import GPT2TokenizerFast  # type: ignore[import-not-found]
  File "/Users/apple/Library/Python/3.9/lib/python/site-packages/transformers/__init__.py", line 27, in <module>
    from . import dependency_versions_check
  File "/Users/apple/Library/Python/3.9/lib/python/site-packages/transformers/dependency_versions_check.py", line 16, in <module>
    from .utils.versions import require_version, require_version_core
  File "/Users/apple/Library/Python/3.9/lib/python/site-packages/transformers/utils/__init__.py", line 24, in <module>
    from .auto_docstring import (
  File "/Users/apple/Library/Python/3.9/lib/python/site-packages/transformers/utils/auto_docstring.py", line 30, in <module>
    from .generic import ModelOutput
  File "/Users/apple/Library/Python/3.9/lib/python/site-packages/transformers/utils/generic.py", line 51, in <module>
    import torch
  File "/Users/apple/Library/Python/3.9/lib/python/site-packages/torch/__init__.py", line 1477, in <module>
    from .functional import *  # noqa: F403
  File "/Users/apple/Library/Python/3.9/lib/python/site-packages/torch/functional.py", line 9, in <module>
    import torch.nn.functional as F
  File "/Users/apple/Library/Python/3.9/lib/python/site-packages/torch/nn/__init__.py", line 1, in <module>
    from .modules import *  # noqa: F403
  File "/Users/apple/Library/Python/3.9/lib/python/site-packages/torch/nn/modules/__init__.py", line 35, in <module>
    from .transformer import TransformerEncoder, TransformerDecoder, \
  File "/Users/apple/Library/Python/3.9/lib/python/site-packages/torch/nn/modules/transformer.py", line 20, in <module>
    device: torch.device = torch.device(torch._C._get_default_device()),  # torch.device('cpu'),
/Users/apple/Library/Python/3.9/lib/python/site-packages/torch/nn/modules/transformer.py:20: UserWarning: Failed to initialize NumPy: _ARRAY_API not found (Triggered internally at /Users/runner/work/pytorch/pytorch/pytorch/torch/csrc/utils/tensor_numpy.cpp:84.)
  device: torch.device = torch.device(torch._C._get_default_device()),  # torch.device('cpu'),

--- Initializing RAG Query Agent ---
Using Embedding Model: mxbai-embed-large
Using LLM Model: llama3.1
/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/src/query_rag.py:46: LangChainDeprecationWarning: The class `OllamaEmbeddings` was deprecated in LangChain 0.3.1 and will be removed in 1.0.0. An updated version of the class exists in the :class:`~langchain-ollama package and should be used instead. To use it run `pip install -U :class:`~langchain-ollama` and import as `from :class:`~langchain_ollama import OllamaEmbeddings``.
  embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)
/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/src/query_rag.py:50: LangChainDeprecationWarning: The class `Chroma` was deprecated in LangChain 0.2.9 and will be removed in 1.0. An updated version of the class exists in the :class:`~langchain-chroma package and should be used instead. To use it run `pip install -U :class:`~langchain-chroma` and import as `from :class:`~langchain_chroma import Chroma``.
  automotive_db = Chroma(persist_directory=AUTOMOTIVE_CHROMA_PATH, embedding_function=embeddings)
Loaded Automotive RAG from /Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/knowledge_base/automotive_chroma
Loaded S&S RAG from /Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/knowledge_base/s_s_chroma
/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/src/query_rag.py:70: LangChainDeprecationWarning: The class `Ollama` was deprecated in LangChain 0.3.1 and will be removed in 1.0.0. An updated version of the class exists in the :class:`~langchain-ollama package and should be used instead. To use it run `pip install -U :class:`~langchain-ollama` and import as `from :class:`~langchain_ollama import OllamaLLM``.
  llm = Ollama(model=LLM_MODEL_NAME)

--- RAG Query Agent Ready ---
Detected domain: GENERAL
Could not determine specific domain or RAG not loaded. Skipping query.
apple@007s-Mac email_writer % 