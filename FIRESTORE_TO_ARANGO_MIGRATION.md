# Firestore to ArangoDB Migration Guide

## 🎯 Migration Overview

This document outlines the migration from Firestore to ArangoDB for presentation storage, leveraging the existing ArangoDB infrastructure already built into the ADK agents.

## ✅ Completed Components

### 1. Frontend ArangoDB Client (`src/lib/arango-client.ts`)
- **Purpose**: Frontend interface to ArangoDB backend
- **Features**:
  - Create/update presentations
  - Batch operations for complex saves
  - Automatic fallback to localStorage
  - Type-safe API with error handling
  - Project-based data organization

### 2. Backend API Routes (`adkpy/app/arango_routes.py`)
- **Purpose**: REST endpoints for presentation persistence
- **Endpoints**:
  - `POST /v1/arango/presentations` - Create presentation
  - `PUT /v1/arango/presentations/{id}/status` - Update status
  - `GET /v1/arango/presentations/{id}/state` - Get complete state
  - `POST /v1/arango/presentations/batch` - Batch operations
  - `GET /v1/arango/health` - Health check
- **Integration**: Uses existing `EnhancedArangoClient` from agent infrastructure

### 3. Enhanced Presentation Hook (`src/hooks/use-presentation-state-arango.ts`)
- **Purpose**: Drop-in replacement for Firestore-based hook
- **Features**:
  - ArangoDB persistence with localStorage fallback
  - Auto-save with debouncing
  - Local file uploads (project-based directories)
  - Real-time state synchronization

### 4. Existing ArangoDB Infrastructure (Already Built)
- **`EnhancedArangoClient`**: Production-ready client with connection pooling
- **Database Schema**: Complete presentation schema with versioning
- **Multi-agent coordination**: Project-based partitioning
- **Health monitoring**: Built-in connection health checks

## 🔧 Integration Steps Required

### Step 1: Enable ArangoDB Routes in FastAPI
Add to `adkpy/app/main.py` (around line 200, after health endpoint):

```python
# --- ArangoDB Presentation Persistence Routes ---
try:
    from .arango_routes import router as arango_router, cleanup_arango_client
    app.include_router(arango_router)
    logger.info("ArangoDB presentation persistence routes registered")
except ImportError as e:
    logger.warning(f"ArangoDB routes not available: {e}")
    cleanup_arango_client = None
```

### Step 2: Switch Presentation Hook
In components using presentation state, replace:

```typescript
// OLD: Firestore version
import { usePresentationState } from '@/hooks/use-presentation-state';

// NEW: ArangoDB version
import { usePresentationStateArango as usePresentationState } from '@/hooks/use-presentation-state-arango';
```

### Step 3: Update Environment Variables
Add to `.env` files:

```bash
# Optional - disable ArangoDB for testing
NEXT_PUBLIC_DISABLE_ARANGO=false

# Enable local file uploads (already supported)
NEXT_PUBLIC_LOCAL_UPLOADS=true

# ArangoDB connection (inherited from agent configuration)
ARANGODB_URL=http://arangodb:8529
ARANGODB_USER=root
ARANGODB_PASSWORD=root
ARANGODB_DB=presentpro
```

## 🗂️ File Storage Strategy

### Local Project-Based Storage
- **Location**: `public/uploads/{presentationId}/`
- **Structure**: Organized by presentation ID for easy cleanup
- **Benefits**:
  - No cloud storage costs
  - Fast access during development
  - Easy backup/restore
  - Project isolation

### Upload API Integration
The existing `/api/upload` endpoint already supports project-based organization:

```typescript
// Files automatically organized by presentation ID
const uploadResult = await uploadFile(file);
// Results in: public/uploads/{presentationId}/{filename}
```

## 📊 Database Schema Mapping

### Firestore → ArangoDB Collections

| Firestore | ArangoDB Collection | Purpose |
|-----------|-------------------|---------|
| `presentations/{id}` | `presentations` | Core metadata |
| `presentations/{id}` | `clarifications` | Chat history |
| `presentations/{id}` | `outlines` | Presentation structure |
| `presentations/{id}` | `slides` | Slide content (versioned) |
| N/A | `design_specs` | Visual design data |
| N/A | `speaker_notes` | Enhanced notes |
| N/A | `scripts` | Full scripts |
| N/A | `reviews` | Critic feedback |

