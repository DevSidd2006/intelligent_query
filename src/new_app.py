import os
import logging
import gc
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from dotenv import load_dotenv

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

import pdfplumber
try:
    import fitz  # PyMuPDF for fast PDF extraction
    # Verify it's the correct PyMuPDF module
    if not hasattr(fitz, 'open'):
        raise ImportError("Wrong fitz module loaded")
except (ImportError, AttributeError):
    # Fallback: Try importing PyMuPDF directly
    try:
        import pymupdf as fitz
    except ImportError:
        # Final fallback: use pdfplumber only
        fitz = None
        logger.warning("PyMuPDF not available, will use pdfplumber only")

import requests
import tempfile
import mimetypes
from docx import Document
import email
import email.policy
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from transformers import pipeline
import json
import openai
import hashlib
import re
from typing import Dict, List, Tuple, Optional, Any
import threading

# Load environment variables
load_dotenv()

# Thread pool for async operations
THREAD_POOL = ThreadPoolExecutor(max_workers=4)

# Global model cache with thread safety
_model_cache = {
    'sentence_transformer': None,
    'ner_pipeline': None
}
_model_lock = threading.Lock()

# Optimized document cache with TTL and size limits
_document_cache = {}
_cache_timestamps = {}
MAX_CACHE_SIZE = 10  # Increased cache size
CACHE_TTL = 3600  # 1 hour TTL
_cache_lock = threading.Lock()

# Precompiled regex patterns for better performance
WHITESPACE_PATTERN = re.compile(r'\n\s*\n')
MULTIPLE_SPACES_PATTERN = re.compile(r' +')
SENTENCE_SPLIT_PATTERN = re.compile(r'(?<=[.!?])\s+')

def get_document_cache_key(url: str) -> str:
    """Generate cache key for document URL"""
    return hashlib.md5(url.encode()).hexdigest()

def cleanup_expired_cache():
    """Remove expired cache entries"""
    with _cache_lock:
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in _cache_timestamps.items()
            if current_time - timestamp > CACHE_TTL
        ]
        for key in expired_keys:
            _document_cache.pop(key, None)
            _cache_timestamps.pop(key, None)
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

def get_cached_document(url: str) -> Optional[Dict]:
    """Get document from cache if available and not expired"""
    cleanup_expired_cache()
    cache_key = get_document_cache_key(url)
    return _document_cache.get(cache_key)

def cache_document(url: str, chunks: List[str], embeddings: np.ndarray, index: faiss.Index, model: SentenceTransformer):
    """Cache document processing results with TTL"""
    cache_key = get_document_cache_key(url)
    
    with _cache_lock:
        # Implement LRU-style cache by removing oldest if at capacity
        if len(_document_cache) >= MAX_CACHE_SIZE:
            # Remove the oldest entry based on timestamp
            oldest_key = min(_cache_timestamps.keys(), key=_cache_timestamps.get)
            _document_cache.pop(oldest_key, None)
            _cache_timestamps.pop(oldest_key, None)
            logger.info(f"Removed oldest document from cache")
        
        _document_cache[cache_key] = {
            'chunks': chunks,
            'embeddings': embeddings, 
            'index': index,
            'model': model
        }
        _cache_timestamps[cache_key] = time.time()
        logger.info(f"Cached document processing results for {url[:50]}...")

@lru_cache(maxsize=1)
def get_sentence_transformer() -> SentenceTransformer:
    """Get cached sentence transformer model - thread-safe singleton"""
    with _model_lock:
        if _model_cache['sentence_transformer'] is None:
            logger.info("⚡ Loading optimized SentenceTransformer model (first time only)...")
            try:
                # Use the fastest model with good quality: all-MiniLM-L6-v2
                _model_cache['sentence_transformer'] = SentenceTransformer(
                    'all-MiniLM-L6-v2',
                    device='cpu'  # Explicitly use CPU for consistency
                )
                logger.info("✅ Loaded all-MiniLM-L6-v2 (fastest model)")
            except Exception as e:
                logger.warning(f"Failed to load all-MiniLM-L6-v2: {e}")
                try:
                    # Fallback to balanced model
                    _model_cache['sentence_transformer'] = SentenceTransformer('all-mpnet-base-v2')
                    logger.info("✅ Loaded all-mpnet-base-v2 (balanced speed/accuracy)")
                except Exception as e2:
                    logger.error(f"Failed to load backup model: {e2}")
                    raise e2
        
        return _model_cache['sentence_transformer']

