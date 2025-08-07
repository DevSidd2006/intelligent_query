#!/usr/bin/env python3
"""
Simple Benchmark Script
Compares performance of different configurations
"""

import time
import json
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def benchmark_pdf_extraction():
    """Benchmark PDF extraction methods"""
    print("📄 Benchmarking PDF Extraction Methods...")
    
    test_url = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
    
    try:
        from src.app import download_and_extract_text
        
        # Test 3 times and average
        times = []
        for i in range(3):
            start = time.time()
            text = download_and_extract_text(test_url)
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  Run {i+1}: {elapsed:.2f}s")
        
        avg_time = sum(times) / len(times)
        print(f"📊 Average PDF Extraction: {avg_time:.2f}s")
        print(f"📄 Text extracted: {len(text):,} characters")
        return text, avg_time
        
    except Exception as e:
        print(f"❌ PDF extraction failed: {e}")
        return None, 0

def benchmark_embedding_models():
    """Benchmark different embedding model configurations"""
    print("\n🧠 Benchmarking Embedding Models...")
    
    # Get sample text
    text, _ = benchmark_pdf_extraction()
    if not text:
        return
    
    # Take a smaller sample for faster testing
    sample_text = text[:10000]  # First 10k characters
    
    from sentence_transformers import SentenceTransformer
    import gc
    
    models_to_test = [
        ("all-MiniLM-L6-v2", "Fast & Lightweight"),
        ("all-mpnet-base-v2", "Balanced"),
        # ("BAAI/bge-large-en-v1.5", "High Accuracy")  # Skip large model for quick test
    ]
    
    for model_name, description in models_to_test:
        print(f"\n  Testing {model_name} ({description})...")
        try:
            # Load model
            load_start = time.time()
            model = SentenceTransformer(model_name)
            load_time = time.time() - load_start
            
            # Create simple chunks
            chunks = [sample_text[i:i+500] for i in range(0, len(sample_text), 500)][:20]  # Max 20 chunks
            
            # Time encoding
            encode_start = time.time()
            embeddings = model.encode(chunks, show_progress_bar=False)
            encode_time = time.time() - encode_start
            
            print(f"    Load time: {load_time:.2f}s")
            print(f"    Encode time: {encode_time:.2f}s ({len(chunks)} chunks)")
            print(f"    Embedding dim: {embeddings.shape[1]}")
            
            # Cleanup
            del model, embeddings
            gc.collect()
            
        except Exception as e:
            print(f"    ❌ Failed: {e}")

def benchmark_question_answering():
    """Benchmark question answering with current setup"""
    print("\n💬 Benchmarking Question Answering...")
    
    try:
        # Use existing processed document from memory
        from src.app import download_and_extract_text, create_document_embeddings, generate_response
        
        test_url = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
        
        # Process document once
        print("  📄 Processing document...")
        process_start = time.time()
        text = download_and_extract_text(test_url)
        chunks, embeddings, index, model = create_document_embeddings(text)
        process_time = time.time() - process_start
        
        print(f"  ✅ Document processed in {process_time:.2f}s")
        print(f"     Chunks: {len(chunks)}")
        print(f"     Embeddings: {embeddings.shape}")
        
        # Test questions
        test_questions = [
            "What is the grace period for premium payment?",
            "What is the waiting period for pre-existing diseases?",
            "Does this policy cover maternity expenses?"
        ]
        
        print("\n  💬 Testing question answering...")
        qa_times = []
        
        for i, question in enumerate(test_questions):
            qa_start = time.time()
            response = generate_response(question, chunks, embeddings, index, model)
            qa_time = time.time() - qa_start
            qa_times.append(qa_time)
            
            try:
                response_data = json.loads(response)
                answer = response_data.get('justification', response)
                answer_preview = answer[:80] + "..." if len(answer) > 80 else answer
            except:
                answer_preview = response[:80] + "..."
            
            print(f"    Q{i+1}: {qa_time:.2f}s - {answer_preview}")
        
        avg_qa = sum(qa_times) / len(qa_times)
        total_time = process_time + avg_qa
        
        print(f"\n  📊 Q&A Summary:")
        print(f"     Document processing: {process_time:.2f}s")
        print(f"     Average Q&A time: {avg_qa:.2f}s")
        print(f"     Total time (1 doc + 1 Q): {total_time:.2f}s")
        
        return {
            "document_processing": process_time,
            "avg_qa_time": avg_qa,
            "total_time": total_time,
            "chunks": len(chunks)
        }
        
    except Exception as e:
        print(f"  ❌ Q&A benchmark failed: {e}")
        return None

