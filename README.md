# ai-music-producer

# Start Backend:
```
cd server
venv\Scripts\activate
uvicorn app:app --reload --port 8000

// Deactivate virtual environment
deactivate
```

# Use Python Launcher with version specification
```
cd server
py -3.11 -m venv venv
```
# Activate virtual env
```
cd server
venv\Scripts\activate
```

# VS Code Setting
選擇正確的 Python 解釋器：
```
按 Ctrl + Shift + P
輸入 "Python: Select Interpreter"
選擇虛擬環境的解釋器：
.\venv\Scripts\python.exe
```
# Start Frontend:
```
cd client
npm run dev
```
# Start Database:
```
docker-compose up -d

// 停止所有服務
docker-compose down

//僅停止容器（保留容器）,稍後可以用 docker-compose start 重新啟動
docker-compose stop

# 只停止 MongoDB
docker-compose stop mongodb

# 只停止 Redis
docker-compose stop redis

# 查看容器狀態
docker-compose ps

# 查看所有 Docker 容器
docker ps -a

# 查看正在運行的容器
docker ps
```


# Frontend Dependencies
```
cd client
npm install react react-dom
npm install @vitejs/plugin-react vite
npm install tone wavesurfer.js midi-parser-js
npm install axios react-query --force
npm install @mui/material @emotion/react @emotion/styled --force
npm install react-dropzone react-hot-toast --force
```



# Use Here-String to create a server/requirements.txt file
```
@"
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
numpy==1.24.3
librosa==0.10.1
soundfile==0.12.1
tensorflow==2.15.0
torch==2.1.0
torchaudio==2.1.0
mido==1.3.0
pretty_midi==0.2.10
music21==8.1.0
scipy==1.11.4
matplotlib==3.8.0
pandas==2.1.3
scikit-learn==1.3.2
motor==3.3.2
python-dotenv==1.0.0
pydub==0.25.1
pymongo==4.5.0
moviepy 
opencv-python 
matplotlib
"@ | Out-File -FilePath "requirements.txt" -Encoding utf8 -Force

pip install -r requirements.txt
```

# 在 PowerShell 中創建 docker-compose.yml
```
@"
version: '3.8'
services:
  mongodb:
    image: mongo:latest
    container_name: music-mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password123
  redis:
    image: redis:alpine
    container_name: music-redis
    ports:
      - "6379:6379"

volumes:
  mongodb_data:
"@ | Out-File -FilePath "docker-compose.yml" -Encoding utf8

# Start MongoDB and Redis
docker-compose up -d
```

# 創建 server/.env 文件
```
@"
MONGO_URL=mongodb://admin:password123@localhost:27017/
DATABASE_NAME=music_producer
REDIS_URL=redis://localhost:6379
API_KEY=your_api_key_here
"@ | Out-File -FilePath "server\.env" -Encoding utf8
```

# 創建 client/.env 文件
```

@"
VITE_API_URL=http://localhost:8000
"@ | Out-File -FilePath "client\.env" -Encoding utf8
```

# AI Music Producer - Project Structure

```
📁 ai-music-producer/
├── 📁 .git/                           # Git version control
├── 📄 .env                            # Environment variables (root)
├── 📄 .gitignore                      # Git ignore file (root)
├── 📄 docker-compose.yml              # Docker compose configuration
├── 📄 README.md                       # Project documentation
├── 📁 data/                           # Data directory
│
├── 📁 client/                         # Frontend React Application
│   ├── 📁 node_modules/               # Frontend dependencies
│   ├── 📁 public/                     # Static assets
│   ├── 📁 src/                        # Source code
│   │   ├── 📁 components/             # React components
│   │   │   ├── 📄 ProjectManager.jsx  
│   │   │   ├── 📄 AudioVisualizer.jsx
│   │   │   ├── 📄 BeatGenerator.jsx
│   │   │   ├── 📄 HarmonyPanel.jsx
│   │   │   ├── 📄 MelodyGenerator.jsx
│   │   │   ├── 📄 MusicUploader.jsx
│   │   │   └── 📄 TrackCombiner.jsx
│   │   ├── 📁 hooks/                  # Custom React hooks
│   │   ├── 📁 utils/                  # Utility functions
│   │   ├── 📄 App.jsx                 # Main App component
│   │   ├── 📄 index.css               # Global styles
│   │   └── 📄 main.jsx                # Application entry point
│   ├── 📄 .gitignore                  # Frontend git ignore
│   ├── 📄 index.html                  # HTML template
│   ├── 📄 package.json                # Frontend dependencies & scripts
│   ├── 📄 package-lock.json           # Dependency lock file
│   └── 📄 vite.config.js              # Vite configuration
│
└── 📁 server/                         # Backend Python Application
    ├── 📁 api/                        # API layer
    │   ├── 📁 __pycache__/            # Python cache
    │   ├── 📄 .gitignore              # API git ignore
    │   └── 📄 database.py             # Database operations
    ├── 📁 audio/                      # Audio processing
    │   ├── 📁 __pycache__/            # Python cache
    │   ├── 📄 .gitignore              # Audio git ignore
    │   ├── 📄 analyzer.py             # Analyze song structure
    │   ├── 📄 combiner.py             # Combine audio tracks
    │   └── 📄 processor.py            # Audio processing logic
    ├── 📁 models/                     # AI Models
    │   ├── 📁 __pycache__/            # Python cache
    │   ├── 📄 .gitignore              # Models git ignore
    │   ├── 📄 beat_generator.py       # Beat generation AI model
    │   ├── 📄 harmony_suggester.py    # Harmony suggestion AI model
    │   └── 📄 melody_generator.py     # Melody generation AI model
    ├── 📁 temp/                       # Temporary files
    ├── 📁 venv/                       # Python virtual environment
    ├── 📄 .env                        # Backend environment variables
    ├── 📄 .gitignore                  # Backend git ignore
    ├── 📄 app.py                      # Main Flask/FastAPI application
    └── 📄 requirements.txt            # Python dependencies
```

# Architecture Overview

**Frontend (Client)**
- **Framework**: React with Vite for fast development
- **Structure**: Component-based architecture with custom hooks and utilities
- **Build Tool**: Vite for modern, fast bundling

**Backend (Server)**
- **Framework**: Python (likely Flask or FastAPI based on app.py)
- **AI Models**: Separate modules for different music generation tasks:
  - Beat generation
  - Melody generation  
  - Harmony suggestion
- **Audio Processing**: Dedicated audio processing module
- **Database**: Separate database layer for data persistence

**Development Environment**
- **Containerization**: Docker Compose for easy deployment
- **Version Control**: Git with appropriate .gitignore files
- **Virtual Environment**: Python venv for dependency isolation