@lru_cache(maxsize=1)
def get_ner_pipeline():
    """Get cached NER pipeline - thread-safe singleton"""
    with _model_lock:
        if _model_cache['ner_pipeline'] is None:
            logger.info("Loading NER pipeline (first time only)...")
            _model_cache['ner_pipeline'] = pipeline(
                "ner", 
                model="dslim/bert-base-NER",
                device=-1  # Force CPU usage for consistency
            )
            logger.info("NER pipeline loaded and cached")
        return _model_cache['ner_pipeline']

@lru_cache(maxsize=1)
def get_api_key() -> str:
    """Get API key with caching"""
    # Primary key name (preferred)
    api_key = os.getenv('OPENROUTER_API_KEY')
    if api_key:
        return api_key
    
    # Fallback key name for backward compatibility
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        logger.warning("Using OPENAI_API_KEY - Consider renaming to OPENROUTER_API_KEY")
        return api_key
    
    # No key found
    raise ValueError("❌ No API key found! Please set OPENROUTER_API_KEY in your .env file")

def clean_text_fast(text: str) -> str:
    """Optimized text cleaning using precompiled regex"""
    text = text.replace("iviviv", "").replace("Air Ambulasce", "Air Ambulance")
    text = WHITESPACE_PATTERN.sub('\n\n', text)
    text = MULTIPLE_SPACES_PATTERN.sub(' ', text)
    return text

# Step 1: Document Ingestion (Optimized)
def extract_text_from_pdf_fast(pdf_path: str) -> str:
    """Fast PDF text extraction using PyMuPDF with optimizations"""
    try:
        logger.info(f"⚡ Starting fast PDF extraction: {pdf_path}")
        
        # Open PDF with PyMuPDF
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # Use list comprehension for better performance
        page_texts = []
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            if page_text.strip():  # Only add non-empty pages
                page_texts.append(page_text)
            
            # Progress indicator every 20 pages for less logging overhead
            if (page_num + 1) % 20 == 0 or page_num == total_pages - 1:
                logger.info(f"Processed {page_num + 1}/{total_pages} pages")
        
        doc.close()
        
        # Join and clean text
        text = "\n".join(page_texts)
        text = clean_text_fast(text)
        
        logger.info(f"✅ Fast extraction completed! Extracted {len(text)} characters from {total_pages} pages")
        return text
        
    except Exception as e:
        logger.error(f"❌ PyMuPDF extraction failed: {str(e)}")
        return extract_text_from_pdf_fallback(pdf_path)

def extract_text_from_pdf_fallback(pdf_path: str) -> str:
    """Fallback PDF extraction using pdfplumber"""
    try:
        logger.info("Using pdfplumber for PDF extraction (fallback)")
        page_texts = []
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"Processing {total_pages} pages with pdfplumber...")
            
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    page_texts.append(page_text)
                
                # Progress indicator every 20 pages
                if page_num % 20 == 0 or page_num == total_pages:
                    logger.info(f"Processed {page_num}/{total_pages} pages")
        
        # Join and clean text
        text = "\n".join(page_texts)
        text = clean_text_fast(text)
        
        logger.info(f"✅ Fallback extraction completed! Extracted {len(text)} characters")
        return text
        
    except Exception as e:
        logger.error(f"❌ Both PyMuPDF and pdfplumber extraction failed: {str(e)}")
        raise e

