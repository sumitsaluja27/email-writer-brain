apple@007s-Mac email_writer % cd "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer"
python3 src/test_beacon_rag.py
/Users/apple/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(

--- Testing Beacon RAG Retrieval ---
Loading Beacon RAG from: /Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/knowledge_base/beacon_capabilities
Using Embedding Model: mxbai-embed-large
/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/src/test_beacon_rag.py:21: LangChainDeprecationWarning: The class `OllamaEmbeddings` was deprecated in LangChain 0.3.1 and will be removed in 1.0.0. An updated version of the class exists in the :class:`~langchain-ollama package and should be used instead. To use it run `pip install -U :class:`~langchain-ollama` and import as `from :class:`~langchain_ollama import OllamaEmbeddings``.
  embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)
/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/src/test_beacon_rag.py:25: LangChainDeprecationWarning: The class `Chroma` was deprecated in LangChain 0.2.9 and will be removed in 1.0. An updated version of the class exists in the :class:`~langchain-chroma package and should be used instead. To use it run `pip install -U :class:`~langchain-chroma` and import as `from :class:`~langchain_chroma import Chroma``.
  beacon_db = Chroma(persist_directory=BEACON_CHROMA_PATH, embedding_function=embeddings)
Beacon RAG loaded successfully.

Performing similarity search with query: "What types of beacons does Rapidise offer?"

--- Top 3 Retrieved Chunks ---

--- Chunk 1 (Score: 156.5631) ---
Content:
or Nordic (nRF52805 or nRF52820) chipsets. These chips facilitate 
communication using Bluetooth 5.3 or earlier standards, offering up to a 100m 
range in open areas. 
• Power Efficiency: The beacons are powered by non-rechargeable Li-ion coin 
cell batteries (CR2032 or CR2450) and are optimized for low power 
consumption, allowing for a typical lifespan of 3+ years. 
• Advertising (The Signal): The beacon's primary function is to continuously 
broadcast an Advertising (ADV) packet at set intervals (default is 5 seconds). 
This broadcast signal is the source of all system data. 
2. Signal Content and Formats 
The information broadcasted is packaged into various standardized formats: 
• Standard Formats: All Rapidise models support Apple iBeacon and Google 
Eddystone formats (including UID, URL, and TLM). Custom formats are also 
supported. 
• Location Data: The beacon broadcasts the RSSI (Received Signal Strength

Metadata:
  author: Sumit Saluja
  creationdate: 2025-11-05T20:17:55-08:00
  product: beacon
  page: 0
  source: 4._technical_and_operational_-_function.pdf
  moddate: 2025-11-05T20:17:55-08:00
  content_type: capability_pdf
  producer: PyPDF
  creator: Microsoft Word
  total_pages: 3
  page_label: 1
-----------------------------

--- Chunk 2 (Score: 164.5674) ---
Content:
The Rapidise BLE Beacon product line includes five primary models for which detailed 
specifications are available: N1, N2, N3, N4, and N14. An additional variant, the IN610 
Variant, is also part of the lineup, known for supporting Apple Find My and Google Find 
My functionality. 
The BLE Beacons are positioned as a balanced choice for indoor visibility, efficiency, 
and scale, offering affordability, accuracy (~2 to 3m), and low power consumption for 
use cases like Asset Tracking, Indoor Navigation, and Environmental Monitoring. 
Below are the key features and detailed specifications for the primary Rapidise Beacon 
models: 
Rapidise BLE Beacon Lineup and Key Features 
Model Key Feature Summary Ideal Use Cases 
N1 Entry-level, compact. 
Indoor Navigation, Proximity Marketing, 
Asset Tracking, Security & Access 
Control, Event Management. 
N2 Temp + humidity sensors. 
Environmental Monitoring, Retail 
Promotions, Asset Tracking, Security & 
Access Control, Event Management.

Metadata:
  author: Sumit Saluja
  creator: Microsoft Word
  product: beacon
  moddate: 2025-11-05T20:17:26-08:00
  total_pages: 3
  page_label: 1
  page: 0
  content_type: capability_pdf
  source: 1._types_of_beacon_and_specs.pdf
  creationdate: 2025-11-05T20:17:26-08:00
  producer: PyPDF
-----------------------------

--- Chunk 3 (Score: 175.8723) ---
Content:
IwayPlus Meets Rapidise
A Perfect Hardware3Software Collaboration
IwayPlus, a system Integrator, was selected to build an Indoor Navigation System, 
essentially a "GPS for indoors". For reliability, accuracy, and scalability, they partnered with 
Rapidise, a world-class ODM specializing in BLE beacons and IoT hardware.
Reliability
Rapidise Solution: Beacons with 
industrial-grade components and 
long-life batteries
Benefit: 24/7 uptime, minimal 
maintenance
Accuracy
Rapidise Solution: Optimized signal 
stability and calibrated RSSI design
Benefit: Sub-2m indoor positioning 
accuracy
Scalability
Rapidise Solution: Complete ODM pipeline for high-volume deployment
Benefit: Fast rollout across entire campus
3

Metadata:
  total_pages: 5
  creationdate: D:20251022100921Z00'00'
  product: beacon
  page_label: 3
  content_type: capability_pdf
  creator: pdf-lib (https://github.com/Hopding/pdf-lib)
  producer: GPL Ghostscript 9.56.1
  source: case_study.pdf
  page: 2
  moddate: D:20251022100921Z00'00'
-----------------------------