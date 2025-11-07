set -e

echo "🚀 PDF Extractor - Starting Services"
echo ""

if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
    echo "Then run this script again."
    exit 1
fi

if ! grep -q "^OPENAI_API_KEY=sk-" .env; then
    echo "⚠️  OPENAI_API_KEY not configured in .env"
    echo "Please edit .env and add your OpenAI API key."
    exit 1
fi

echo "✓ Environment configured"
echo ""

echo "Building and starting containers..."
docker compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

echo ""
echo "Checking backend health..."
for i in {1..30}; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ Backend is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start"
        docker-compose logs backend
        exit 1
    fi
    sleep 2
done

echo ""
echo "✅ Services are running!"
echo ""
echo "📱 Frontend:  http://localhost:8080"
echo "🔧 Backend:   http://localhost:8000"
echo "📚 API Docs:  http://localhost:8000/docs"
echo ""
echo "View logs:    docker-compose logs -f"
echo "Stop:         docker-compose down"
echo ""
