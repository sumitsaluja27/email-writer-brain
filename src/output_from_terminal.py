apple@007s-Mac email_writer % cd "/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer"
python3 src/test_dashcam_rag.py
/Users/apple/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(

--- Testing Dashcam RAG Retrieval ---
Loading Dashcam RAG from: /Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/knowledge_base/dashcam_capabilities
Using Embedding Model: mxbai-embed-large
/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/src/test_dashcam_rag.py:21: LangChainDeprecationWarning: The class `OllamaEmbeddings` was deprecated in LangChain 0.3.1 and will be removed in 1.0.0. An updated version of the class exists in the :class:`~langchain-ollama package and should be used instead. To use it run `pip install -U :class:`~langchain-ollama` and import as `from :class:`~langchain_ollama import OllamaEmbeddings``.
  embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)
/Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/src/test_dashcam_rag.py:25: LangChainDeprecationWarning: The class `Chroma` was deprecated in LangChain 0.2.9 and will be removed in 1.0. An updated version of the class exists in the :class:`~langchain-chroma package and should be used instead. To use it run `pip install -U :class:`~langchain-chroma` and import as `from :class:`~langchain_chroma import Chroma``.
  dashcam_db = Chroma(persist_directory=DASHCAM_CHROMA_PATH, embedding_function=embeddings)
Dashcam RAG loaded successfully.

Performing similarity search with query: "What is Rapidise's deployment scale for dashcams?"

--- Top 3 Retrieved Chunks ---

--- Chunk 1 (Score: 120.9758) ---
Content:
IoT/Connected
 
Vehicle
 
solutions,
 
and
 
Telematics.
 
Their
 
ODM
 
capabilities
 
specifically
 
cover
 
Camera
 
Modules
 
&
 
Products,
 
Driver
 
Monitoring
 
Systems
 
(DMS),
 
Vision
 
Algorithms,
 
and
 
AI
 
Boxes.
 Focus  on  Dashcam-Related  Services  Rapidise  offers  several  dashcam  solutions,  often  utilizing  Qualcomm  processors  and  their  
proprietary
 
RISE
 
platforms,
 
which
 
integrate
 
advanced
 
connectivity
 
and
 
AI/Edge
 
capabilities.
 1.  Dual  Camera  Dashcam  (QCS5430  /  RISE  X1  Platform):  Rapidise  is  engaged  as  an  ODM  to  
build
 
this
 
product,
 
which
 
features
 
in-cabin
 
and
 
road-facing
 
cameras.
 
It
 
includes
 
connectivity
 
(Wi-Fi,
 
Bluetooth,
 
LTE,
 
GPS)
 
and
 
advanced
 
algorithms
 
for
 
detecting
 
events
 
like
 
sudden
 
braking
 
and
 
rapid
 
acceleration.
 
This
 
solution
 
targets
 
transport
 
fleets
 
in
 
North
 
America.

Metadata:
  source: 1._concise_overview_of_rapidise_-_dashcams.pdf
  product: dashcam
  title: Concise overview of Rapidise
  page: 0
  producer: Skia/PDF m142 Google Docs Renderer
  content_type: capability_pdf
  total_pages: 2
  creationdate: 
  creator: PyPDF
  page_label: 1
-----------------------------

--- Chunk 2 (Score: 142.5550) ---
Content:
expertise
 
in
 
embedded
 
hardware,
 
mechanical
 
design,
 
and
 
camera
 
modules.
 1.  Technical  Stack  (Processors,  Sensors,  and  Cameras)  Rapidise  utilizes  Qualcomm  processors  and  their  proprietary  RISE  platforms  for  automotive  
solutions.
 •  Processors/Platforms:      ◦  Qualcomm  QCS5430  utilizing  the  RISE  X1  Platform  (8  Core  CPU,  3.5  TOPS  NPU)  for  Dual  
Camera
 
Dashcams.
     ◦  Qualcomm  SM6225  utilizing  the  RISE  Y1  Platform  (8  Core  CPU,  2  TOPS  NPU)  for  Dual  
DashCams.
     ◦  Qualcomm  QCM6125  or  SC668S-WF  (associated  with  RISE  C1  Platform)  for  DashCam  +  
LTE
 
Edge
 
AI
 
Box
 
solutions.
 •  Cameras  and  Sensors:      ◦  Dashcam  solutions  frequently  incorporate  a  compact  2-camera  unit  for  front  and  in-cabin  
views.

Metadata:
  creator: PyPDF
  source: 2._end-to-end_capabilities_-_dashcam.pdf
  product: dashcam
  producer: Skia/PDF m142 Google Docs Renderer
  title: End-to-End capabilities for dashcam
  total_pages: 3
  creationdate: 
  page: 0
  content_type: capability_pdf
  page_label: 1
-----------------------------

--- Chunk 3 (Score: 146.2113) ---
Content:
Rapidise  operates  as  an  Original  Design  Manufacturer  (ODM)  leveraging  its  12+  years  of  design  and  
25+
 
years
 
of
 
manufacturing
 
experience
 
to
 
deliver
 
complex
 
dashcam
 
and
 
vehicle
 
telematics
 
solutions.
 
The
 
following
 
case
 
studies
 
summarize
 
three
 
distinct
 
dashcam
 
projects
 
based
 
on
 
Rapidise’s
 
proprietary
 
RISE
 
platforms.
 --------------------------------------------------------------------------------  Summarized  Dashcam  Case  Studies  1.  LTE  Edge  AI  Box  (Emergency  Call  System)  This  project  represents  a  high-volume  engagement  focused  specifically  on  vehicle  safety  and  
compliance,
 
targeting
 
the
 
rigorous
 
Japanese
 
market.
 Element  Details  and  Outcomes  
Objective  To  enhance  vehicle  safety  by  developing  an  advanced  emergency  call  system  designed  to  automatically  connect  to  an  emergency  call  center  upon  accident  detection.

Metadata:
  product: dashcam
  title: 2-3 case studies of Rapidise's dashcam
  total_pages: 3
  page_label: 1
  creator: PyPDF
  source: 5._2-3_case_studies_-_dashcam.pdf
  content_type: capability_pdf
  page: 0
  creationdate: 
  producer: Skia/PDF m142 Google Docs Renderer
-----------------------------
