#!/usr/bin/env python3
"""
Quick Performance Test for Local Development
Tests individual components of the pipeline for optimization
"""

import time
import sys
import os
import gc
from typing import Dict, List
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_component_timing():
    """Test timing of individual components"""
    print("🔧 Testing Individual Components...")
    print("=" * 50)
    
    # Import and test PDF extraction
    print("📄 Testing PDF Extraction...")
    start_time = time.time()
    
    try:
        from src.app import extract_text_from_pdf, download_and_extract_text
        
        # Test URL download and extraction
        test_url = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
        
        extraction_start = time.time()
        text = download_and_extract_text(test_url)
        extraction_time = time.time() - extraction_start
        
        print(f"✅ PDF Extraction: {extraction_time:.2f}s")
        print(f"   Text length: {len(text):,} characters")
        
    except Exception as e:
        print(f"❌ PDF Extraction failed: {e}")
        return
    
    # Test embedding creation
    print("\n🧠 Testing Embedding Creation...")
    try:
        from src.app import create_document_embeddings
        
        embedding_start = time.time()
        chunks, embeddings, index, model = create_document_embeddings(text)
        embedding_time = time.time() - embedding_start
        
        print(f"✅ Embedding Creation: {embedding_time:.2f}s")
        print(f"   Chunks created: {len(chunks)}")
        print(f"   Embeddings shape: {embeddings.shape}")
        
    except Exception as e:
        print(f"❌ Embedding Creation failed: {e}")
        return
    
    # Test question answering
    print("\n💬 Testing Question Answering...")
    test_questions = [
        "What is the grace period for premium payment?",
        "What is the waiting period for pre-existing diseases?",
        "Does this policy cover maternity expenses?"
    ]
    
    try:
        from src.app import generate_response
        
        qa_times = []
        for i, question in enumerate(test_questions):
            qa_start = time.time()
            response = generate_response(question, chunks, embeddings, index, model)
            qa_time = time.time() - qa_start
            qa_times.append(qa_time)
            
            # Parse response
            try:
                response_data = json.loads(response)
                answer = response_data.get('justification', response)[:100] + "..."
            except:
                answer = response[:100] + "..."
            
            print(f"✅ Question {i+1}: {qa_time:.2f}s")
            print(f"   Q: {question}")
            print(f"   A: {answer}")
            print()
        
        avg_qa_time = sum(qa_times) / len(qa_times)
        print(f"📊 Average Q&A Time: {avg_qa_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Question Answering failed: {e}")
        return
    
    # Memory cleanup
    gc.collect()
    
    # Summary
    total_time = time.time() - start_time
    print("\n" + "=" * 50)
    print("📊 COMPONENT TIMING SUMMARY")
    print("=" * 50)
    print(f"📄 PDF Extraction:     {extraction_time:.2f}s")
    print(f"🧠 Embedding Creation: {embedding_time:.2f}s")
    print(f"💬 Avg Q&A Time:       {avg_qa_time:.2f}s")
    print(f"⏱️  Total Time:         {total_time:.2f}s")
    print()
    print("🎯 Performance Breakdown:")
    print(f"   PDF Extraction: {(extraction_time/total_time)*100:.1f}%")
    print(f"   Embedding:      {(embedding_time/total_time)*100:.1f}%")
    print(f"   Q&A (avg):      {(avg_qa_time/total_time)*100:.1f}%")

def test_memory_usage():
    """Test memory usage of components"""
    print("\n🧠 Testing Memory Usage...")
    print("=" * 50)
    
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        def get_memory_mb():
            return process.memory_info().rss / 1024 / 1024
        
        initial_memory = get_memory_mb()
        print(f"Initial Memory: {initial_memory:.1f} MB")
        
        # Test model loading
        print("\n📚 Loading Models...")
        from src.app import get_sentence_transformer, get_ner_pipeline
        
        # Load sentence transformer
        model_start_memory = get_memory_mb()
        st_model = get_sentence_transformer()
        st_memory = get_memory_mb()
        print(f"SentenceTransformer: +{st_memory - model_start_memory:.1f} MB (Total: {st_memory:.1f} MB)")
        
        # Load NER pipeline
        ner_start_memory = get_memory_mb()
        ner_pipeline = get_ner_pipeline()
        ner_memory = get_memory_mb()
        print(f"NER Pipeline: +{ner_memory - ner_start_memory:.1f} MB (Total: {ner_memory:.1f} MB)")
        
        # Test document processing
        print("\n📄 Processing Document...")
        from src.app import download_and_extract_text, create_document_embeddings
        
        doc_start_memory = get_memory_mb()
        test_url = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
        text = download_and_extract_text(test_url)
        chunks, embeddings, index, model = create_document_embeddings(text)
        doc_memory = get_memory_mb()
        print(f"Document Processing: +{doc_memory - doc_start_memory:.1f} MB (Total: {doc_memory:.1f} MB)")
        
        print(f"\n📊 Memory Summary:")
        print(f"   Peak Memory Usage: {doc_memory:.1f} MB")
        print(f"   Memory Increase: +{doc_memory - initial_memory:.1f} MB")
        
        # Check if memory usage is within limits
        memory_limit_mb = 512  # Render free tier limit
        if doc_memory > memory_limit_mb:
            print(f"⚠️  WARNING: Memory usage ({doc_memory:.1f} MB) exceeds Render free tier limit ({memory_limit_mb} MB)")
        else:
            print(f"✅ Memory usage within Render free tier limit")
        
    except ImportError:
        print("❌ psutil not available. Install with: pip install psutil")
    except Exception as e:
        print(f"❌ Memory testing failed: {e}")

def test_api_locally():
    """Test the local API if it's running"""
    print("\n🌐 Testing Local API...")
    print("=" * 50)
    
    try:
        import requests
        
        # Test health endpoint
        try:
            response = requests.get("http://localhost:3000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Local API is running")
                health_data = response.json()
                print(f"   Status: {health_data.get('status')}")
                print(f"   Service: {health_data.get('service')}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("❌ Local API not running on localhost:3000")
            print("   Start with: python src/app.py")
        except Exception as e:
            print(f"❌ API test failed: {e}")
            
    except ImportError:
        print("❌ requests not available. Install with: pip install requests")

def main():
    print("🚀 Quick Performance Test for Intelligent Query API")
    print("=" * 60)
    
    # Test individual components
    test_component_timing()
    
    # Test memory usage
    test_memory_usage()
    
    # Test local API
    test_api_locally()
    
    print("\n✅ Performance testing completed!")
    print("\nTo run full API tests, use:")
    print("python test_performance.py --quick")

if __name__ == "__main__":
    main()
