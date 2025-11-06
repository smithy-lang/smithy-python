# smithy-testing

This package provides generated test clients used to verify functionality in tools and libraries built with Smithy.


## Features
- **Generated Test Clients** - Real smithy-python clients for testing.
- **Test Fixtures** - Pytest fixtures for common testing scenarios.


## Test Clients

### 1. SmithyKitchenSink (Generic Smithy Client)
- **Purpose**: Test core smithy-python functionality (retries, request/response pipeline, serde)
- **Auth**: HTTP Basic Auth
- **Use Cases**: Core smithy functionality, protocol testing, generic client behavior

### 2. AwsKitchenSink (AWS Client)  
- **Purpose**: Test AWS-specific functionality (SigV4 auth, credentials, endpoints)
- **Auth**: SigV4
- **Use Cases**: AWS authentication, credential resolution, AWS retry behavior


## Quick Start

### Basic Functional Test
```python
# In smithy-kitchen-sink/tests/

from smithy_core.retries import SimpleRetryStrategy
from smithy_http.testing import MockHTTPClient
from ..codegen.smithy_kitchen_sink.client import SmithyKitchenSink
from ..codegen.smithy_kitchen_sink.config import Config
from ..codegen.smithy_kitchen_sink.models import GetItemInput


async def test_simple_retry():
    # Set up mock responses
    http_client = MockHTTPClient()
    http_client.add_response(
        status=500, 
        headers=[("X-Amzn-Errortype", "InternalError")], 
        body=b'{"message": "server error"}'
    )
    http_client.add_response(
        status=500, 
        headers=[("X-Amzn-Errortype", "InternalError")], 
        body=b'{"message": "server error"}'
    )
    http_client.add_response(200, body=b'{"message": "success"}')
    
    # Create client with mock transport
    config = Config(
        transport=http_client,
        endpoint_uri="https://test.example.com",
        retry_strategy=SimpleRetryStrategy(max_attempts=3)
    )
    client = SmithyKitchenSink(config=config)
    
    response = await client.get_item(GetItemInput(id="test-123"))
    
    assert http_client.call_count == 3
    assert response.message == "success"
```

## Development

### Regenerating Test Clients

After modifying Smithy models, regenerate the clients:
```
python src/smithy_testing/internal/generate_clients.py
```

### Test Organization                                                                                                                                                                                            
Tests live in each client's directory:                                                                                                                                                                           
- `smithy-kitchen-sink/tests/`                                                                                                                                                                        
- `aws-kitchen-sink/tests/`   


### Adding New Test Scenarios

To add new operations or traits:
1. Edit the Smithy model files (`model/main.smithy`)
2. Update `smithy-build.json` if needed
3. Regenerate clients using the script above
4. Add tests using the new operations
