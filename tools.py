import json
from datetime import datetime


NOW = datetime.fromisoformat("2026-06-10T09:00:00+02:00")

tools = [
    {
        "type": "function",
        "name": "search_policies",
        "description": "Gets the policies rules",
    },
    {
        "type": "function",
        "name": "get_booking",
        "description": "returns the details of one booking",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "A booking id"
                }
            },
            "required": ["id"]
        }
    },
    {
        "type": "function",
        "name": "calculate_refund",
        "description": "calculates how much a customer gets back if they cancel a booking",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "A booking id"
                }
            },
            "required": ["id"]
        }
    }
]

def search_policies_function() -> str:
    """Gets the policies rules"""
    
    with open("./data/policies/cancellations.md", "r", encoding="utf-8") as cancellation_raw_data:
        cancellation_data = cancellation_raw_data.read()
        
    with open("./data/policies/faq.md", "r", encoding="utf-8") as faq_raw_rata:
            faq_data = faq_raw_rata.read()
            
    with open("./data/policies/prices.md", "r", encoding="utf-8") as prices_raw_data:
            prices_data = prices_raw_data.read()
            
    return json.dumps([cancellation_data, faq_data, prices_data])



def get_booking_function(id: str) -> str:
    with open("./data/bookings.json", "r", encoding="utf-8") as bookings_raw_data:
        bookings_data = json.load(bookings_raw_data)
     
        result = None
        
        for booking in bookings_data:
            if booking["id"] == id:
                result = json.dumps(booking)
        
        if result:
            return result
        else:
            return "booking not found"
        

def calculate_refund_function(id: str) -> str:
    """Returns how much a customer gets back"""
    with open("./data/bookings.json", "r", encoding="utf-8") as bookings_raw_data:
        bookings_data = json.load(bookings_raw_data)
         
        result = None
        
        for booking in bookings_data:
            if booking["id"] == id:
                result = booking
        
        if not result:
            return "booking not found"
        
        if result["status"] != "confirmed":
            return "this booking can't be cancelled"
        
        cost: float = result["rental_price_eur"]
        deposit: float = result["deposit_eur"]
        
        paid_with: str = result["paid_with"]
        
        booking_date = datetime.fromisoformat(result["start"])
        
        hours_before_start = (booking_date - NOW).total_seconds() / 3600
        
        
        refund_rental = 0
      
        if hours_before_start >= 24 and hours_before_start < 48:
            refund_rental = cost / 2
            
        elif hours_before_start >= 48:
            refund_rental = cost
            
        refund_total = refund_rental + deposit
       
        return json.dumps({
            "refund_total_eur": round(refund_total, 1), 
            "rental_refund_eur": round(refund_rental, 1), 
            "deposit_refund_eur": round(deposit, 1),
            "booking_fee_refunded_eur": 0, 
            "refund_method": paid_with
        })