### Data Transformation
The ArangoDB client handles automatic conversion:

```typescript
// Frontend Presentation type → ArangoDB collections
await savePresentation(presentation);

// ArangoDB collections → Frontend Presentation type
const presentation = await loadPresentation(presentationId);
```

## 🔄 Migration Benefits

### 1. Leverages Existing Infrastructure
- **No new database setup**: Uses existing ArangoDB instance
- **Connection pooling**: Already optimized for performance
- **Multi-agent coordination**: Built-in project isolation
- **Health monitoring**: Existing monitoring and retry logic

### 2. Enhanced Capabilities
- **Versioning**: Slide content history tracking
- **Agent attribution**: Track which agent modified what
- **Graph relationships**: Future support for complex queries
- **Real-time updates**: Potential for WebSocket integration

### 3. Cost & Performance
- **No Firestore costs**: Eliminates cloud database expenses
- **Local file storage**: No Firebase Storage costs
- **Faster queries**: Direct database access vs. cloud API
- **Better caching**: Local connection pooling

## 🚨 Rollback Strategy

### Environment Flag Rollback
Set environment variable to disable ArangoDB:

```bash
NEXT_PUBLIC_DISABLE_ARANGO=true
```

This automatically falls back to localStorage-only mode.

### Component-Level Rollback
Revert import in components:

```typescript
// Rollback to Firestore
import { usePresentationState } from '@/hooks/use-presentation-state';
```

### Data Migration
Both systems can coexist during transition:
- ArangoDB client falls back to localStorage
- Firestore version continues to work unchanged
- Manual data export/import possible if needed

## 🧪 Testing Strategy

### 1. Health Check Tests
```bash
# Test ArangoDB connection
curl http://localhost:8089/v1/arango/health

# Test agent connectivity
curl http://localhost:10001/health
```

### 2. Data Persistence Tests
1. Create presentation with content
2. Refresh browser (localStorage fallback)
3. Restart services (ArangoDB persistence)
4. Verify data integrity

### 3. File Upload Tests
1. Upload files in presentation
2. Verify organization: `public/uploads/{presentationId}/`
3. Test file access via URLs
4. Verify cleanup on presentation delete

## 📋 Remaining Tasks

### Immediate (Required for Basic Function)
- [ ] **Integrate ArangoDB routes** in `main.py`
- [ ] **Switch presentation hook** in main components
- [ ] **Test basic create/save/load** workflow

### Optional (Enhanced Features)
- [ ] **Remove Firestore dependencies** from package.json
- [ ] **Real-time updates** via WebSocket
- [ ] **Background sync** for offline support
- [ ] **Data migration script** for existing users

### Cleanup (Post-Migration)
- [ ] **Remove Firestore files** (`firebase.ts`, etc.)
- [ ] **Update Docker configs** (remove Firebase environment)
- [ ] **Update documentation** to reflect ArangoDB usage

## 🔍 Troubleshooting

### Common Issues

1. **"ArangoDB not available" errors**
   - Check Docker: `docker ps | grep arango`
   - Check connection: `curl http://localhost:8530/_api/version`
   - Verify environment variables

2. **Files not uploading**
   - Check directory permissions: `public/uploads/`
   - Verify `/api/upload` endpoint
   - Check file size limits

3. **Data not persisting**
   - Enable debug logging in ArangoDB client
   - Check browser console for errors
   - Verify presentation ID generation

4. **Migration conflicts**
   - Use `NEXT_PUBLIC_DISABLE_ARANGO=true` to test
   - Check both localStorage and ArangoDB data
   - Verify component import paths

## 📞 Support

- **ArangoDB Issues**: Check `adkpy/agents/base_arango_client.py` logs
- **Frontend Issues**: Browser console + Network tab
- **File Upload Issues**: Check `public/uploads/` permissions
- **Integration Issues**: Verify environment variable setup

## 🎉 Success Metrics

Migration is complete when:
- ✅ Presentations save/load without Firestore errors
- ✅ Files upload to project-based directories
- ✅ Real-time updates work (browser refresh preserves state)
- ✅ No Firebase/Firestore console errors
- ✅ ArangoDB health checks pass
- ✅ Local development works offline

---

**Next Step**: Integrate the ArangoDB routes into the main FastAPI application to enable the new persistence layer.