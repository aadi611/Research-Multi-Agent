
import base64
import mimetypes
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from openai.types.chat import ChatCompletion

from .base_agent import BaseAgent


class MultiModalResearchAgent(BaseAgent):
    """
    Multimodal research agent.

    Supports:
    - Remote image URLs
    - Local image files
    - Multiple images per research request
    - Text-only research when no images are supplied
    """

    SUPPORTED_FORMATS = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }

    DEFAULT_MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20 MB
    DEFAULT_MAX_IMAGES = 10
    DEFAULT_MAX_TOKENS = 2000

    def __init__(
        self,
        *args: Any,
        max_image_size: int = DEFAULT_MAX_IMAGE_SIZE,
        max_images: int = DEFAULT_MAX_IMAGES,
        **kwargs: Any,
    ) -> None:

        super().__init__(*args, **kwargs)

        self.max_image_size = max_image_size
        self.max_images = max_images

        if max_image_size <= 0:
            raise ValueError("Maximum image size must be positive.")

        if max_images <= 0:
            raise ValueError("Maximum image count must be positive.")

    # ---------------------------------------------------------
    # Image Validation
    # ---------------------------------------------------------

    @staticmethod
    def _validate_image_url(url: str) -> str:
        """Validate remote image URL structure."""

        if not isinstance(url, str) or not url.strip():
            raise ValueError("Image URL cannot be empty.")

        parsed = urlparse(url.strip())

        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"Invalid image URL: {url}")

        return url.strip()

    def _validate_image_path(self, path: Path) -> str:
        """Validate local image file."""

        if not path.exists():
            raise FileNotFoundError(
                f"Image file not found: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Image path is not a file: {path}"
            )

        suffix = path.suffix.lower()

        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported image format: {suffix}"
            )

        if path.stat().st_size > self.max_image_size:
            raise ValueError(
                f"Image exceeds maximum size of "
                f"{self.max_image_size // (1024 * 1024)} MB: {path}"
            )

        return self.SUPPORTED_FORMATS[suffix]

    # ---------------------------------------------------------
    # Image Processing
    # ---------------------------------------------------------

    def _encode_local_image(self, path_str: str) -> dict:
        """
        Convert a local image into an OpenAI-compatible
        base64 data URL.
        """

        path = Path(path_str)

        media_type = self._validate_image_path(path)

        encoded = base64.b64encode(
            path.read_bytes()
        ).decode("utf-8")

        data_url = (
            f"data:{media_type};base64,{encoded}"
        )

        return {
            "type": "image_url",
            "image_url": {
                "url": data_url,
            },
        }

    def _build_image_content(
        self,
        image_urls: list[str] | None = None,
        image_paths: list[str] | None = None,
    ) -> list[dict]:

        content = []

        image_urls = image_urls or []
        image_paths = image_paths or []

        total_images = len(image_urls) + len(image_paths)

        if total_images > self.max_images:
            raise ValueError(
                f"Maximum {self.max_images} images allowed. "
                f"Received {total_images}."
            )

        # Remote images
        for url in image_urls:
            validated_url = self._validate_image_url(url)

            content.append({
                "type": "image_url",
                "image_url": {
                    "url": validated_url,
                },
            })

        # Local images
        for path in image_paths:
            content.append(
                self._encode_local_image(path)
            )

        return content

    # ---------------------------------------------------------
    # Prompt Construction
    # ---------------------------------------------------------

    @staticmethod
    def _build_research_prompt(
        query: str,
        has_visuals: bool,
    ) -> str:

        if has_visuals:
            return f"""
You are an expert multimodal research analyst.

Analyze the provided visual content in the context
of the following research topic:

Research Topic:
{query}

Your analysis must include:

1. Visual Description
   Describe what each image represents.

2. Key Observations
   Identify important data, patterns, trends,
   relationships, and anomalies.

3. Research Relevance
   Explain how the visual information relates
   to the research question.

4. Evidence and Interpretation
   Separate directly observable information
   from your interpretations.

5. Limitations
   Identify missing information, uncertainty,
   and potential visual interpretation errors.

6. Research Insights
   Explain the implications of the visual evidence.
"""

        return f"""
You are an expert academic research analyst.

Research Topic:
{query}

Provide a comprehensive overview covering:

1. Fundamental concepts
2. Important research findings
3. Common diagrams and visual representations
4. Important datasets and measurements
5. Current research directions
6. Open research questions
"""

    # ---------------------------------------------------------
    # Research Execution
    # ---------------------------------------------------------

    def research(
        self,
        query: str,
        image_urls: list[str] | None = None,
        image_paths: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:

        query = self._validate_query(query)

        # Prepare images
        image_content = self._build_image_content(
            image_urls=image_urls,
            image_paths=image_paths,
        )

        has_visuals = bool(image_content)

        # Construct multimodal message
        prompt = self._build_research_prompt(
            query=query,
            has_visuals=has_visuals,
        )

        content = [
            *image_content,
            {
                "type": "text",
                "text": prompt,
            },
        ]

        # Execute model request
        response = self._get_completion(
            messages=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
            max_completion_tokens=kwargs.get(
                "max_completion_tokens",
                self.DEFAULT_MAX_TOKENS,
            ),
        )

        return {
            **self._get_metadata(),
            "query": query,
            "findings": self._get_text(response),
            "has_visual_content": has_visuals,
            "image_count": len(image_content),
            "image_sources": {
                "urls": len(image_urls or []),
                "local_files": len(image_paths or []),
            },
        }
