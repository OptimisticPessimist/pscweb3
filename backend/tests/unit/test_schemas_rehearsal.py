from datetime import datetime
import pytest
from pydantic import ValidationError
from src.schemas.rehearsal import RehearsalCreate

def test_rehearsal_create_valid_deadline():
    """Valid deadline (00 or 30 mins) should be accepted."""
    valid_data = {
        "date": datetime(2025, 12, 13, 10, 0),
        "duration_minutes": 120,
        "attendance_deadline": datetime(2025, 12, 12, 10, 0)
    }
    rehearsal = RehearsalCreate(**valid_data)
    assert rehearsal.attendance_deadline == datetime(2025, 12, 12, 10, 0)

    valid_data_30 = {
        "date": datetime(2025, 12, 13, 10, 0),
        "duration_minutes": 120,
        "attendance_deadline": datetime(2025, 12, 12, 10, 30)
    }
    rehearsal_30 = RehearsalCreate(**valid_data_30)
    assert rehearsal_30.attendance_deadline == datetime(2025, 12, 12, 10, 30)

def test_rehearsal_create_invalid_deadline():
    """Invalid deadline (not 00 or 30 mins) should raise ValidationError."""
    invalid_data = {
        "date": datetime(2025, 12, 13, 10, 0),
        "duration_minutes": 120,
        "attendance_deadline": datetime(2025, 12, 12, 10, 15)
    }
    with pytest.raises(ValidationError) as exc:
        RehearsalCreate(**invalid_data)
    
    assert "Attendance deadline must be in 30-minute intervals" in str(exc.value)

def test_rehearsal_create_no_deadline():
    """No deadline should be accepted (logic handles it later)."""
    data = {
        "date": datetime(2025, 12, 13, 10, 0),
        "duration_minutes": 120,
        "attendance_deadline": None
    }
    rehearsal = RehearsalCreate(**data)
    assert rehearsal.attendance_deadline is None