def extract_text_from_pdf(pdf_path: str) -> str:
    """Main PDF extraction function - uses fast PyMuPDF first, then fallback"""
    if fitz is not None:
        return extract_text_from_pdf_fast(pdf_path)
    else:
        logger.warning("PyMuPDF not available, using pdfplumber")
        return extract_text_from_pdf_fallback(pdf_path)

# DOCX extraction (optimized)
def extract_text_from_docx(docx_path: str) -> str:
    """Optimized DOCX text extraction"""
    doc = Document(docx_path)
    # Use list comprehension for better performance
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(paragraphs)

# Email extraction (.eml)
def extract_text_from_email(email_path: str) -> str:
    """Optimized email text extraction"""
    with open(email_path, 'rb') as f:
        msg = email.message_from_binary_file(f, policy=email.policy.default)
    
    body = msg.get_body(preferencelist=('plain'))
    return body.get_content() if body else ''

# Download file from URL and auto-detect type (with connection pooling)
def download_and_extract_text(url: str) -> str:
    """Optimized file download and extraction"""
    # Use session for connection pooling
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (compatible; PDF-QA-Bot/1.0)'
    })
    
    try:
        response = session.get(url, timeout=30)  # Add timeout
        if response.status_code != 200:
            raise Exception(f"Failed to download file: {url} (Status: {response.status_code})")
        
        # Guess file type from headers or URL
        content_type = response.headers.get('content-type', '')
        ext = mimetypes.guess_extension(content_type) or ('.' + url.split('.')[-1].lower())
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
        
        try:
            # Dispatch to correct extractor
            if ext in ['.pdf', 'pdf']:
                return extract_text_from_pdf(tmp_path)
            elif ext in ['.docx', 'docx']:
                return extract_text_from_docx(tmp_path)
            elif ext in ['.eml', 'msg']:
                return extract_text_from_email(tmp_path)
            else:
                raise Exception(f"Unsupported file type: {ext}")
        finally:
            # Cleanup temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
    finally:
        session.close()

# Step 2: Text Chunking and Embedding (Heavily Optimized)
def create_optimized_chunks(text: str) -> List[str]:
    """Optimized chunking strategy for speed and accuracy"""
    chunks = []
    
    # Split by double newlines first (paragraphs)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    
    for paragraph in paragraphs:
        # Optimal chunk size: 400-500 characters for speed
        if len(paragraph) <= 500:
            if len(paragraph) >= 80:  # Filter very short chunks
                chunks.append(paragraph)
        else:
            # Split longer paragraphs by sentences using precompiled regex
            sentences = SENTENCE_SPLIT_PATTERN.split(paragraph)
            current_chunk = ""
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                # Add sentence if it fits in current chunk
                test_chunk = current_chunk + (" " if current_chunk else "") + sentence
                if len(test_chunk) <= 500:
                    current_chunk = test_chunk
                else:
                    # Save current chunk and start new one
                    if current_chunk and len(current_chunk) >= 80:
                        chunks.append(current_chunk)
                    current_chunk = sentence
            
            # Don't forget the last chunk
            if current_chunk and len(current_chunk) >= 80:
                chunks.append(current_chunk)
    
    logger.info(f"📊 Created {len(chunks)} optimized chunks")
    return chunks

