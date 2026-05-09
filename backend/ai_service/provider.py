import json
import os
import urllib.error
import urllib.request


class GeminiProvider:
    name = 'gemini'

    def __init__(self, api_key: str, model: str = 'gemini-1.5-flash') -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str) -> str:
        url = (
            'https://generativelanguage.googleapis.com/v1beta/models/'
            f'{self.model}:generateContent?key={self.api_key}'
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
            'generationConfig': {
                'temperature': 0.4,
                'maxOutputTokens': 200,
            },
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                data = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode('utf-8') if exc.fp else str(exc)
            raise RuntimeError(detail) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(str(exc)) from exc

        candidates = data.get('candidates', [])
        if not candidates:
            raise RuntimeError('No candidates returned by Gemini.')

        parts = candidates[0].get('content', {}).get('parts', [])
        if not parts:
            raise RuntimeError('No content returned by Gemini.')

        return parts[0].get('text', '').strip()


def get_default_provider():
    api_key = os.getenv('GEMINI_API_KEY', '').strip()
    if not api_key:
        return None
    return GeminiProvider(api_key=api_key)


def generate_with_fallback(prompt: str, fallback_text: str):
    provider = get_default_provider()
    if not provider:
        return fallback_text, 'fallback', True

    try:
        text = provider.generate(prompt)
        if not text:
            return fallback_text, 'fallback', True
        return text, provider.name, False
    except RuntimeError:
        return fallback_text, 'fallback', True
