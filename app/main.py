from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile

from .config import get_settings
from .job_manager import JobManager
from .schemas import GenerationRequest, JobCreateResponse, JobState, QuestionType

settings = get_settings()
job_manager = JobManager(settings)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await job_manager.start()
    try:
        yield
    finally:
        await job_manager.stop()


app = FastAPI(title=settings.app_name, lifespan=lifespan)


def _parse_question_types(raw_value: str | None) -> list[QuestionType]:
    if not raw_value:
        return [QuestionType.single_choice]

    result: list[QuestionType] = []
    invalid_values: list[str] = []

    for item in raw_value.split(","):
        normalized = item.strip()
        if not normalized:
            continue
        try:
            result.append(QuestionType(normalized))
        except ValueError:
            invalid_values.append(normalized)

    if invalid_values:
        allowed = ", ".join(item.value for item in QuestionType)
        raise HTTPException(
            status_code=422,
            detail=(
                "Некорректные question_types: "
                f"{', '.join(invalid_values)}. Допустимые значения: {allowed}"
            ),
        )

    return result or [QuestionType.single_choice]


async def _extract_uploaded_files(request: Request) -> list[UploadFile]:
    form = await request.form()
    files: list[UploadFile] = []

    for item in form.getlist("files"):
        if isinstance(item, UploadFile) and item.filename:
            files.append(item)

    return files


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "app": settings.app_name}


@app.get("/config")
async def config() -> dict:
    return job_manager.config_snapshot()


@app.post("/jobs/generate", response_model=JobCreateResponse)
async def create_generation_job(
    request_http: Request,
    topic: str = Form(...),
    number: int = Form(...),
    question_types: str | None = Form(default="single_choice"),
    language: str = Form(default="ru"),
    difficulty: str | None = Form(default=None),
    audience: str | None = Form(default=None),
    extra_instructions: str | None = Form(default=None),
) -> JobCreateResponse:
    files = await _extract_uploaded_files(request_http)
    request = GenerationRequest(
        topic=topic,
        number=number,
        question_types=_parse_question_types(question_types),
        language=language,
        difficulty=difficulty,
        audience=audience,
        extra_instructions=extra_instructions,
    )
    job = await job_manager.create_job(request=request, files=files)
    return JobCreateResponse(job_id=job.id, status=job.status, created_at=job.created_at)


@app.get("/jobs/{job_id}", response_model=JobState)
async def get_job(job_id: str) -> JobState:
    return job_manager.get_job(job_id)


@app.post("/generate", response_model=JobState)
async def generate(
    request_http: Request,
    topic: str = Form(...),
    number: int = Form(...),
    question_types: str | None = Form(default="single_choice"),
    language: str = Form(default="ru"),
    difficulty: str | None = Form(default=None),
    audience: str | None = Form(default=None),
    extra_instructions: str | None = Form(default=None),
) -> JobState:
    files = await _extract_uploaded_files(request_http)
    request = GenerationRequest(
        topic=topic,
        number=number,
        question_types=_parse_question_types(question_types),
        language=language,
        difficulty=difficulty,
        audience=audience,
        extra_instructions=extra_instructions,
    )
    return await job_manager.generate_now(request=request, files=files)


@app.get("/question/{prompt}/{number}")
async def legacy_generate(prompt: str, number: int) -> dict:
    request = GenerationRequest(topic=prompt, number=number)
    job = await job_manager.generate_now(request=request, files=[])
    return {
        "job_id": job.id,
        "status": job.status,
        "result": job.result.parsed_response or job.result.raw_response,
        "errors": job.errors,
    }
