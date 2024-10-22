# ZugaCloud Readme App

This document provides step-by-step instructions on how to create an AWS account, set up an S3 bucket, and create an IAM user with the appropriate permissions for your ZugaCloud app.

## Table of Contents

1. [Creating an AWS Account](#1-creating-an-aws-account)
2. [Setting Up an S3 Bucket](#2-setting-up-an-s3-bucket)
3. [Creating an IAM User](#3-creating-an-iam-user)
4. [Assigning Permissions: AmazonS3FullAccess](#4-assigning-permissions-amazons3fullaccess)
5. [Creating and Attaching Custom Inline Policies](#5-creating-and-attaching-custom-inline-policies)
6. [Modifying the Custom Inline Policy for Different Use Cases](#6-modifying-the-custom-inline-policy-for-different-use-cases)

---

### 1. Creating an AWS Account

1. Visit the [AWS Sign Up Page](https://portal.aws.amazon.com/billing/signup#/start).
2. Enter your email address and create a new AWS account by following the on-screen instructions.
3. Verify your identity via a phone number and credit card information (this is for verification purposes only; you won't be charged unless you use paid services).
4. After completing the sign-up process, log in to the [AWS Management Console](https://aws.amazon.com/console/).

---

### 2. Setting Up an S3 Bucket

1. Log in to your AWS Management Console.
2. Navigate to [**Services** > **S3**](https://s3.console.aws.amazon.com/s3/home).
3. Click on **Create Bucket**.
4. Configure your bucket settings:
   - **Bucket Name**: Choose a globally unique name, e.g., `zugaarchive`.
   - **Region**: Select a region close to your primary users or application.
5. Keep default settings unless specific configurations are required (e.g., versioning or encryption).
6. Click **Create Bucket**.

---

### 3. Creating an IAM User

1. Navigate to [**Services** > **IAM** (Identity and Access Management)](https://console.aws.amazon.com/iam/home).
2. Click on **Users** from the left sidebar.
3. Select **Add User**.
4. Set the username (e.g., `zugacloud-user`) and choose the **Access type**:
   - Select **Programmatic access** if the user will interact with AWS programmatically (e.g., via the CLI or SDK).
   - Select **AWS Management Console access** if the user needs access to the AWS Console.
5. Click **Next: Permissions**.

---

### 4. Assigning Permissions: AmazonS3FullAccess

1. On the **Permissions** page, click on **Attach policies directly**.
2. Search for `AmazonS3FullAccess` in the list of available policies.
3. Check the box next to `AmazonS3FullAccess` to grant the user full access to S3.
4. Click **Next: Tags**, add any necessary tags, and then click **Next: Review**.
5. Review the user configuration and click **Create User**.

---

### 5. Creating and Attaching Custom Inline Policies

After creating the user with `AmazonS3FullAccess`, you can define custom permissions based on specific needs using inline policies. This section covers adding an inline policy to restrict access to a specific bucket and its objects.

1. Go to [**Services** > **IAM** > **Users**](https://console.aws.amazon.com/iam/home#/users).
2. Select the newly created user (e.g., `zugacloud-user`).
3. Click on the **Permissions** tab.
4. Scroll down and click **Add inline policy**.
5. Select the **JSON** tab and paste the following JSON code to define the custom policy:

   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "s3:ListBucket",
                   "s3:GetObject"
               ],
               "Resource": [
                   "arn:aws:s3:::zugaarchive",
                   "arn:aws:s3:::zugaarchive/*"
               ]
           }
       ]
   }
   ```
6. Click Review Policy
7. Enter a name for the policy (e.g., ZugaCloudCustomPolicy) and click Create Policy.

---

### 6. Modifying the Custom Inline Policy for Different Use Cases

The provided custom inline policy restricts the user to only list and read objects in the zugaarchive bucket. If you want to modify this policy for different scenarios, you can adjust the Action and Resource fields accordingly.

#### Adjusting Permissions Based on Actions

- `s3:ListBucket`: Allows the user to list the objects in the specified bucket.
- `s3:GetObject`: Allows the user to read the contents of the objects in the specified bucket.
- Add or remove actions as needed, such as `s3:PutObject` (to upload new objects) or `s3:DeleteObject` (to delete objects).

Example: If you want the user to also upload files to the bucket, update the Action field like this:

```json
"Action": [
    "s3:ListBucket",
    "s3:GetObject",
    "s3:PutObject"
]
```

#### Modifying the Resource Field

- The Resource field specifies which S3 bucket and objects the policy applies to.
- Update the bucket name if using a different one. For example, to allow access to a bucket named mybucket and its contents, change the Resource field like this:

```json
"Resource": [
    "arn:aws:s3:::mybucket",
    "arn:aws:s3:::mybucket/*"
]
```

#### Restricting to Specific Folders

To further restrict access to a specific folder in the bucket, modify the Resource field with the folder path. For example, to limit access to a folder named data:

```json
"Resource": [
    "arn:aws:s3:::mybucket/data",
    "arn:aws:s3:::mybucket/data/*"
]
```

#### Setting Conditions

You can add conditions to control access based on factors such as IP address, time of day, or the presence of certain tags on objects. For example, to restrict access to a specific IP range, add a Condition block:

```json
"Condition": {
    "IpAddress": {
        "aws:SourceIp": "203.0.113.0/24"
    }
}
```