def create_document_embeddings(text: str) -> Tuple[List[str], np.ndarray, faiss.Index, SentenceTransformer]:
    """Create optimized document embeddings with maximum speed"""
    model = get_sentence_transformer()
    
    logger.info("🚀 Starting optimized chunking and embedding process...")
    
    # Fast chunking
    chunks = create_optimized_chunks(text)
    avg_chunk_size = sum(len(c) for c in chunks) // len(chunks) if chunks else 0
    logger.info(f"💡 Average chunk size: {avg_chunk_size} characters")
    
    # Optimized embedding with larger batches for speed
    logger.info("🔮 Encoding chunks with fast model...")
    
    # Use larger batch size for better GPU utilization
    batch_size = 64  # Increased batch size
    all_embeddings = []
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        # Disable progress bar for speed, normalize embeddings for better similarity
        batch_embeddings = model.encode(
            batch, 
            show_progress_bar=False,
            normalize_embeddings=True,  # Better for similarity search
            convert_to_numpy=True
        )
        all_embeddings.append(batch_embeddings)
        
        # Less frequent progress updates
        processed = min(i + batch_size, len(chunks))
        if processed % 128 == 0 or processed == len(chunks):
            logger.info(f"Encoded {processed}/{len(chunks)} chunks")
    
    # Combine all embeddings
    embeddings = np.vstack(all_embeddings) if len(all_embeddings) > 1 else all_embeddings[0]
    
    # Create optimized FAISS index with better performance
    logger.info("🗂️ Creating optimized FAISS index...")
    dimension = embeddings.shape[1]
    
    # Use IndexFlatIP for cosine similarity (since we normalized embeddings)
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings.astype('float32'))
    
    logger.info(f"✅ Embedding process completed! {len(chunks)} chunks indexed")
    
    return chunks, embeddings, index, model

@lru_cache(maxsize=128)
def estimate_tokens_cached(text_hash: str, char_count: int, word_count: int) -> int:
    """Cached token estimation for repeated text patterns"""
    # More accurate estimation based on character and word counts
    base_tokens = char_count / 3.8  # Slightly more accurate ratio
    word_adjustment = word_count * 0.1  # Small adjustment for word boundaries
    return int(base_tokens + word_adjustment)

def estimate_tokens(text: str) -> int:
    """Fast token estimation with caching"""
    char_count = len(text)
    word_count = len(text.split())
    text_hash = str(hash(text[:100]))  # Use first 100 chars for hash
    
    return estimate_tokens_cached(text_hash, char_count, word_count)

# Step 3: Query Parsing (Optimized)
@lru_cache(maxsize=256)
def parse_query_cached(query: str) -> Dict[str, Optional[str]]:
    """Cached query parsing for repeated queries"""
    parsed = {"care_type": None, "beneficiary": None, "period": None}
    
    query_lower = query.lower()
    
    # Fast string matching instead of NER for common patterns
    if "mother" in query_lower:
        parsed["beneficiary"] = "mother"
    if "preventive care" in query_lower:
        parsed["care_type"] = "routine preventive care"
    if "just delivered" in query_lower or "postpartum" in query_lower:
        parsed["period"] = "postpartum"
    
    return parsed

def parse_query(query: str) -> Dict[str, Optional[str]]:
    """Fast query parsing with caching"""
    return parse_query_cached(query)

# Step 4: Semantic Retrieval (Optimized)
def retrieve_relevant_chunks(query: str, chunks: List[str], embeddings: np.ndarray, 
                           index: faiss.Index, model: SentenceTransformer, k: int = 3) -> List[str]:
    """Optimized semantic retrieval"""
    # Encode query with same settings as chunks
    query_embedding = model.encode([query], normalize_embeddings=True, convert_to_numpy=True)
    
    # Search for similar chunks
    scores, indices = index.search(query_embedding.astype('float32'), k)
    
    # Return relevant chunks with size limits for token management
    relevant_chunks = []
    for i in indices[0]:
        if i < len(chunks):  # Safety check
            chunk = chunks[i]
            # Limit chunk size to prevent token overflow
            if len(chunk) > 400:
                chunk = chunk[:400] + "..."
            relevant_chunks.append(chunk)
    
    return relevant_chunks

# Step 5: Decision and Output Generation (Async Optimized)
async def generate_response_async(query: str, chunks: List[str], embeddings: np.ndarray = None, 
                                index: faiss.Index = None, model_st: SentenceTransformer = None, 
                                llm_model: str = "anthropic/claude-sonnet-4") -> str:
    """Async response generation for better concurrency"""
    
    def _sync_generate():
        return generate_response(query, chunks, embeddings, index, model_st, llm_model)
    
    # Run the sync function in thread pool
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(THREAD_POOL, _sync_generate)

