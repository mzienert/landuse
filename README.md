La Plata County Code LLM Knowledge Base Project
Project Overview
This project aims to create a retrieval-augmented generation (RAG) system using the La Plata County Code as a knowledge base for an LLM. The code is scraped from the public online viewer, processed into chunks, vectorized, stored in a vector database, and integrated with an LLM for querying. The end goal is a private POC with a chatbot frontend to demonstrate utility, which we plan to present to La Plata County for potential collaboration or official use.
Key objectives:

Provide accurate, searchable access to county ordinances via natural language queries (e.g., "What are zoning rules in Animas Valley?").
Ensure legality and ethics: Use public data, no public redistribution, add disclaimers for non-official advice.
Low-cost POC using AWS free tier where possible.

Components Needed
The system consists of the following components:

Scraper: Python script using Selenium and BeautifulSoup to extract all sections from the dynamic website. Outputs individual .txt files and a full_code.json.
Chunker: Splits extracted text into manageable chunks (e.g., 1000 chars with overlap) for embedding, using LangChain's RecursiveCharacterTextSplitter. Outputs chunks.json.
Vectorizer (Embeddings): Generates vectors from chunks using Amazon Bedrock (Titan Embeddings). Outputs vectors.json for storage.
Vector Database: PGVector extension on Amazon RDS PostgreSQL for storing and querying vectors. Free tier eligible.
RAG Integration: LangChain for retrieval from the DB and augmentation of LLM prompts. LLM via Bedrock (e.g., Claude).
Frontend: Next.js chatbot UI from Vercel templates, connected to the RAG backend.
Deployment: AWS for backend (S3 for files, RDS for DB, Lambda/EC2 for queries); Vercel for frontend (free tier).

Dependencies: Python (Selenium, BeautifulSoup, LangChain, boto3), AWS services (Bedrock, RDS, S3).
Research on Templates
We evaluated two Vercel AI templates for the frontend:

AI SDK RAG Template:

Focus: Basic RAG chatbot with chunking, embeddings, and retrieval.
Stack: Next.js, Vercel AI SDK, Drizzle ORM, PostgreSQL (compatible with PGVector).
Pros: Simple setup, serverless, good for quick POC.
Cons: Less flexible for custom chains/agents; requires more work to integrate LangChain and Bedrock (defaults to OpenAI).
Suitability: Good but limited beyond basic RAG.


LangChain Starter Template:

Focus: Broader AI app with RAG, chat, agents, and retrieval examples.
Stack: Next.js, LangChain.js, LangGraph.js, Vercel AI SDK; supports custom vector stores (e.g., PGVector).
Pros: Native LangChain integration aligns with our backend; easy to swap DB/LLM; extensible for agents; polished UI with citations.
Cons: Slightly more scope than needed (ignore extras); defaults to Supabase/OpenAI but swap-friendly.
Suitability: Better overall—faster integration, future-proof.



Conclusion: Use LangChain Starter for better alignment and features. Integration: Swap vector store to PGVector, LLM/embeddings to Bedrock in API routes.
Current Stage

Scraper: Functional but encountering session errors during long runs (e.g., InvalidSessionIdException). We've added driver restarts and checkpointing to resume. ~1298 sections identified; partial extraction complete (files with content like section_1.txt).
Chunking/Vectorization/DB: Ready but waiting for full scrape output. POC code prepared for AWS.
RAG/Frontend: Code snippets ready; frontend template selected but not deployed yet.
Progress: ~70% (scraping in progress; troubleshooting ongoing). Legality confirmed as public data use.

TODO Items

Complete Scraper Run: Remove limits, let it finish extracting all sections (monitor for errors, resume from checkpoints).
Verify Extraction: Check full_code.json for completeness (all 1298 entries with content).
Chunk Text: Run chunk_la_plata_code.py on full_code.json to generate chunks.json.
Setup AWS Resources: Create S3 bucket, RDS PGVector instance (run CREATE EXTENSION vector;), upload chunks.json.
Vectorize and Load DB: Run vectorize_load.py in AWS to embed and store in PGVector.
Test RAG: Run query test code; verify accurate responses with citations.
Deploy Frontend: Fork LangChain Starter on Vercel, configure API routes for PGVector/Bedrock.
Add Disclaimers: Include "Not official legal advice" in UI/responses.
Demo/Approach County: Build POC app, test queries, contact La Plata Planning Dept with demo.
Optimize/Clean: Sort secids if needed, monitor AWS costs, handle edge cases (e.g., empty sections).