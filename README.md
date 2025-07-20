# OptiSigns Support Bot

Daily automated scraper for OptiSigns support articles with OpenAI Vector Store integration.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

## How to Run Locally

````bash
# Run scraper and upload to OpenAI
git clone https://github.com/haihhdev/mini-supportbot.git
cd mini-supportbot
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
pip install -r requirements.txt
python main.py


## Docker

```bash
# Build and run
docker build -t mini-supportbot .
docker run -e OPENAI_API_KEY=your-api-key mini-supportbot
````

## Screenshot of Playground Answer

The OptiBot assistant correctly answers "How do I add a YouTube video?" with proper citations from uploaded documentation.

_Note: Screenshot shows assistant responding with citations from OptiSigns support articles._