def generate_response(query: str, chunks: List[str], embeddings: np.ndarray = None, 
                     index: faiss.Index = None, model_st: SentenceTransformer = None, 
                     llm_model: str = "anthropic/claude-sonnet-4") -> str:
    """Optimized response generation"""
    from openai import OpenAI
    
    try:
        api_key = get_api_key()
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=15.0  # Add timeout for faster failures
        )
        
    except ValueError as e:
        logger.error(f"API Key Error: {e}")
        return json.dumps({
            "justification": "❌ API key not configured. Please set OPENROUTER_API_KEY in your .env file."
        })
    except Exception as e:
        logger.error(f"Client initialization error: {e}")
        return json.dumps({
            "justification": f"❌ Failed to initialize AI client: {str(e)}"
        })
    
    # Fast query parsing and retrieval
    parsed_query = parse_query(query)
    relevant_chunks = retrieve_relevant_chunks(query, chunks, embeddings, index, model_st)
    # Highly specific, concise, number-focused insurance policy prompt
    prompt = f"""You are an expert insurance policy analyst. Provide concise yet comprehensive answers with maximum numerical precision.

CRITICAL REQUIREMENTS:
- For yes/no questions: Start with 'Yes,' or 'No,' then provide essential explanation
- Include ALL key numbers: exact days, months, years, percentages, amounts
- State important plan variations (Plan A vs Plan B vs Plan C) with key differences only
- Include essential age limits, waiting periods, and main coverage conditions
- Quote main benefit amounts, caps, and limits with numbers
- Mention only critical exceptions and key conditions
- Keep responses concise-medium length (50 words max) but include all essential details

ANSWER FORMAT:
- Yes/No questions: 'Yes, [key explanation with specifics]' or 'No, [key explanation with specifics]'
- Other questions: Direct answer with essential numerical details
- Focus on: main timeframes, key percentages, important plan differences, primary limits
- Include only the most relevant conditions and exceptions
- Avoid excessive bullet points and sub-details

IMPORTANT:
- Do NOT include phrases like 'according to the document', 'as per the policy', or any reference to the source. Only give the direct answer.

Document Context:
{chr(10).join([f"{i+1}. {chunk}" for i, chunk in enumerate(relevant_chunks)])}

Question: {query}

Concise answer with essential details and maximum numerical accuracy:"""
    # Estimate token count using improved function
    estimated_tokens = estimate_tokens(prompt)
    logger.info(f"Estimated prompt tokens: {estimated_tokens}")
    # If prompt is too long, use only the first chunk
    if estimated_tokens > 8000:
        logger.warning("Prompt too long, using only first chunk")
        relevant_chunks = relevant_chunks[:1]
        # Recreate shorter prompt
        prompt = f"""Answer this insurance policy question directly and naturally.

Question: {query}

Policy information: {relevant_chunks[0][:300]}...

Provide a direct, factual answer. Include specific details when mentioned.

Format: {{"justification": "Your direct answer presenting the policy information as facts"}}"""

    try:
        # Optimized API call with lower token limits for speed
        response = client.chat.completions.create(
            model=llm_model,
            messages=[
                {
                    "role": "system", 
                    "content": "You are an insurance expert. Provide direct, factual answers. Return JSON format only."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,  # Lower token limit for faster response
            temperature=0.3,  # Lower temperature for more consistent responses
            extra_headers={
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "PDF Q&A System"
            }
        )
        
        response_text = response.choices[0].message.content
        
        # Fast JSON parsing
        try:
            # Clean up common markdown artifacts quickly
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                if end > start:
                    response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                if end > start:
                    response_text = response_text[start:end].strip()
            
            # Try to parse JSON
            parsed_response = json.loads(response_text)
            return json.dumps(parsed_response, separators=(',', ':'))  # Compact JSON
        except json.JSONDecodeError:
            # Fast fallback
            return json.dumps({"justification": response_text}, separators=(',', ':'))
            
    except Exception as e:
        logger.error(f"API call failed: {str(e)}")
        return json.dumps({"justification": f"Error: {str(e)}"}, separators=(',', ':'))

# Interactive Q&A Function (Optimized)
async def interactive_qa_session_async(chunks: List[str], embeddings: np.ndarray, 
                                     index: faiss.Index, model_st: SentenceTransformer):
    """Async interactive Q&A session"""
    logger.info("Starting interactive Q&A session")
    print("=" * 60)
    print("📄 PDF Question-Answer System (Optimized)")
    print("=" * 60)
    print("You can now ask questions about the PDF document!")
    print("Type 'quit', 'exit', or 'q' to stop.")
    print("-" * 60)
    
    while True:
        try:
            # Get user input (blocking, but that's okay for CLI)
            user_query = input("\n🤔 Ask your question: ").strip()
            
            # Check for exit commands
            if user_query.lower() in ['quit', 'exit', 'q', '']:
                print("\n👋 Thank you for using the PDF Q&A system!")
                break
            
            # Process the query asynchronously
            print("\n🔍 Processing your question...")
            start_time = time.time()
            
            response = await generate_response_async(user_query, chunks, embeddings, index, model_st)
            
            processing_time = time.time() - start_time
            
            # Display the response
            print("\n📋 Response:")
            print("-" * 40)
            
            # Parse and display JSON response
            try:
                response_data = json.loads(response)
                print(f"Answer: {response_data.get('justification', 'N/A')}")
                print(f"⏱️ Processing time: {processing_time:.2f}s")
            except:
                print(response)
                print(f"⏱️ Processing time: {processing_time:.2f}s")
            
            print("-" * 40)
            
        except KeyboardInterrupt:
            logger.info("Session ended by user")
            print("\n\n👋 Session ended by user. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error during Q&A session: {str(e)}")
            print(f"\n❌ An error occurred: {str(e)}")
            print("Please try asking your question again.")

# FastAPI Implementation (Heavily Optimized)
from fastapi import FastAPI, UploadFile, File, Form, Request, Header, Body, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from typing import List, Optional
from collections import defaultdict
import asyncio

# Advanced rate limiting with sliding window
class SlidingWindowRateLimit:
    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip] 
            if now - req_time < self.window_seconds
        ]
        
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        
        self.requests[client_ip].append(now)
        return True

