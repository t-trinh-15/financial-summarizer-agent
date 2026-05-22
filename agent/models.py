'''
Objective: Pydantic models that define the shape of the agent's output. 
The forms that LLM has to fill out.'''

from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

class Transaction(str,Enum):
    PURCHASE = "purchase"
    REFUND = "refund"
    FEE = "fee"
    TRANSFER = "transfer"
    UNKNOWN = "unknown"
    
class Confidence(str,Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    
class TranslatedTransaction(BaseModel):
    '''A transaction that has been translated from the original bank statement into a plain English description.'''
    
    merchant: str = Field(default=None, 
                          description="The name of the merchant or payee involved in the transaction. For example: Starbucks, CVS, Amazon.")
    
    amount: Optional[Decimal] = Field(
        default=None,
        description="The amount of the transaction. Positive for purchases, negative for refunds. For example: $10.00 ."
    )
    
    currency: Optional[str] = Field(
        default=None,
        description="The currency of the transaction amount. For example: USD, EUR. Default to USD if unclear"
    )
    
    transaction_type: Optional[Transaction] = Field(
        default=Transaction.UNKNOWN,
        description="The type of transaction. One of: purchase, refund, fee, transfer, unknown, subscription. Default to unknown if unclear."
    )
    
    plain_english_explanation: Optional[str] = Field(
        default=None,
        description="A plain English explanation of the transaction. For example: 'Purchased coffee at Starbucks.'"
    )
    
    confidence: Confidence = Field(
        default=Confidence.MEDIUM,
        description="The confidence level of the translation. One of: high, medium, low. Default to medium."
    )