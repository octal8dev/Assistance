import os
import time
from dotenv import load_dotenv
from yoomoney import Quickpay, Client

load_dotenv()

YOOMONEY_TOKEN = os.getenv('YOOMONEY_TOKEN')
YOOMONEY_RECEIVER = os.getenv('YOOMONEY_RECEIVER')

def create_payment(user_id, amount: float = 10):
    # Create unique label with timestamp to avoid conflicts
    label = f"{user_id}_{int(time.time())}"
    
    quickpay = Quickpay(
        receiver=YOOMONEY_RECEIVER,
        quickpay_form="shop",
        targets="example",
        paymentType="SB",
        sum=amount,
        label=label,
        successURL="example"
    )
    return quickpay.redirected_url, label

def check_payment(label, expected_amount: float):
    try:
        client = Client(YOOMONEY_TOKEN)
        # Get recent operations without label filter first
        history = client.operation_history(records=20)
        
        # Calculate minimum amount considering 3% YooMoney commission
        min_expected_amount = expected_amount * 0.97
        
        print(f"Looking for payment - Label: {label}, Expected: {expected_amount}, Min expected (after 3% commission): {min_expected_amount}")
        
        for operation in history.operations:
            operation_label = getattr(operation, 'label', 'None')
            print(f"Checking operation: status={operation.status}, label={operation_label}, amount={operation.amount}, direction={operation.direction}")
            
            if (operation.status == 'success' and 
                hasattr(operation, 'label') and
                operation.label == label and 
                float(operation.amount) >= min_expected_amount and
                operation.direction == 'in'):
                print(f"Payment found! Label: {label}, Amount: {operation.amount}")
                return True
        
        print(f"Payment not found for label: {label}, expected amount: {expected_amount}")
        return False
    except Exception as e:
        print(f"Error checking payment: {e}")
        return False