rate_limiter = SlidingWindowRateLimit(max_requests=20, window_seconds=60)

app = FastAPI(
    title="Optimized PDF Q&A System",
    description="High-performance document question-answering system",
    version="2.0.0"
)

# Preload models at startup
@app.on_event("startup")
async def startup_event():
    """Preload all models and setup optimizations"""
    logger.info("Starting optimized PDF Q&A system...")
    logger.info("Preloading ML models at startup...")
    
    try:
        # Preload models in parallel using asyncio.to_thread (returns coroutine)
        await asyncio.gather(
            asyncio.to_thread(get_sentence_transformer),
            asyncio.to_thread(get_ner_pipeline),
        )
        # Clear any startup cache
        gc.collect()
        logger.info("All models preloaded successfully!")
        logger.info("System ready for high-performance processing!")
    except Exception as e:
        logger.error(f"Error preloading models: {e}")

def verify_bearer_token(authorization: str) -> Tuple[bool, Optional[str]]:
    """Fast bearer token verification"""
    required_token = os.getenv('HACKRX_BEARER_TOKEN')
    if not required_token:
        return False, "HACKRX_BEARER_TOKEN environment variable is not configured."
    
    if not authorization or not authorization.startswith('Bearer '):
        return False, "Missing or invalid Authorization header."
    
    token = authorization[7:].strip()  # Faster than split
    if token != required_token:
        return False, "Invalid Bearer token."
    return True, None

