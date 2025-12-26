# Quick Start Guide

## Installation & Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Make sure backend is running:**
   ```bash
   # In the project root, start the backend server
   # Backend should be running on http://localhost:8000
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   ```

5. **Open your browser:**
   - Frontend: http://localhost:3000
   - Backend API Docs: http://localhost:8000/api/docs

## First Steps

1. **Register an Agent:**
   - Go to "Agents" page
   - Click "Register Agent"
   - Fill in the form and register
   - **IMPORTANT:** Save the API token shown after registration
   - The agent ID will be automatically saved

2. **Set Agent ID in Settings (optional):**
   - Go to "Settings" page
   - Enter your agent ID if you need to change it
   - This is used for memory operations

3. **Start Chatting:**
   - Go to "Chat" page
   - Select a model (default: gpt-oss:20b)
   - Type your message and press Enter
   - The chat will automatically search memories for context

4. **Manage Memories:**
   - Go to "Memories" page
   - Search for existing memories
   - Create new memories manually
   - Memories are automatically saved from chat conversations

## Features

✅ **Dashboard** - Overview of agents and system health  
✅ **Chat** - ChatGPT-like interface with memory integration  
✅ **Agents** - Register and manage AI agents  
✅ **Memories** - Search and manage agent memories  
✅ **Settings** - Configure agent ID and theme  
✅ **Theme Toggle** - Switch between light and dark mode  

## Troubleshooting

### Backend not connecting?
- Make sure backend is running on http://localhost:8000
- Check browser console for errors
- Verify API endpoints in browser network tab

### Chat not working?
- Ensure Ollama is running: `ollama serve`
- Check if models are available: `ollama list`
- Pull model if needed: `ollama pull gpt-oss:20b`

### Memory operations failing?
- Make sure you have an agent ID set
- Check Settings page and set agent ID if needed
- Verify agent is registered in Agents page

## Build for Production

```bash
npm run build
```

The production build will be in the `dist` folder.

