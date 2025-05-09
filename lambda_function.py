import boto3
import json
import urllib.parse
def lambda_handler(event, context):
    # Initialize AWS clients
    s3_client = boto3.client('s3')
    rekognition_client = boto3.client('rekognition')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('vehicleNumberPlates') # Replace with your DynamoDB table name

    # Get S3 bucket and object key
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])

    try:
        # Use Rekognition to detect text (including license plates)
        response = rekognition_client.detect_text(
            Image={
               'S3Object': {
                   'Bucket': bucket_name,
                   'Name': object_key
               } 
            }
        )

        # Filter detected text for potential license plate numbers
        detected_text = [text['DetectedText'] for text in response['TextDetections'] if text['Type'] == 'LINE']

        # Optionally: Apply regex or heuristics to identify plate patterns
        # For example: Common license plates (alphanumeric, 6-10 chars)
        import re
        plate_candidates = [t for t in detected_text if re.match(r'^[A-Z0-9\-]{6,12}$', t)]

        # Save to DynamoDB
        table.put_item(
            Item={
                'ImageName': object_key,
                'DetectedPlates': plate_candidates,
                'AllDetectedText': detected_text
            }
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'License plate detection completed successfully',
                'detectedPlates': plate_candidates
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error processing image')
        }