# Optimized health check
@app.get("/health")
async def health_check():
    """Optimized health check endpoint"""
    try:
        api_key = get_api_key()
        return {
            "status": "healthy",
            "service": "Optimized PDF Q&A System",
            "version": "2.0.0",
            "api_configured": bool(api_key),
            "cache_size": len(_document_cache),
            "uptime": time.time()
        }
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e)
        }, status_code=503)

@app.post("/hackrx/run")
async def hackrx_run(
    request: Request,
    authorization: str = Header(None),
    documents: Optional[str] = Body(None),
    questions: Optional[List[str]] = Body(None)
):
    """Optimized main processing endpoint"""
    start_time = time.time()
    
    # Fast rate limiting check
    client_ip = request.client.host
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
    
    # Fast bearer token verification
    ok, err = verify_bearer_token(authorization)
    if not ok:
        logger.warning(f"Bearer token verification failed: {err}")
        return JSONResponse({"success": False, "error": err}, status_code=401)

    # Quick input validation
    if not documents:
        return JSONResponse({
            "success": False, 
            "error": "Missing 'documents' parameter. Please provide a URL to the document."
        }, status_code=400)
    
    if not questions or not isinstance(questions, list) or len(questions) == 0:
        return JSONResponse({
            "success": False, 
            "error": "Questions must be a non-empty list."
        }, status_code=400)
    
    # Fast URL validation
    if not documents.startswith(('http://', 'https://')):
        return JSONResponse({
            "success": False, 
            "error": "Documents parameter must be a valid URL."
        }, status_code=400)

    try:
        logger.info(f"Processing {len(questions)} questions for document: {documents[:60]}...")
        
        # Check cache first (fastest path)
        cached_doc = get_cached_document(documents)
        if cached_doc:
            logger.info("Using cached document processing results")
            chunks = cached_doc['chunks']
            embeddings = cached_doc['embeddings']
            index = cached_doc['index']
            model_st = cached_doc['model']
            cache_hit = True
        else:
            cache_hit = False
            logger.info("Processing new document...")
            
            # Download and process document asynchronously
            def process_document():
                text = download_and_extract_text(documents)
                return create_document_embeddings(text)
            
            # Run document processing in thread pool using asyncio.to_thread (returns coroutine)
            chunks, embeddings, index, model_st = await asyncio.to_thread(process_document)
            
            logger.info(f"Document processed: {len(chunks)} chunks created")
            
            # Cache the results asynchronously (don't wait)
            asyncio.create_task(asyncio.to_thread(cache_document, documents, chunks, embeddings, index, model_st))

        # Process questions concurrently for maximum speed
        async def process_question(question: str, q_idx: int) -> str:
            try:
                logger.info(f"Processing Q{q_idx+1}: {question[:50]}...")
                response = await generate_response_async(
                    question, chunks, embeddings, index, model_st
                )
                # Extract answer from JSON response
                try:
                    result = json.loads(response)
                    # If justification is present and is a string, return it
                    justification = result.get('justification', None)
                    if justification and isinstance(justification, str):
                        return justification
                    # If justification is not present, try to return the whole result as a string
                    if isinstance(result, str):
                        return result
                    # If result is a dict, join all values as a string
                    if isinstance(result, dict):
                        return ' '.join(str(v) for v in result.values())
                    return str(result)
                except json.JSONDecodeError:
                    # If not JSON, just return the raw response string
                    return response
            except Exception as e:
                logger.error(f"Error processing question {q_idx+1}: {str(e)}")
                return f"Error processing question: {str(e)}"

        # Process all questions concurrently with semaphore for resource control
        semaphore = asyncio.Semaphore(4)  # Limit concurrent API calls
        
        async def process_with_semaphore(q, q_idx):
            async with semaphore:
                return await process_question(q, q_idx)
        # Execute all questions in parallel
        answers = await asyncio.gather(
            *[process_with_semaphore(q, i) for i, q in enumerate(questions)],
            return_exceptions=True
        )
        
        # Handle any exceptions in results
        final_answers = []
        for i, answer in enumerate(answers):
            if isinstance(answer, Exception):
                logger.error(f"Question {i+1} failed: {str(answer)}")
                final_answers.append(f"Error: {str(answer)}")
            else:
                final_answers.append(answer)

        # Calculate performance metrics
        total_time = time.time() - start_time
        avg_time_per_question = total_time / len(questions)
        
        logger.info(f"Successfully processed {len(questions)} questions in {total_time:.2f}s")
        logger.info(f"Average time per question: {avg_time_per_question:.2f}s")
        logger.info(f"Cache hit: {cache_hit}")
        
        # Cleanup memory if not using cache
        if not cache_hit:
            # Force garbage collection for memory management
            gc.collect()
        
        # Return response in expected format
        return JSONResponse({
            "answers": final_answers
        })

    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"❌ Request failed after {total_time:.2f}s: {str(e)}")
        
        # Emergency cleanup
        gc.collect()
        
        return JSONResponse({
            "success": False, 
            "error": str(e)
        }, status_code=500)

