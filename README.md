# Mini-RAG

A production-style **Retrieval-Augmented Generation (RAG)** backend for document-based question answering, built with FastAPI, PostgreSQL/PgVector, and a modular, provider-agnostic architecture.

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-PgVector-336791)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)
![License](https://img.shields.io/badge/license-MIT-green)

## Overview

Mini-RAG is an end-to-end RAG pipeline: users upload documents, the system chunks and embeds them, stores the embeddings in a Postgres/PgVector store, and answers natural-language questions by retrieving relevant context and generating grounded responses through an LLM. The system is built around a **factory-pattern architecture**, making it easy to swap LLM providers or vector stores without touching business logic.

## Features

- 📄 **File Upload & Processing** — ingest and pre-process documents for indexing
- 🧠 **LLM Factory** — pluggable architecture supporting multiple LLM providers
- 🗂️ **Vector DB Factory** — pluggable architecture supporting multiple vector stores
- 🔍 **Semantic Search** — similarity search over embedded document chunks
- 💬 **Augmented Answers** — context-grounded answer generation (RAG)
- 🐘 **Postgres + PgVector** — persistent, production-grade vector storage
- 🐳 **Dockerized** — one-command environment setup with Docker Compose
- 🔄 **Alembic Migrations** — versioned, reproducible database schema

## Tech Stack

| Layer            | Technology                  |
|-------------------|------------------------------|
| API Framework      | FastAPI (async)               |
| Database           | PostgreSQL + PgVector         |
| ORM / Migrations   | SQLAlchemy + Alembic          |
| LLM Integration    | Provider-agnostic LLM Factory |
| Vector Store       | Provider-agnostic Vector DB Factory |
| Containerization   | Docker & Docker Compose       |
| API Testing        | POSTMAN Collection            |

## Table of Contents

- [Requirements](#requirements)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Database Migrations](#database-migrations)
- [Running with Docker](#running-with-docker)
- [Running the Server Locally](#running-the-server-locally)
- [API Testing](#api-testing)
- [License](#license)

## Requirements

- Python 3.12 or later
- Docker & Docker Compose

## Getting Started

### 1. Set up a Python environment with MiniConda

Download and install MiniConda from the [official quick command-line install guide](https://docs.anaconda.com/free/miniconda/#quick-command-line-install), then create and activate a dedicated environment:

```bash
conda create -n mini-rag python=3.12
conda activate mini-rag
```

> **Tip:** For a more readable terminal prompt while working in this project, you can optionally set:
> ```bash
> export PS1="\[\033[01;32m\]\u@\h:\w\n\[\033[00m\]\$ "
> ```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

## Configuration

Copy the example environment file and fill in your own values:

```bash
cp .env.example .env
```

At minimum, set your `OPENAI_API_KEY` in the `.env` file, along with your Postgres connection details.

## Database Migrations

This project uses **SQLAlchemy** with **Alembic** for versioned schema migrations against Postgres/PgVector.

```bash
alembic upgrade head
```

## Running with Docker

The project ships with a Docker Compose setup for Postgres (with the PgVector extension).

```bash
cd docker
cp .env.example .env
```

Update the `.env` file with your credentials, then start the services:

```bash
cd docker
sudo docker compose up -d
```

## Running the Server Locally

Start the FastAPI development server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

The API will be available at `http://localhost:5000`, with interactive docs at `http://localhost:5000/docs`.

## API Testing

A ready-to-use POSTMAN collection is included for exploring and testing the API endpoints:

[`/assets/mini-rag-app.postman_collection.json`](/assets/mini-rag-app.postman_collection.json)

## License

This project is licensed under the MIT License.
