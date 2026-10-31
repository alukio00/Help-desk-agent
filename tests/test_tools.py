import pytest
from tools import search_policies_function, calculate_refund_function, get_booking_function
import json



@pytest.fixture
def project_data(tmp_path, monkeypatch):
    """Creates temporary data instead of using a real data."""

    monkeypatch.chdir(tmp_path)

    policies_dir = tmp_path / "data" / "policies"
    policies_dir.mkdir(parents=True)

    (policies_dir / "cancellations.md").write_text(
        "Cancellation policy",
        encoding="utf-8",
    )
    (policies_dir / "faq.md").write_text(
        "Frequently asked questions",
        encoding="utf-8",
    )
    (policies_dir / "prices.md").write_text(
        "Rental prices",
        encoding="utf-8",
    )

    bookings = [
        {
            "id": "CW-1",
            "status": "confirmed",
            "bike_type": "city",
            "bikes": 1,
            "start": "2026-06-14T10:00:00+02:00",
            "end": "2026-06-16T10:00:00+02:00",
            "add_ons": [],
            "rental_price_eur": 100.0,
            "booking_fee_eur": 2.0,
            "deposit_eur": 20.0,
            "paid_with": "card"
        }
        
    ]

    (tmp_path / "data" / "bookings.json").write_text(
        json.dumps(bookings),
        encoding="utf-8",
    )

    return tmp_path


# Search policies test 


def test_search_policies_function(project_data):
    result = search_policies_function()

    documents = json.loads(result)

    assert documents == [
        "Cancellation policy",
        "Frequently asked questions",
        "Rental prices",
    ]
   
   
# Get booking tests
 
    
def test_get_booking_returns_found(project_data):
    result = get_booking_function("CW-1")

    booking = json.loads(result)

    assert booking["id"] == "CW-1"
    assert booking["status"] == "confirmed"
    assert booking["bike_type"] == "city"
    assert booking["bikes"] == 1
    assert booking["start"] == "2026-06-14T10:00:00+02:00"
    assert booking["end"] == "2026-06-16T10:00:00+02:00"
    assert booking["add_ons"] == []
    assert booking["rental_price_eur"] == 100.0
    assert booking["booking_fee_eur"] == 2.0
    assert booking["deposit_eur"] == 20.0
    assert booking["paid_with"] == "card"


def test_get_booking_returns_not_found(project_data):
    result = get_booking_function("UNKNOWN")

    assert result == "booking not found"
    

# Refund tests 


def test_refund_booking_not_found(project_data):
    assert calculate_refund_function("UNKNOWN") == "booking not found"


def test_refund_unconfirmed_booking(project_data):

    path = project_data / "data" / "bookings.json"
    bookings = json.loads(path.read_text(encoding="utf-8"))

    bookings[0]["status"] = "cancelled"
    path.write_text(json.dumps(bookings), encoding="utf-8")
    assert calculate_refund_function("CW-1") == "this booking can't be cancelled"
    
    bookings[0]["status"] = "in_progress"
    path.write_text(json.dumps(bookings), encoding="utf-8")
    assert calculate_refund_function("CW-1") == "this booking can't be cancelled"
    
    bookings[0]["status"] = "completed"
    path.write_text(json.dumps(bookings), encoding="utf-8")
    assert calculate_refund_function("CW-1") == "this booking can't be cancelled"
    


@pytest.mark.parametrize(
    "start, paid_with, expected",
    [
        # Less than 24h: refund only deposit
        ("2026-06-11T08:00:00+02:00", "card", {
            "refund_total_eur": 20.0, 
            "rental_refund_eur": 0, 
            "deposit_refund_eur": 20.0,
            "booking_fee_refunded_eur": 0, 
            "refund_method": "card"
        }),

        # Exactly 24h: counts as 24-48h, 50% price and deposit
        ("2026-06-11T09:00:00+02:00", "card", {
            "refund_total_eur": 70.0, 
            "rental_refund_eur": 50.0, 
            "deposit_refund_eur": 20.0,
            "booking_fee_refunded_eur": 0, 
            "refund_method": "card"
        }),

        # Exactly 48h: counts as > 48h, 100% price and deposit
        ("2026-06-12T09:00:00+02:00", "voucher", {
            "refund_total_eur": 120.0, 
            "rental_refund_eur": 100.0, 
            "deposit_refund_eur": 20.0,
            "booking_fee_refunded_eur": 0, 
            "refund_method": "voucher"
        }),
    ],
)
def test_calculate_refund_rules(
    project_data,
    start,
    paid_with,
    expected,
):
    path = project_data / "data" / "bookings.json"
    bookings = json.loads(path.read_text(encoding="utf-8"))

    bookings[0]["start"] = start
    bookings[0]["paid_with"] = paid_with

    path.write_text(json.dumps(bookings), encoding="utf-8")

    result = json.loads(calculate_refund_function("CW-1"))

    assert result["refund_total_eur"] == expected["refund_total_eur"]
    assert result["deposit_refund_eur"] == expected["deposit_refund_eur"]
    assert result["rental_refund_eur"] == expected["rental_refund_eur"]