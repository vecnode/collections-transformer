from __future__ import annotations

import base64
import io
import logging
import threading
import traceback
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from PIL import Image
from transformers import Blip2ForConditionalGeneration, Blip2Processor

from app.core.config import app_settings as settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Blip2Config:
    """Configuration for the local Transformers BLIP-2 backend."""

    model_name: str = settings.blip2_model_name
    default_prompt: str = "Provide a detailed description of this image."
    timeout_seconds: float = 300.0
    repetition_penalty: float = 1.1


class Blip2TransformersBackend:
    """High-level wrapper around a local BLIP-2 Transformers model for image captioning."""

    def __init__(self, config: Blip2Config | None = None) -> None:
        self.config = config or Blip2Config()
        self._processor: Blip2Processor | None = None
        self._model: Blip2ForConditionalGeneration | None = None
        self._device: str | None = None
        self._dtype: Any | None = None
        self._init_lock = threading.Lock()

    @property
    def model_name(self) -> str:
        return self.config.model_name

    @property
    def processor(self) -> Blip2Processor | None:
        return self._processor

    @property
    def model(self) -> Blip2ForConditionalGeneration | None:
        return self._model

    def init(self, force_cpu: bool = False) -> None:
        """Load processor and model once, preferring CUDA if available unless forced to CPU."""
        if self._processor is not None and self._model is not None:
            return

        with self._init_lock:
            if self._processor is not None and self._model is not None:
                return

            import torch

            device = "cpu" if force_cpu else ("cuda" if torch.cuda.is_available() else "cpu")
            logger.info("Initializing BLIP-2 model '%s' on %s", self.config.model_name, device)

            processor = Blip2Processor.from_pretrained(self.config.model_name)
            model_dtype = torch.float32

            if device == "cuda":
                try:
                    model = Blip2ForConditionalGeneration.from_pretrained(
                        self.config.model_name,
                        torch_dtype=torch.float16,
                    ).to(device)
                    model_dtype = torch.float16
                    logger.info("Loaded BLIP-2 with float16 on CUDA")
                except Exception:
                    logger.warning(
                        "Failed float16 BLIP-2 load on CUDA, retrying float32",
                        exc_info=True,
                    )
                    model = Blip2ForConditionalGeneration.from_pretrained(self.config.model_name).to(device)
                    model_dtype = torch.float32
            else:
                model = Blip2ForConditionalGeneration.from_pretrained(self.config.model_name).to(device)

            model.eval()
            if device == "cuda":
                torch.cuda.empty_cache()

            self._processor = processor
            self._model = model
            self._device = device
            self._dtype = model_dtype

            logger.info("BLIP-2 model initialized successfully")

    @staticmethod
    def _decode_image(image_data: str | bytes) -> Image.Image:
        if isinstance(image_data, str):
            payload = image_data.split(",", 1)[1] if image_data.startswith("data:image") else image_data
            image_bytes = base64.b64decode(payload)
        else:
            image_bytes = image_data
        return Image.open(io.BytesIO(image_bytes))

    def _prepare_inputs(self, image: Image.Image, prompt: str | None = None) -> dict[str, Any]:
        import torch

        if self._processor is None or self._model is None or self._device is None:
            raise RuntimeError("BLIP-2 backend not initialized")

        if prompt:
            inputs = self._processor(images=image, text=prompt, return_tensors="pt")
        else:
            inputs = self._processor(images=image, return_tensors="pt")
        converted: dict[str, Any] = {}
        for key, value in inputs.items():
            if isinstance(value, torch.Tensor):
                if value.dtype.is_floating_point:
                    converted[key] = value.to(device=self._device, dtype=self._dtype)
                else:
                    converted[key] = value.to(device=self._device)
            else:
                converted[key] = value
        return converted

    def _generate_caption(self, image: Image.Image, prompt: str | None = None, max_words: int | None = None) -> str:
        import torch

        if self._model is None or self._device is None:
            raise RuntimeError("BLIP-2 backend not initialized")

        max_new_tokens = max(8, int(max_words * 1.3)) if max_words else 80
        num_beams = 5 if self._device == "cpu" else 3
        inputs = self._prepare_inputs(image, prompt)

        if self._device == "cuda":
            torch.cuda.empty_cache()

        generate_kwargs: dict[str, Any] = {
            "max_new_tokens": max_new_tokens,
            "num_beams": num_beams,
            "do_sample": False,
            "repetition_penalty": self.config.repetition_penalty,
            "length_penalty": 1.0,
            "no_repeat_ngram_size": 3,
            "early_stopping": True,
        }
        if max_new_tokens >= 120:
            generate_kwargs["min_new_tokens"] = min(max_new_tokens - 2, 80)

        with torch.no_grad():
            generated_ids = self._model.generate(**inputs, **generate_kwargs)

        if self._processor is None:
            raise RuntimeError("BLIP-2 processor not initialized")

        text = self._processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        if prompt:
            prompt_norm = prompt.strip()
            if text.startswith(prompt_norm):
                text = text[len(prompt_norm):].lstrip(" :\n\t")

        # If generation returns empty/echo-only text, retry once with greedy decoding.
        if not text:
            fallback_kwargs = {
                "max_new_tokens": max(16, min(128, max_new_tokens + 16)),
                "num_beams": 1,
                "do_sample": False,
            }
            with torch.no_grad():
                generated_ids = self._model.generate(**inputs, **fallback_kwargs)
            text = self._processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
            if prompt:
                prompt_norm = prompt.strip()
                if text.startswith(prompt_norm):
                    text = text[len(prompt_norm):].lstrip(" :\n\t")

        del generated_ids, inputs
        if self._device == "cuda":
            torch.cuda.empty_cache()

        return text

    def describe_image(self, image: str | bytes, prompt: str | None = None, max_words: int | None = None) -> str:
        """Describe one image while retaining prompt parameter for API symmetry."""
        effective_prompt = prompt

        self.init()
        image_obj = self._decode_image(image)

        try:
            return self._generate_caption(image_obj, prompt=effective_prompt, max_words=max_words)
        except Exception as exc:
            import torch

            if self._device == "cuda" and isinstance(exc, torch.cuda.OutOfMemoryError):
                logger.warning("CUDA OOM while generating BLIP-2 caption, retrying on CPU")
                self._processor = None
                self._model = None
                self._device = None
                self._dtype = None
                self.init(force_cpu=True)
                return self._generate_caption(image_obj, prompt=effective_prompt, max_words=max_words)
            raise

    def describe_images(self, images: list[str | bytes], prompt: str | None = None, max_words: int | None = None) -> list[str]:
        responses: list[str] = []
        for image_data in images:
            responses.append(self.describe_image(image=image_data, prompt=prompt, max_words=max_words))
        return responses


