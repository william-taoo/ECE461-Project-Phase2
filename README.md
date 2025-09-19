# ECE461 Project - Fall 2025

## Group Members:
- Akash Kumar
- Alexis Haas
- Ishana Thakre

## Project Setup:
1. Clone the repository
2. Run `pip install -r requirements.txt` to install dependencies

## Testing:
Run `python -m pytest` in the terminal to execute the test suite

## AWS Model Deployment (for developers):
1. Ensure you have AWS CLI configured with appropriate permissions
2. Go to the AWS SageMaker AI console
3. Search for "LLama 3 8B Instruct" under JumpStart->Foundational Models
4. Open the model in SageMaker Studio
5. Deploy the model with endpoint: "jumpstart-dft-meta-textgeneration-l-20250919-201634"
6. When done, delete the endpoint to avoid incurring costs