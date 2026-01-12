# Code Archaeologist Frontend

Next.js frontend for the Code Archaeologist graph-RAG application.

## Features

- **Interactive Graph Visualization**: React Flow-based graph canvas showing code structure
- **Natural Language Chat**: Query your codebase using natural language
- **Code Inspector**: View detailed information about selected nodes
- **Repository Ingestion**: Import GitHub repositories for analysis

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Graph Visualization**: React Flow
- **State Management**: React Hooks

## Project Structure

```
frontend/
├── app/
│   ├── components/
│   │   ├── GraphCanvas.tsx      # Graph visualization component
│   │   ├── ChatSidebar.tsx      # Chat interface component
│   │   ├── CodeInspector.tsx    # Code details panel
│   │   └── IngestionPanel.tsx   # Repository ingestion UI
│   ├── layout.tsx               # Root layout
│   ├── page.tsx                 # Main page
│   └── globals.css              # Global styles
├── lib/
│   ├── api.ts                   # API client for backend
│   └── utils.ts                 # Utility functions
├── types/
│   └── index.ts                 # TypeScript type definitions
└── package.json
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend server running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

The application will be available at `http://localhost:3000`.

## Components

### GraphCanvas

Renders the code structure as an interactive graph using React Flow.

- **Features**: Zoom, pan, node highlighting, click interactions
- **Node Types**: File (blue), Class (green), Function (orange)
- **Edge Types**: CONTAINS, DEFINES, CALLS

### ChatSidebar

Natural language interface for querying the codebase.

- **Features**: Message history, node references, real-time responses
- **Example Queries**:
  - "Show me all classes"
  - "Find functions that call authenticate"
  - "What files contain the User class?"

### CodeInspector

Displays detailed information about selected nodes.

- **Features**: Node metadata, code preview, file location
- **Node Types**: File, Class, Function

### IngestionPanel

UI for importing GitHub repositories.

- **Features**: URL validation, progress tracking, error handling
- **Supported**: Public GitHub repositories with Python/JavaScript code

## API Integration

The frontend communicates with the backend via REST API:

- `GET /health` - Check backend status
- `GET /graph` - Fetch complete graph data
- `POST /chat` - Send natural language queries
- `POST /ingest` - Ingest a repository

See `lib/api.ts` for the complete API client implementation.

## Configuration

### Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Tailwind Configuration

Customize styling in `tailwind.config.js`.

## Development

### Type Safety

All components use TypeScript with strict type checking. Type definitions are in `types/index.ts`.

### Code Style

- ESLint for linting
- Prettier for formatting (recommended)
- Follow Next.js best practices

### Testing

```bash
# Run linter
npm run lint

# Type check
npm run build
```

## Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Docker

```bash
# Build image
docker build -t code-archaeologist-frontend .

# Run container
docker run -p 3000:3000 code-archaeologist-frontend
```

## Troubleshooting

### Backend Connection Issues

- Ensure backend is running on `http://localhost:8000`
- Check CORS configuration in backend
- Verify `NEXT_PUBLIC_API_URL` environment variable

### Build Errors

- Clear `.next` directory: `rm -rf .next`
- Reinstall dependencies: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (should be 18+)

## License

MIT
