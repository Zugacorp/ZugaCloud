/**
 * Test script for Storj auto-detection functionality
 * This script tests whether the frontend can automatically detect and use Storj credentials.
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');

// Configuration
const API_BASE_URL = 'http://localhost:5000';
const LOGS_DIR = path.join(__dirname, '..', 'logs');

// Ensure logs directory exists
if (!fs.existsSync(LOGS_DIR)) {
  fs.mkdirSync(LOGS_DIR, { recursive: true });
}

// Clear previous log file
const LOG_FILE = path.join(LOGS_DIR, 'storj_auto_detection_test.log');
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
  log('Fetching current configuration...');
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
    
    log(`Current configuration: ${JSON.stringify(config, null, 2)}`);
    return response.data;
  } catch (error) {
    log(`Error fetching configuration: ${error.message}`);
    return null;
  }
}

async function updateConfig(configUpdate) {
  log(`Updating configuration: ${JSON.stringify(configUpdate, null, 2)}`);
  try {
    const response = await axios.post(`${API_BASE_URL}/api/config`, configUpdate);
    log('Configuration updated successfully');
    return response.data;
  } catch (error) {
    log(`Error updating configuration: ${error.message}`);
    return null;
  }
}

async function testStorjAutoDetection() {
  log('=== Testing Storj Auto-Detection ===');
  
  // Step 1: Fetch current config
  const originalConfig = await fetchConfig();
  if (!originalConfig) {
    log('ERROR: Could not fetch original configuration. Test cannot proceed.');
    return false;
  }
  
  // Save original provider to restore later
  const originalProvider = originalConfig.storage_provider;
  const originalBucket = originalConfig.bucket_name;
  log(`Original storage provider: ${originalProvider || 'Not set'}`);
  log(`Original bucket: ${originalBucket || 'Not set'}`);
  
  // Step 2: Check if Storj credentials are present
  const hasStorjCredentials = !!(originalConfig.storj_access_key && originalConfig.storj_secret_key);
  if (!hasStorjCredentials) {
    log('ERROR: Storj credentials are not present in the configuration. Test cannot proceed.');
    return false;
  }
  
  // Step 3: Reset provider to AWS 
  log('Setting storage provider to "aws" to test auto-detection...');
  await updateConfig({ storage_provider: 'aws' });
  
  // Verify the change
  const updatedConfig = await fetchConfig();
  if (!updatedConfig || updatedConfig.storage_provider !== 'aws') {
    log('ERROR: Failed to update storage provider to "aws".');
    // Try to restore original settings
    await updateConfig({ storage_provider: originalProvider, bucket_name: originalBucket });
    return false;
  }
  
  // Step 4: Simulate page reload by fetching config again (testing if the backend detects Storj)
  log('Simulating page reload to test if backend auto-detects Storj credentials...');
  const reloadedConfig = await fetchConfig();
  
  if (!reloadedConfig) {
    log('ERROR: Failed to fetch configuration after simulated reload.');
    // Try to restore original settings
    await updateConfig({ storage_provider: originalProvider, bucket_name: originalBucket });
    return false;
  }
  
  // Step 5: Check if provider was auto-switched to Storj
  const autoDetectionWorked = reloadedConfig.storage_provider === 'storj';
  
  if (autoDetectionWorked) {
    log('SUCCESS: The system automatically detected Storj credentials and switched the provider!');
  } else {
    log(`WARNING: Auto-detection did not work. Provider is still: ${reloadedConfig.storage_provider}`);
  }
  
  // Step 6: Test bucket auto-selection for "zugacloud"
  log('Testing if "zugacloud" bucket is automatically selected...');
  
  // Fetch buckets using the Storj provider
  try {
    const response = await axios.get(`${API_BASE_URL}/api/buckets?provider=storj`);
    const buckets = response.data;
    
    log(`Found ${buckets.length} Storj buckets`);
    
    // Check if zugacloud bucket exists
    const zugacloudBucket = buckets.find(bucket => bucket.name === 'zugacloud');
    if (zugacloudBucket) {
      log('Found "zugacloud" bucket in Storj buckets list');
      
      // Check if it was auto-selected
      if (reloadedConfig.bucket_name === 'zugacloud') {
        log('SUCCESS: "zugacloud" bucket was automatically selected!');
      } else {
        log(`WARNING: "zugacloud" bucket was not auto-selected. Selected bucket: ${reloadedConfig.bucket_name || 'None'}`);
      }
    } else {
      log('WARNING: "zugacloud" bucket was not found in Storj buckets list');
    }
  } catch (error) {
    log(`Error fetching Storj buckets: ${error.message}`);
  }
  
  // Step 7: Restore original configuration
  log('Restoring original configuration...');
  await updateConfig({ storage_provider: originalProvider, bucket_name: originalBucket });
  
  // Verify restoration
  const restoredConfig = await fetchConfig();
  if (restoredConfig && restoredConfig.storage_provider === originalProvider && 
      restoredConfig.bucket_name === originalBucket) {
    log('Original configuration restored successfully');
  } else {
    log('WARNING: Failed to restore original configuration');
  }
  
  // Test summary
  log('\n=== Test Summary ===');
  log(`Storj credentials present: ${hasStorjCredentials ? 'Yes' : 'No'}`);
  log(`Auto-detection of Storj provider: ${autoDetectionWorked ? 'Working' : 'Not working'}`);
  log(`Log file: ${LOG_FILE}`);
  
  return autoDetectionWorked;
}

// Run the test
testStorjAutoDetection().then(result => {
  log(`Test completed with result: ${result ? 'PASSED' : 'FAILED'}`);
}).catch(error => {
  log(`Unhandled error in test execution: ${error.message}`);
  log(error.stack);
}); 