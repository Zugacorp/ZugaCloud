/**
 * Test script for BucketSelector component
 * This script tests the frontend API endpoints related to bucket selection
 * and verifies that the application can properly detect and select Storj buckets.
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');

// Configuration
const API_BASE_URL = 'http://localhost:5000'; // Default local API URL
const LOGS_DIR = path.join(__dirname, '..', 'logs');

// Ensure logs directory exists
if (!fs.existsSync(LOGS_DIR)) {
  fs.mkdirSync(LOGS_DIR, { recursive: true });
}

// Clear previous log file
const LOG_FILE = path.join(LOGS_DIR, 'bucket_selector_test.log');
if (fs.existsSync(LOG_FILE)) {
  fs.unlinkSync(LOG_FILE);
}

// Configure logging
function log(message) {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] ${message}`;
  
  // Log to console
  console.log(logMessage);
  
  // Log to file
  fs.appendFileSync(LOG_FILE, logMessage + '\n');
}

// Helper functions
async function fetchConfig() {
  log('Fetching configuration from API...');
  try {
    const response = await axios.get(`${API_BASE_URL}/api/config`);
    
    // Log configuration (but mask secrets)
    const config = { ...response.data };
    if (config.storj_secret_key) {
      config.storj_secret_key = '***masked***';
    }
    if (config.aws_secret_access_key) {
      config.aws_secret_access_key = '***masked***';
    }
    
    log(`Configuration received: ${JSON.stringify(config, null, 2)}`);
    return response.data;
  } catch (error) {
    log(`Error fetching configuration: ${error.message}`);
    if (error.response) {
      log(`Response status: ${error.response.status}`);
      log(`Response data: ${JSON.stringify(error.response.data)}`);
    }
    return null;
  }
}

async function listBuckets(provider = null) {
  const endpoint = provider 
    ? `${API_BASE_URL}/api/buckets?provider=${provider}` 
    : `${API_BASE_URL}/api/buckets`;
    
  log(`Fetching buckets from API (provider: ${provider || 'default'})...`);
  
  try {
    const response = await axios.get(endpoint);
    log(`Buckets received: ${JSON.stringify(response.data, null, 2)}`);
    return response.data;
  } catch (error) {
    log(`Error fetching buckets: ${error.message}`);
    if (error.response) {
      log(`Response status: ${error.response.status}`);
      log(`Response data: ${JSON.stringify(error.response.data)}`);
    }
    return null;
  }
}

async function checkStorjConfig(config) {
  if (!config) return false;
  
  const hasStorjKeys = !!(config.storj_access_key && config.storj_secret_key);
  log(`Storj configuration check: ${hasStorjKeys ? 'VALID' : 'MISSING'}`);
  
  if (hasStorjKeys) {
    log(`Storj access key: ${config.storj_access_key.substring(0, 4)}...`);
    log(`Storj secret key: Present (masked)`);
  } else {
    log('Storj credentials are missing in the configuration');
  }
  
  return hasStorjKeys;
}

async function checkAWSConfig(config) {
  if (!config) return false;
  
  const hasAWSKeys = !!(config.aws_access_key_id && config.aws_secret_access_key);
  log(`AWS configuration check: ${hasAWSKeys ? 'VALID' : 'MISSING'}`);
  
  if (hasAWSKeys) {
    log(`AWS access key ID: ${config.aws_access_key_id.substring(0, 4)}...`);
    log(`AWS secret access key: Present (masked)`);
    log(`AWS region: ${config.aws_region || 'Not specified'}`);
  } else {
    log('AWS credentials are missing in the configuration');
  }
  
  return hasAWSKeys;
}

async function checkConfigContext(config) {
  if (!config) return false;
  
  // Check which storage provider is set in the config
  const provider = config.storage_provider;
  log(`Current storage provider in config: ${provider || 'Not set'}`);
  
  // Check if the config has a selected bucket
  const selectedBucket = config.bucket_name;
  log(`Current selected bucket in config: ${selectedBucket || 'None'}`);
  
  return { provider, selectedBucket };
}

// Main test function
async function runTests() {
  log('=== Starting BucketSelector Testing ===');
  
  // Step 1: Get the current configuration
  const config = await fetchConfig();
  if (!config) {
    log('ERROR: Failed to fetch configuration. Tests cannot proceed.');
    return;
  }
  
  // Step 2: Check configuration values
  log('\n=== Checking Configuration ===');
  const hasStorjConfig = await checkStorjConfig(config);
  const hasAWSConfig = await checkAWSConfig(config);
  const { provider, selectedBucket } = await checkConfigContext(config);
  
  if (!hasStorjConfig && !hasAWSConfig) {
    log('ERROR: Neither Storj nor AWS credentials are configured. Tests cannot proceed.');
    return;
  }
  
  // Step 3: Test bucket listing with default provider
  log('\n=== Testing Default Bucket Listing ===');
  const defaultBuckets = await listBuckets();
  
  if (!defaultBuckets) {
    log('ERROR: Failed to fetch buckets with default provider.');
  } else {
    log(`Found ${defaultBuckets.length} buckets with default provider.`);
    
    // Check for zugacloud bucket
    const zugacloudBucket = defaultBuckets.find(bucket => bucket.name === 'zugacloud');
    if (zugacloudBucket) {
      log('SUCCESS: Found "zugacloud" bucket in the default bucket list.');
    } else {
      log('NOTE: "zugacloud" bucket was not found in the default bucket list.');
    }
  }
  
  // Step 4: Test bucket listing with specific providers
  if (hasStorjConfig) {
    log('\n=== Testing Storj Bucket Listing ===');
    const storjBuckets = await listBuckets('storj');
    
    if (!storjBuckets) {
      log('ERROR: Failed to fetch Storj buckets.');
    } else {
      log(`Found ${storjBuckets.length} Storj buckets.`);
      
      // Check for zugacloud bucket
      const zugacloudBucket = storjBuckets.find(bucket => bucket.name === 'zugacloud');
      if (zugacloudBucket) {
        log('SUCCESS: Found "zugacloud" bucket in Storj.');
      } else {
        log('WARNING: "zugacloud" bucket was not found in Storj.');
      }
    }
  }
  
  if (hasAWSConfig) {
    log('\n=== Testing AWS Bucket Listing ===');
    const awsBuckets = await listBuckets('aws');
    
    if (!awsBuckets) {
      log('ERROR: Failed to fetch AWS buckets.');
    } else {
      log(`Found ${awsBuckets.length} AWS buckets.`);
    }
  }
  
  // Step 5: Diagnostic summary
  log('\n=== Diagnostic Summary ===');
  
  if (hasStorjConfig) {
    if (provider === 'storj') {
      log('✓ Storj is correctly set as the current storage provider.');
    } else {
      log('⚠ Storj credentials are present but not set as the current provider.');
      log(`   Current provider is: ${provider || 'Not set'}`);
    }
  }
  
  if (hasAWSConfig) {
    if (provider === 'aws') {
      log('✓ AWS is correctly set as the current storage provider.');
    } else if (!hasStorjConfig) {
      log('⚠ AWS credentials are present but not set as the current provider.');
      log(`   Current provider is: ${provider || 'Not set'}`);
    }
  }
  
  if (selectedBucket) {
    log(`✓ A bucket (${selectedBucket}) is selected in the configuration.`);
  } else {
    log('⚠ No bucket is currently selected in the configuration.');
  }
  
  log('\n=== Testing Complete ===');
  log(`Detailed log has been saved to: ${LOG_FILE}`);
}

// Run the tests
runTests().catch(error => {
  log(`Unhandled error in test execution: ${error.message}`);
  log(error.stack);
}); 