_backend: Blip2TransformersBackend | None = None
blip2_processor = None
blip2_model = None
blip2_model_name = None


def _get_backend() -> Blip2TransformersBackend:
    global _backend
    if _backend is None:
        _backend = Blip2TransformersBackend()
    return _backend


def _sync_legacy_globals() -> None:
    global blip2_processor, blip2_model, blip2_model_name
    backend = _get_backend()
    blip2_processor = backend.processor
    blip2_model = backend.model
    blip2_model_name = backend.model_name


def init_blip2(force_cpu: bool = False):
    """Initialize BLIP-2 model (legacy-compatible wrapper)."""
    try:
        backend = _get_backend()
        backend.init(force_cpu=force_cpu)
        _sync_legacy_globals()
    except Exception:
        logger.error("Error initializing BLIP-2 model", exc_info=True)
        raise


def get_blip2_multimodal_response(primer_message, user_message, images, max_words=None):
    """Handle multimodal image requests using the BLIP-2 Transformers backend."""
    _ = primer_message
    prompt = user_message

    try:
        backend = _get_backend()
        backend.init()
        _sync_legacy_globals()

        responses = backend.describe_images(images=images, prompt=prompt, max_words=max_words)
        response_text = responses[0] if len(responses) == 1 else "\n\n".join(
            [f"Image {idx + 1}: {text}" for idx, text in enumerate(responses)]
        )

        llm_end_time_ms = round(datetime.now().timestamp() * 1000)
        estimated_tokens = len(response_text.split()) * 1.3
        token_usage = {
            "prompt_tokens": int(estimated_tokens * 0.3),
            "completion_tokens": int(estimated_tokens * 0.7),
            "total_tokens": int(estimated_tokens),
        }

        return {
            "status": "200",
            "res": response_text,
            "end": llm_end_time_ms,
            "token": token_usage,
        }
    except Exception as exc:
        logger.error("Error in BLIP-2 multimodal response: %s", exc)
        logger.debug(traceback.format_exc())
        return {
            "status": "400",
            "error": str(exc),
        }
