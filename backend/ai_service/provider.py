import json
import os
import urllib.error
import urllib.request


class GeminiProvider:
    name = 'gemini'
    RESPONSE_MIME_TYPE_ERROR = 'responseMimeType'

    def __init__(
        self,
        api_key: str,
        model: str = 'gemini-2.5-flash',
        api_version: str = 'v1beta',
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.api_version = api_version

    def _build_url(self) -> str:
        return (
            f'https://generativelanguage.googleapis.com/{self.api_version}/models/'
            f'{self.model}:generateContent?key={self.api_key}'
        )

    def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_output_tokens: int = 200,
    ) -> str:
        url = self._build_url()
        generation_config = self._build_generation_config(
            temperature,
            max_output_tokens,
        )
        payload = {
            'contents': [
                {
                    'parts': [
                        {
                            'text': prompt,
                        }
                    ]
                }
            ],
            'generationConfig': generation_config,
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )

        data = self._send_request(request)

        candidates = data.get('candidates', [])
        if not candidates:
            raise RuntimeError('No candidates returned by Gemini.')

        parts = candidates[0].get('content', {}).get('parts', [])
        if not parts:
            raise RuntimeError('No content returned by Gemini.')

        return parts[0].get('text', '').strip()

    def generate_json(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_output_tokens: int = 2000,
    ):
        data = self._generate_json_response(
            prompt,
            temperature,
            max_output_tokens,
            use_json_mode=True,
        )

        candidates = data.get('candidates', [])
        if not candidates:
            raise RuntimeError('No candidates returned by Gemini.')

        parts = candidates[0].get('content', {}).get('parts', [])
        if not parts:
            raise RuntimeError('No content returned by Gemini.')

        raw = parts[0].get('text', '').strip()
        if not raw:
            raise RuntimeError('Empty JSON response from Gemini.')

        try:
            return self._parse_json(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError('Invalid JSON returned by Gemini.') from exc

    def _generate_json_response(
        self,
        prompt: str,
        temperature: float,
        max_output_tokens: int,
        use_json_mode: bool,
    ) -> dict:
        try:
            return self._send_request(
                self._build_json_request(
                    prompt,
                    temperature,
                    max_output_tokens,
                    use_json_mode=use_json_mode,
                )
            )
        except RuntimeError as exc:
            if use_json_mode and self.RESPONSE_MIME_TYPE_ERROR in str(exc):
                return self._generate_json_response(
                    prompt,
                    temperature,
                    max_output_tokens,
                    use_json_mode=False,
                )
            raise

    def _build_json_request(
        self,
        prompt: str,
        temperature: float,
        max_output_tokens: int,
        use_json_mode: bool = True,
    ) -> urllib.request.Request:
        generation_config = self._build_generation_config(
            temperature,
            max_output_tokens,
        )
        if use_json_mode:
            generation_config['responseMimeType'] = 'application/json'

        payload = {
            'contents': [
                {
                    'parts': [
                        {
                            'text': prompt,
                        }
                    ]
                }
            ],
            'generationConfig': generation_config,
        }

        return urllib.request.Request(
            self._build_url(),
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )

    def _build_generation_config(
        self,
        temperature: float,
        max_output_tokens: int,
    ) -> dict:
        generation_config = {
            'temperature': temperature,
            'maxOutputTokens': max_output_tokens,
        }

        thinking_budget = os.getenv('GEMINI_THINKING_BUDGET', '').strip()
        if not thinking_budget and self.model.startswith('gemini-2.5-flash'):
            thinking_budget = '0'

        if thinking_budget:
            try:
                generation_config['thinkingConfig'] = {
                    'thinkingBudget': int(thinking_budget),
                }
            except ValueError:
                pass

        return generation_config

    @staticmethod
    def _send_request(request: urllib.request.Request) -> dict:
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode('utf-8') if exc.fp else str(exc)
            raise RuntimeError(detail) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(str(exc)) from exc

    @staticmethod
    def _parse_json(raw: str):
        cleaned = raw.strip()

        if cleaned.startswith('```'):
            cleaned = cleaned.strip('`').strip()
            if cleaned.lower().startswith('json'):
                cleaned = cleaned[4:].strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        start = min(
            (idx for idx in (cleaned.find('['), cleaned.find('{')) if idx != -1),
            default=-1,
        )
        end = max(cleaned.rfind(']'), cleaned.rfind('}'))
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start : end + 1])

        return json.loads(cleaned)


def get_default_provider():
    api_key = os.getenv('GEMINI_API_KEY', '').strip()
    if not api_key:
        return None
    model = os.getenv('GEMINI_MODEL', '').strip() or 'gemini-2.5-flash'
    api_version = os.getenv('GEMINI_API_VERSION', '').strip() or 'v1beta'
    return GeminiProvider(api_key=api_key, model=model, api_version=api_version)


def generate_with_fallback(
    prompt: str,
    fallback_text: str,
    temperature: float = 0.3,
    max_output_tokens: int = 200,
):
    provider = get_default_provider()
    if not provider:
        return fallback_text, 'fallback', True

    try:
        text = provider.generate(
            prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        if not text:
            return fallback_text, 'fallback', True
        return text, provider.name, False
    except RuntimeError:
        return fallback_text, 'fallback', True
