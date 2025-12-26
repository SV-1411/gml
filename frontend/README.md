# GML Infrastructure Frontend

Modern React.js dashboard for GML Infrastructure with ChatGPT-like chat interface.

## Features

- 🎨 **Modern UI**: Clean, professional interface with white/black theme support
- 💬 **ChatGPT-like Chat**: Beautiful chat interface similar to ChatGPT/Gemini
- 🤖 **Agent Management**: Register and manage AI agents
- 🧠 **Memory Management**: Search and manage agent memories
- 📊 **Dashboard**: Overview of system status and metrics
- 🌓 **Theme Toggle**: Switch between light and dark themes
- ⚡ **Fast**: Built with Vite for optimal performance

## Tech Stack

- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Axios
- Lucide React (Icons)

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build

```bash
npm run build
```

The built files will be in the `dist` directory.

## Configuration

### API URL

The frontend connects to the backend API. By default, it uses `http://localhost:8000`.

To change the API URL, create a `.env` file:

```
VITE_API_URL=http://localhost:8000
```

## Usage

1. **Register an Agent**: Go to Settings and set your Agent ID, or register a new agent in the Agents page
2. **Start Chatting**: Use the Chat page to interact with AI models
3. **Manage Memories**: Search and create memories in the Memories page
4. **Monitor System**: View system status and metrics in the Dashboard

## Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable components
│   │   ├── Layout/      # Layout components (Sidebar, Header)
│   │   ├── Agents/      # Agent-related components
│   │   └── Memories/    # Memory-related components
│   ├── contexts/        # React contexts (Theme)
│   ├── pages/           # Page components
│   ├── services/        # API service layer
│   ├── App.tsx          # Main app component
│   └── main.tsx         # Entry point
├── public/              # Static assets
└── package.json
```

## License

MIT

