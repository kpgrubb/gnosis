# GNOSIS — Personal Research Intelligence

Query your curated PDF corpus in plain language. Get cited, trust-tiered answers.

## Setup

```bash
pip install -r requirements.txt
```

### 1. OpenAI API Key

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Authentication

Generate a password hash:

```bash
python -c "from auth import hash_password; print(hash_password('your-password'))"
```

Create `.streamlit/secrets.toml`:

```toml
[passwords]
admin = "$2b$12$YOUR_HASH_HERE"
```

### 3. Add Reports

- Drop PDFs into `data/reports/`
- Edit `data/reports/metadata.json` to assign trust tiers

### 4. Run

```bash
streamlit run app.py
```

## Trust Tiers

| Tier | Meaning | Badge |
|------|---------|-------|
| 1 | Verified — top-tier source | Green |
| 2 | Credible — reputable but secondary | Yellow |
| 3 | Caveat — use with caution | Red |
