# Sagar AI

Intelligent prompting micro-service of **Project ____________** enabling platform users to retrieve, analyse and work with the integrated ocean and marine science data for Indian maritime and EEZ.

## 🏗️ Architecture

- **Broker Server**: It is a proxy server through which client connect and avail prompting services of platform. It is responsible to manage multiple connected users and implement RAG based context generation for user prompts. It also sends users requests to desired Model servers 

- **Intelligence Servers**: They are servers with LLM Model pools utilizing diffrent models as required by request. They generate answers to user query in stream of tokens and return the tokens to broker to server client connections.

- **Containerization**:  Intelligent Prompting Service (Sagar  AI) of platform is containerized with DOCKER and it has container for broker server and one container each for different models. All servers run once and serve as single abstracted service using docker compose.  

## 🚀 Quick Start (Using Containers)

### Prerequisites
- Install Docker and Setup 
- Download LLM Base model files as in sagar_model/model-download.txt
### 1. Clone and Setup
```bash
git clone <repository-url>
cd sagar-ai
```
### 2. Copy Model Files and rename To Desired Location 
Download model files from sagar_model/model-download.txt rename downloaded files as per given name and copy to desired location.
- sagarTiny : [root]/sagar_model/sagar_tiny/sagartiny.gguf

### 2. Start All Services
```bash
# Using Docker
docker compose up

# Run in background (detached mode)
docker compose up -d
```

### 3. Test Services 
- **testClient.html (Testing Interface)**: http://localhost:8080 
- **sagar-ai-server**: ws://localhost:8000/{endpoints}
- **model-server-sagar-tiny**: ws://localhost:8001/{endpoints}

### 4. Stop Services
```bash
# Stop services
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v
```

## 🌐 API Endpoints

### Broker Server
- #### Docker Environment
  - `https://sagar-ai/` - serve testClient.html (Testing Interface for this service) 
  - `ws://sagar-ai/test` - check server status / echo message back 
  - `ws://sagar-ai/sagarAI` - prompt to default language model service 
- #### Local Environment
  - `ws://localhost:8000/{endpoint}`

### Model Servers 
- #### Docker Environment
  - `ws://model-server-sagar-tiny/generate` - stream back generated tokens on user query to broker server when using sagarTiny.
- #### Local Environment
  - `ws://localhost:8001/{endpoint}`

## Information
1. This is a micro-service part of a platform 
2. Reuse not allowed without permission 
3. Developed & Managed by group of individuals

## 📞 Support
For questions or issues, please open an issue on the project repository or mail any member of project.  