Mongo tools for the MoviesReviews project

This folder contains `mongo_tools.py`, a small utility module with functions and a CLI to perform CRUD operations, manage indexes, and analyze query plans against the project's MongoDB database.

Quick PowerShell examples (run from project root):

Enable Mongo for the one-off command and list indexes for the `movies` collection:

```powershell
$env:USE_MONGODB='True'; $env:MONGODB_URI='mongodb://localhost:27017'; $env:MONGODB_NAME='moviereviews_db'; python .\scripts\mongo_tools.py list-indexes --collection movies
```

Explain a query and show the execution plan (for a movie with slug `inception`):

```powershell
$env:USE_MONGODB='True'; python .\scripts\mongo_tools.py explain --collection movies --filter '{"slug":"inception"}'
```

Analyze a query (execution time and simple recommendations):

```powershell
$env:USE_MONGODB='True'; python .\scripts\mongo_tools.py explain --collection movies --filter '{"slug":"inception"}'
# or use the analyze helper programmatically from a Python REPL
```

Create a simple compound index (unique):

```powershell
$env:USE_MONGODB='True'; python .\scripts\mongo_tools.py create-index --collection movies --keys 'slug:1,title:1' --unique
```

Insert a document into `reviews`:

```powershell
$env:USE_MONGODB='True'; python .\scripts\mongo_tools.py create --collection reviews --doc '{"movie_slug":"inception","username":"alice","rating":5,"title":"Great","body":"Loved it"}'
```

Notes
- These examples set `USE_MONGODB=True` only for the spawned process; they do not change your project settings permanently.
- The analyze/suggest index helpers are heuristic and provide simple, human-readable recommendations; they are not a replacement for in-depth profiling.
- If Mongo is not running or inaccessible, the commands will print a helpful error.
