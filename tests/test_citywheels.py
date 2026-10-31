
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import citywheels


def make_function_call(name, arguments=None):
    """Simulate a Gemini response containing a function call."""
    step = SimpleNamespace(
        type="function_call",
        name=name,
        arguments=arguments or {},
        id="call_123",
    )

    return SimpleNamespace(
        steps=[step],
        id="interaction_123",
        output_text="",
        status="requires_action"
    )


def make_client(tool_name, arguments=None):
    """Create a mocked Gemini client with two predefined responses."""
    client = MagicMock()

    first_response = make_function_call(tool_name, arguments)
    final_response = SimpleNamespace(
        output_text="Response for the customer",
        status=""
    )

    # Return the function call first, followed by the final response.
    client.interactions.create.side_effect = [
        first_response,
        final_response,
    ]

    return client


def test_search_policies_is_called():
    """Verify that the policy search function is called."""
    client = make_client("search_policies")

    with patch("citywheels.search_policies_function", return_value="Opening hours: 9 AM–5 PM") as mock_search:
        result = citywheels.handle_message(
            "What are your opening hours?",
            client,
        )

    mock_search.assert_called_once_with()

    assert result == "Response for the customer", "Check that the final response is returned."
    assert client.interactions.create.call_count == 2, "Check that Gemini was called twice."


def test_get_booking_receives_booking_id():
    """Verify that the booking function receives the correct booking ID."""
    
    client = make_client("get_booking", {"booking_id": "CW123"})

    with patch("citywheels.get_booking_function", return_value="Booking CW123") as mock_booking:
        result = citywheels.handle_message(
            "Check booking CW123",
            client,
        )

    mock_booking.assert_called_once_with(booking_id="CW123")

  
    assert result == "Response for the customer", "Check that the final response is returned."


def test_calculate_refund_is_called():
    """Verify that the refund calculation function is called."""
    
    client = make_client("calculate_refund", {"booking_id": "CW123"})

    with patch("citywheels.calculate_refund_function", return_value="Refund: 50 PLN") as mock_refund:
        result = citywheels.handle_message(
            "How much will I get refunded?",
            client,
        )

    mock_refund.assert_called_once_with(booking_id="CW123")

    assert result == "Response for the customer", "Check that the final response is returned."


def test_no_function_call_returns_text():
    """Verify that text is returned when Gemini does not call a tool."""
    client = MagicMock()

    client.interactions.create.return_value = SimpleNamespace(
        steps=[],
        output_text="I cannot help with this request.",
        status=""
    )

    result = citywheels.handle_message(
        "Hello",
        client,
    )
    
    assert result == "I cannot help with this request.", "Verify that the text response is returned directly."
    assert client.interactions.create.call_count == 1, "Verify that Gemini was called only once."


def test_unknown_tool_raises_error():
    """Verify that an unknown tool raises a ValueError."""
    client = make_client("unknown_tool")

    # Check that the expected exception is raised.
    with pytest.raises(ValueError, match="Unknown tool"):
        citywheels.handle_message("Test", client)

    assert client.interactions.create.call_count == 1, "Verify that no second API call was made."
