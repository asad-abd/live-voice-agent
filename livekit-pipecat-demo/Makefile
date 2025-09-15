# LiveKit + Pipecat Demo with React Client - ULTRA SIMPLE
# Just 2 commands: setup + demo

.PHONY: setup demo demo-quick stop

# Default target shows help
help: ## Show available commands
	@echo "LiveKit + Pipecat Demo with React Client - ULTRA SIMPLE"
	@echo ""
	@echo "  make setup           - Install everything (run once)"
	@echo "  make demo            - Start demo (browser opens automatically)"
	@echo "  make demo-quick - Start demo without LiveKit (assumes already running)"
	@echo ""
	@echo "🛑 To stop:"
	@echo "  make stop            - Stop all services"
	@echo ""
	@echo "⚡ First time: make setup && make demo"
	@echo "⚡ Next time:  make demo"
	@echo "⚡ LiveKit running: make demo-quick"

setup: ## Complete setup - install everything
	@echo "🏗️  Setting up LiveKit + Pipecat Demo..."
	
	# Check Docker
	@if ! command -v docker >/dev/null 2>&1; then \
		echo "❌ Docker not found. Install Docker Desktop first."; \
		exit 1; \
	fi
	
	# Check Python
	@if ! command -v python3 >/dev/null 2>&1; then \
		echo "❌ Python 3 not found. Install Python 3.8+ first."; \
		exit 1; \
	fi
	
	# Create virtual environment
	@echo "🐍 Creating virtual environment..."
	@python3 -m venv venv
	
	# Install dependencies
	@echo "📦 Installing Python dependencies..."
	@./venv/bin/python -m pip install --upgrade pip --quiet
	@cd agent && ../venv/bin/python -m pip install -r requirements.txt --quiet
	@cd cmd/token_server && ../../venv/bin/python -m pip install -r requirements.txt --quiet

	# Install React client dependencies
	@echo "📦 Installing React client dependencies..."
	@cd client-react && npm install --silent
	
	# Test imports
	@echo "🧪 Testing installations..."
	@./venv/bin/python -c "import pipecat; print('✅ Pipecat ready')" 2>/dev/null || echo "⚠️  Pipecat import warning (may still work)"
	@./venv/bin/python -c "import fastapi; print('✅ FastAPI ready')" 2>/dev/null || echo "❌ FastAPI failed"
	@./venv/bin/python -c "import livekit; print('✅ LiveKit ready')" 2>/dev/null || echo "❌ LiveKit failed"
	
	@echo ""
	@echo "✅ Setup complete! Now run: make demo"

demo: ## Start everything and open browser
	@echo "🚀 Starting LiveKit + Pipecat Demo..."
	
	# Stop any existing services
	@echo "🧹 Cleaning up..."
	@-lsof -ti:3000,7880,8080 | xargs kill -9 2>/dev/null || true
	@-pkill -f "spawn_agent.py\|main.py\|http.server 3000\|react-scripts start" 2>/dev/null || true
	@-docker stop $$(docker ps -q --filter "publish=7880") 2>/dev/null || true
	
	# Start LiveKit server (backend first)
	@echo "📡 Starting LiveKit server..."
	@if command -v docker-compose >/dev/null 2>&1; then \
		docker-compose up -d; \
	else \
		docker compose up -d; \
	fi
	
	# Wait for LiveKit to be ready (HTTP OK)
	@echo "⏳ Waiting for LiveKit server (http://localhost:7880)..."
	@attempts=0; \
	until curl -fsS http://localhost:7880 >/dev/null 2>&1; do \
		attempts=$$((attempts+1)); \
		if [ $$attempts -gt 40 ]; then \
			echo "❌ LiveKit did not become ready"; \
			docker logs $$((docker ps -q --filter name=livekit* | head -n1)) 2>/dev/null || true; \
			exit 1; \
		fi; \
		sleep 1; \
	done; \
	echo "✅ LiveKit server ready!"
	
	# Start token server
	@echo "🔑 Starting token server..."
	@cd cmd/token_server && ../../venv/bin/python main.py &
	@sleep 2
	
	# Start agent (before frontend so Deepgram/LiveKit is ready)
	@echo "🤖 Starting Pipecat agent..."
	@cd agent && ../venv/bin/python spawn_agent.py &
	@sleep 3

	# Start React client last
	@echo "🌐 Starting React client..."
	@cd client-react && npm start &
	@sleep 10
	
	# Open browser
	@echo ""
	@echo "🎉 Demo ready!"
	@echo "🌐 Opening browser at http://localhost:3000..."
	@if command -v open >/dev/null 2>&1; then \
		open http://localhost:3000; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:3000; \
	else \
		echo "📱 Manually open: http://localhost:3000"; \
	fi
	@echo ""
	@echo "🎤 Click 'Join Room and Enable Mic' to test the React client!"
	@echo "🛑 To stop: make stop"

demo-quick: ## Start demo without LiveKit (assumes LiveKit already running)
	@echo "🚀 Starting Pipecat Demo (LiveKit assumed running)..."
	
	# Check if LiveKit is already running
	@if ! docker ps | grep -q livekit-server; then \
		echo "⚠️  LiveKit server not detected. Consider running 'make demo' instead."; \
		echo "📡 Continuing anyway..."; \
	else \
		echo "✅ LiveKit server detected!"; \
	fi
	
	# Stop any existing services (except LiveKit)
	@echo "🧹 Cleaning up existing services..."
	@-lsof -ti:3000,8080 | xargs kill -9 2>/dev/null || true
	@-pkill -f "spawn_agent.py\|main.py\|http.server 3000\|react-scripts start" 2>/dev/null || true
	
	# Start token server
	@echo "🔑 Starting token server..."
	@cd cmd/token_server && ../../venv/bin/python main.py &
	@sleep 2
	
	# Start React client
	@echo "🌐 Starting React client..."
	@cd client-react && npm start &
	@sleep 10
	
	# Start agent
	@echo "🤖 Starting Pipecat agent..."
	@cd agent && ../venv/bin/python spawn_agent.py &
	@sleep 3
	
	# Open browser
	@echo ""
	@echo "🎉 Demo ready!"
	@echo "🌐 Opening browser at http://localhost:3000..."
	@if command -v open >/dev/null 2>&1; then \
		open http://localhost:3000; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:3000; \
	else \
		echo "📱 Manually open: http://localhost:3000"; \
	fi
	@echo ""
	@echo "🎤 Click 'Join Room and Enable Mic' to test the React client!"
	@echo "🛑 To stop: make stop"

stop: ## Stop all services
	@echo "🛑 Stopping all services..."
	@-lsof -ti:3000,7880,8080 | xargs kill -9 2>/dev/null || true
	@-pkill -f "spawn_agent.py\|main.py\|http.server 3000\|react-scripts start" 2>/dev/null || true
	@if command -v docker-compose >/dev/null 2>&1; then \
		docker-compose down 2>/dev/null || true; \
	else \
		docker compose down 2>/dev/null || true; \
	fi
	@echo "✅ All services stopped"