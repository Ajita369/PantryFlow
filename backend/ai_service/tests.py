import json
from unittest.mock import patch

from django.test import SimpleTestCase

from .provider import GeminiProvider


class GeminiProviderTests(SimpleTestCase):
    def test_generate_json_retries_without_response_mime_type_when_unsupported(self):
        provider = GeminiProvider(api_key='test-key')
        response = {
            'candidates': [
                {
                    'content': {
                        'parts': [
                            {
                                'text': '[{"title": "Rice bowl"}]',
                            }
                        ]
                    }
                }
            ]
        }

        with patch.object(
            provider,
            '_send_request',
            side_effect=[
                RuntimeError(
                    'Invalid JSON payload received. Unknown name "responseMimeType" '
                    'at generation_config: Cannot find field.'
                ),
                response,
            ],
        ) as send_request:
            data = provider.generate_json('Return JSON')

        first_request = send_request.call_args_list[0].args[0]
        second_request = send_request.call_args_list[1].args[0]
        first_payload = json.loads(first_request.data.decode('utf-8'))
        second_payload = json.loads(second_request.data.decode('utf-8'))

        self.assertEqual(data, [{'title': 'Rice bowl'}])
        self.assertEqual(send_request.call_count, 2)
        self.assertEqual(
            first_payload['generationConfig']['responseMimeType'],
            'application/json',
        )
        self.assertNotIn('responseMimeType', second_payload['generationConfig'])
