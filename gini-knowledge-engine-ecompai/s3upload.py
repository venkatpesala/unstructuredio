from fastapi import FastAPI, File, UploadFile, HTTPException
import boto3
from botocore.exceptions import NoCredentialsError

app = FastAPI()

# Initialize the S3 client
s3_client = boto3.client('s3')

# Replace 'your-s3-bucket-name' with your actual S3 bucket name
BUCKET_NAME = 'zapier-test-123'

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "query": q}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Read the file contents
        file_contents = await file.read()
        
        print(f"Uploading {file.filename}")

        # Upload the file to S3
        s3_client.put_object(Bucket=BUCKET_NAME, Key=file.filename, Body=file_contents)

        return {"message": f"File '{file.filename}' uploaded successfully"}

    except NoCredentialsError:
        raise HTTPException(status_code=401, detail="AWS credentials not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