# Additional utility endpoints for monitoring and optimization
@app.get("/stats")
async def get_stats():
    """Get system performance statistics"""
    return {
        "cache_size": len(_document_cache),
        "cache_entries": list(_cache_timestamps.keys()),
        "model_loaded": _model_cache['sentence_transformer'] is not None,
        "ner_loaded": _model_cache['ner_pipeline'] is not None,
        "memory_info": {
            "cache_memory_mb": len(_document_cache) * 50,  # Rough estimate
        }
    }

@app.post("/clear-cache")
async def clear_cache(authorization: str = Header(None)):
    """Clear document cache (admin endpoint)"""
    ok, err = verify_bearer_token(authorization)
    if not ok:
        return JSONResponse({"error": err}, status_code=401)
    
    with _cache_lock:
        cache_count = len(_document_cache)
        _document_cache.clear()
        _cache_timestamps.clear()
    
    gc.collect()
    
    return {
        "message": f"Cleared {cache_count} cached documents",
        "cache_size": len(_document_cache)
    }

# CLI Interface (Optimized)
async def main_cli():
    """Optimized CLI interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python script.py <document_url>")
        return
    
    document_url = sys.argv[1]
    
    try:
        logger.info("Starting CLI PDF Q&A System...")
        
        # Process document
        print("📥 Downloading and processing document...")
        start_time = time.time()
        
        text = download_and_extract_text(document_url)
        chunks, embeddings, index, model_st = create_document_embeddings(text)
        
        setup_time = time.time() - start_time
        print(f"✅ Document ready in {setup_time:.2f}s ({len(chunks)} chunks)")
        
        # Start interactive session
        await interactive_qa_session_async(chunks, embeddings, index, model_st)
        
    except Exception as e:
        logger.error(f"CLI error: {str(e)}")
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    import sys
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Verify API key is configured
        get_api_key()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        sys.exit(1)
    
    # Check if running as CLI or server
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        # CLI mode
        asyncio.run(main_cli())
    else:
        # Server mode
        port = int(os.getenv('PORT', 2000))
        host = os.getenv('HOST', '0.0.0.0')
        uvicorn_config = {
            "host": host,
            "port": port,
            "workers": 1,
            "log_level": "info",
            "access_log": False,
        }
        # Try to use uvloop for better performance
        try:
            import uvloop
            uvicorn_config["loop"] = "uvloop"
        except ImportError:
            pass
        # Try to use httptools for better performance
        try:
            import httptools
            uvicorn_config["http"] = "httptools"
        except ImportError:
            pass
        logger.info(f"Starting optimized server on {host}:{port}")
        uvicorn.run(app, **uvicorn_config)