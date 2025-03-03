# ZugaCloud Testing

This directory contains tests for the ZugaCloud application, with a focus on Storj integration testing.

## Test Structure

The tests are organized into the following categories:

- **Environment Tests**: Verify that the necessary environment variables and configuration files are set up correctly.
- **Connection Tests**: Test direct connections to Storj using different configurations.
- **Client Tests**: Test the `StorjClient` class implementation.
- **Frontend Tests**: Test frontend components like the bucket selector.
- **Server Tests**: Test the API server functionality.

## Test Runner

A test runner script is provided to make it easier to run and manage tests. The test runner organizes tests by category, runs them, and saves the output to log files.

### Usage

```bash
# List all available tests
python tests/run_tests.py --list

# Run all tests
python tests/run_tests.py

# Run specific test categories
python tests/run_tests.py --categories env connection

# Run tests without saving output
python tests/run_tests.py --no-save
```

### Test Results

Test results are saved to the `tests/results` directory by default. Each test run creates a log file with the test name and timestamp.

## Manual Testing

You can also run individual tests manually:

```bash
# Run environment test
python tests/aws/check_storj_env.py

# Run connection test
python tests/aws/test_direct_storj.py

# Run client test
python tests/aws/test_storj_client.py

# Run frontend test
node tests/frontend/test_bucket_selector.js

# Run server test
python tests/simple_server.py
```

## Test Descriptions

### Environment Tests

- `check_storj_env.py`: Checks if the necessary Storj environment variables are set.

### Connection Tests

- `test_direct_storj.py`: Tests direct connection to Storj using different addressing styles and configurations.
- `test_direct_bucket.py`: Tests direct access to specific Storj buckets.
- `test_head_bucket.py`: Tests if specific buckets exist using the `head_bucket` operation.

### Client Tests

- `test_storj_client.py`: Tests the `StorjClient` class implementation.

### Frontend Tests

- `test_bucket_selector.js`: Tests the bucket selector component.
- `test_storj_auto_detection.js`: Tests automatic detection of Storj credentials.

### Server Tests

- `simple_server.py`: A simple Flask server that provides the necessary API endpoints for testing.

## Troubleshooting

If you encounter issues with the tests, check the following:

1. Make sure the necessary environment variables are set in `backend/.env`.
2. Verify that the Storj credentials are correct.
3. Check if the Storj bucket exists and is accessible.
4. Ensure that the necessary dependencies are installed.

## Adding New Tests

To add a new test:

1. Create a new test file in the appropriate directory.
2. Add the test file to the `TEST_CATEGORIES` dictionary in `run_tests.py`.
3. Update this README with a description of the new test. 