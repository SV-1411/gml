# How to Set Agent ID

## The Problem
Error: `Agent ID required. Provide X-Agent-ID header.`

This happens because the memory API requires an agent ID to identify who is creating the memory.

## Quick Fix

### Option 1: Use Settings Page (Easiest)

1. **Go to Settings page** (in the sidebar menu)
2. **You'll see two options:**
   - **Dropdown:** Select from registered agents (if you have any)
   - **Manual input:** Enter agent ID directly
3. **Click "Save"** button

### Option 2: Register an Agent First

If you don't have any agents:

1. **Go to Agents page**
2. **Click "Register Agent"**
3. **Fill in the form:**
   - Agent ID: `my-agent-001` (or any ID you want)
   - Name: `My Agent`
   - Capabilities: Add at least one (e.g., "memory_management")
4. **Click "Register"**
5. **The agent ID is automatically saved** to localStorage

### Option 3: Use an Existing Agent

If you already have agents registered:

1. **Go to Settings page**
2. **Select an agent from the dropdown**
3. **Click "Save"**

## After Setting Agent ID

Once you set an agent ID in Settings:
- ✅ It's saved in localStorage
- ✅ All API calls automatically include `X-Agent-ID` header
- ✅ You can create memories
- ✅ File uploads will work
- ✅ Everything will work!

## Verify Agent ID is Set

1. Go to Settings page
2. You should see your agent ID in the input field
3. If empty, select one or enter manually

## Notes

- The agent ID is stored in browser localStorage
- It persists across page refreshes
- You can change it anytime in Settings
- When you register a new agent, it's automatically set as your default

## Summary

**The fix is simple:**
1. Go to Settings page
2. Select or enter an Agent ID
3. Click Save
4. Try creating memory again - it will work!

