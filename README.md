# Examtie Backend system

Submission for the 27ᵗʰ National Software Contest (NSC)

> [!TIP]
> Instruction for running Examtie with docker compose available at [Examtie/Examtie](https://github.com/Examtie/Examtie)

## Quick Start

### Development Server

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Using Docker

```bash
docker build -t examtie-backend .
docker run -p 8000:8000 examtie-backend
```
