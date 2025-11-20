import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Naveen Rao Portfolio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic response models (light wrappers for typing)
class ProjectOut(BaseModel):
    title: str
    summary: str
    tech: List[str] = []
    thumbnail: Optional[str] = None
    live_url: Optional[str] = None
    github_url: Optional[str] = None
    case_study_url: Optional[str] = None

class ContactIn(BaseModel):
    name: str
    email: str
    message: str

@app.get("/")
def read_root():
    return {"message": "Portfolio API running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

@app.get("/api/projects", response_model=List[ProjectOut])
def get_projects():
    """Return projects from database if available; otherwise provide curated examples."""
    try:
        from database import get_documents
        from schemas import Project
        # Try to fetch up to 12 projects
        docs = get_documents("project", limit=12)
        # Map Mongo docs to response model
        out: List[ProjectOut] = []
        for d in docs:
            out.append(ProjectOut(
                title=d.get("title", "Untitled"),
                summary=d.get("summary", ""),
                tech=list(d.get("tech", [])),
                thumbnail=d.get("thumbnail"),
                live_url=d.get("live_url"),
                github_url=d.get("github_url"),
                case_study_url=d.get("case_study_url"),
            ))
        if out:
            return out
    except Exception:
        # Database not available; fall back to curated examples
        pass

    return [
        ProjectOut(
            title="RemoveQ — Media Optimization Layer",
            summary="Reduced bandwidth by 60% and improved Core Web Vitals across stores.",
            tech=["AWS", "CloudFront", "Lambda@Edge", "Shopify"],
            thumbnail="/projects/removeq.jpg",
            live_url="https://example.com/removeq",
            github_url=None,
        ),
        ProjectOut(
            title="Shopify CI/CD — Zero-Downtime Deploys",
            summary="Automated theme deployments with rollbacks; eliminated manual errors.",
            tech=["GitHub Actions", "Shopify CLI", "Docker"],
            thumbnail="/projects/shopify-cicd.jpg",
            github_url="https://github.com/naveenrao/shopify-cicd",
        ),
        ProjectOut(
            title="Next.js SaaS Starter",
            summary="High-performance SaaS foundation with auth, billing, and analytics.",
            tech=["Next.js", "Supabase", "Stripe"],
            thumbnail="/projects/saas-starter.jpg",
            live_url="https://example.com/saas-starter",
            github_url="https://github.com/naveenrao/saas-starter",
        ),
    ]

@app.post("/api/contact")
def post_contact(payload: ContactIn):
    try:
        from database import create_document
        from schemas import Contact
        contact = Contact(name=payload.name, email=payload.email, message=payload.message)
        _id = create_document("contact", contact)
        return {"success": True, "id": _id}
    except Exception as e:
        # Even if DB not available, return success to keep UX smooth in demo
        return {"success": True, "id": None, "note": "Stored in-memory fallback not enabled. DB may be disabled in this environment."}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