def benchmark_full_pipeline():
    """Benchmark the complete pipeline end-to-end"""
    print("\n🚀 Full Pipeline Benchmark...")
    print("=" * 50)
    
    start_time = time.time()
    
    # Simulate the hackrx/run endpoint
    test_payload = {
        "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
        "questions": [
            "What is the grace period for premium payment?",
            "What is the waiting period for pre-existing diseases?",
            "Does this policy cover maternity expenses?",
            "What is the No Claim Discount offered?",
            "Are there any sub-limits on room rent for Plan A?"
        ]
    }
    
    try:
        from src.app import download_and_extract_text, create_document_embeddings, generate_response
        
        # Document processing
        doc_start = time.time()
        text = download_and_extract_text(test_payload["documents"])
        chunks, embeddings, index, model = create_document_embeddings(text)
        doc_time = time.time() - doc_start
        
        # Question answering
        qa_start = time.time()
        answers = []
        for question in test_payload["questions"]:
            response = generate_response(question, chunks, embeddings, index, model)
            try:
                result = json.loads(response)
                answer = result.get('justification', response)
            except:
                answer = response
            answers.append(answer)
        qa_time = time.time() - qa_start
        
        total_time = time.time() - start_time
        
        print(f"📄 Document Processing: {doc_time:.2f}s")
        print(f"💬 Q&A ({len(test_payload['questions'])} questions): {qa_time:.2f}s")
        print(f"⏱️  Total Pipeline Time: {total_time:.2f}s")
        print(f"📊 Average per question: {qa_time/len(test_payload['questions']):.2f}s")
        
        # Performance targets
        print(f"\n🎯 Performance Analysis:")
        if total_time < 60:
            print(f"✅ Excellent: Total time under 1 minute")
        elif total_time < 120:
            print(f"⚠️  Good: Total time under 2 minutes")
        else:
            print(f"❌ Slow: Total time over 2 minutes")
        
        if qa_time/len(test_payload['questions']) < 10:
            print(f"✅ Fast Q&A: Average under 10s per question")
        else:
            print(f"⚠️  Slow Q&A: Average over 10s per question")
        
        return {
            "document_time": doc_time,
            "qa_time": qa_time,
            "total_time": total_time,
            "questions_count": len(test_payload['questions']),
            "avg_per_question": qa_time/len(test_payload['questions']),
            "answers": answers
        }
        
    except Exception as e:
        print(f"❌ Pipeline benchmark failed: {e}")
        return None

def main():
    print("⚡ Quick Benchmark for Intelligent Query API")
    print("=" * 60)
    
    # Run benchmarks
    results = {}
    
    # 1. PDF Extraction
    text, pdf_time = benchmark_pdf_extraction()
    results['pdf_extraction'] = pdf_time
    
    # 2. Embedding models (if we have text)
    if text:
        benchmark_embedding_models()
    
    # 3. Question answering
    qa_results = benchmark_question_answering()
    if qa_results:
        results.update(qa_results)
    
    # 4. Full pipeline
    pipeline_results = benchmark_full_pipeline()
    if pipeline_results:
        results['pipeline'] = pipeline_results
    
    print("\n" + "=" * 60)
    print("📊 FINAL BENCHMARK SUMMARY")
    print("=" * 60)
    
    if pipeline_results:
        print(f"🚀 Complete Pipeline Performance:")
        print(f"   📄 Document Processing: {pipeline_results['document_time']:.1f}s")
        print(f"   💬 Q&A ({pipeline_results['questions_count']} questions): {pipeline_results['qa_time']:.1f}s")
        print(f"   ⏱️  Total Time: {pipeline_results['total_time']:.1f}s")
        print(f"   📊 Average per Question: {pipeline_results['avg_per_question']:.1f}s")
        
        # Deployment recommendations
        print(f"\n🎯 Deployment Recommendations:")
        if pipeline_results['total_time'] < 60:
            print(f"   ✅ Ready for production deployment")
            print(f"   ✅ Suitable for Railway.app (1GB RAM)")
        elif pipeline_results['total_time'] < 120:
            print(f"   ⚠️  Consider optimization for better UX")
            print(f"   ✅ Suitable for Railway.app (1GB RAM)")
        else:
            print(f"   ❌ Needs optimization before deployment")
            print(f"   ⚠️  May need more than 1GB RAM")
    
    print(f"\n✅ Benchmark completed!")

if __name__ == "__main__":
    main()
