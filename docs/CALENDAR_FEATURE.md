# Calendar Feature Documentation

## Overview

The calendar feature allows users to schedule meetings and view their calendar through text or audio prompts. The system intelligently detects calendar-related queries and executes the appropriate actions.

## Features

### 1. Schedule Meetings
Schedule meetings with natural language commands:
- **Text/Audio**: "Schedule a meeting tomorrow at 3pm"
- **Text/Audio**: "Book a meeting called Project Review at 5pm"
- **Text/Audio**: "Schedule Team Standup tomorrow at 10am for 30 minutes"

### 2. View Today's Calendar
Get a formatted view of all events scheduled for today:
- **Text/Audio**: "What's on my calendar today?"
- **Text/Audio**: "Show me today's calendar"
- **Text/Audio**: "Get today's calendar"
- **Text/Audio**: "What do I have scheduled today?"

### 3. List All Scheduled Meetings
View all your scheduled meetings (today and upcoming):
- **Text/Audio**: "List all my meetings"
- **Text/Audio**: "Show all scheduled meetings"
- **Text/Audio**: "What meetings do I have scheduled?"
- **Text/Audio**: "List my meetings"
- **Text/Audio**: "Show my meetings"

### 4. Meeting Details
When scheduling, you can specify:
- **Title**: Meeting name
- **Time**: When it starts (natural language)
- **Duration**: How long it lasts (default: 60 minutes)
- **Location**: Where it takes place (optional)
- **Description**: What it's about (optional)

## Natural Language Time Expressions

The system understands various time formats:
- "tomorrow at 3pm"
- "at 5:30pm" (today or tomorrow if time has passed)
- "in 2 hours"
- "next Monday at 10am"

## Example Conversations

### Scheduling a Meeting

**User (Text/Audio)**: "Schedule a meeting called Team Standup tomorrow at 10am for 30 minutes"

**Eva**: "✅ Meeting 'Team Standup' scheduled for 2026-03-16 at 10:00 AM"

### Viewing Today's Calendar

**User (Text/Audio)**: "What's on my calendar today?"

**Eva**:
```
📅 Your calendar for today (Sunday, March 15, 2026):

You have 2 event(s) scheduled:

1. Team Standup
   ⏰ 05:32 PM - 06:02 PM
   📍 Conference Room A
   📝 Daily team sync

2. Client Meeting
   ⏰ 07:32 PM - 08:32 PM
   📝 Discuss project requirements
```

### Listing All Meetings

**User (Text/Audio)**: "List all my meetings"

**Eva**:
```
📅 Your Scheduled Meetings (5 total):

📆 Today:
  • Team Standup
    ⏰ 05:32 PM - 06:02 PM
    📍 Conference Room A
    📝 Daily team sync

  • Client Meeting
    ⏰ 07:32 PM - 08:32 PM
    📝 Discuss project requirements

📆 Tomorrow:
  • Project Review
    ⏰ 03:00 PM - 04:00 PM
    📝 Quarterly review meeting

📆 Monday, March 17, 2026:
  • Weekly Planning
    ⏰ 10:00 AM - 11:00 AM
    📍 Main Office
```

## Technical Details

### Files Created/Modified

1. **app/services/calendar_service.py** - Core calendar service
   - `schedule_meeting()` - Schedule new events
   - `get_todays_calendar()` - Retrieve today's events
   - `cancel_event()` - Cancel scheduled events
   - `parse_time_expression()` - Parse natural language times

2. **app/engines/tool_engine.py** - Tool detection and execution
   - `detect_calendar_query()` - Detect calendar-related queries
   - `extract_calendar_data()` - Extract meeting details from text
   - `_handle_schedule_meeting()` - Handle scheduling requests
   - `_handle_get_todays_calendar()` - Handle calendar view requests

3. **data/calendar.json** - Persistent storage for calendar events

### Tool Definitions

#### schedule_meeting
- **Parameters**: title, time_expression, duration_minutes, description, location, user_id
- **Returns**: Scheduled event details with confirmation message

#### get_todays_calendar
- **Parameters**: user_id
- **Returns**: Formatted list of today's events with times and details

#### list_all_meetings
- **Parameters**: user_id
- **Returns**: Formatted list of all scheduled meetings (today and upcoming), grouped by date

#### cancel_meeting
- **Parameters**: event_id, user_id
- **Returns**: Cancellation confirmation

## Data Storage

Calendar events are stored in `data/calendar.json` with the following structure:

```json
{
  "event_1234567890": {
    "id": "event_1234567890",
    "title": "Team Standup",
    "description": "Daily team sync",
    "start_time": "2026-03-16T10:00:00",
    "end_time": "2026-03-16T10:30:00",
    "duration_minutes": 30,
    "location": "Conference Room A",
    "attendees": [],
    "created_at": "2026-03-15T15:32:18",
    "user_id": "user123",
    "status": "scheduled",
    "has_conflicts": false,
    "conflicts": []
  }
}
```

## Conflict Detection

The system automatically detects scheduling conflicts:
- Checks if new meeting overlaps with existing events
- Warns user about conflicts but still allows scheduling
- Displays conflict information in the response

## Voice Integration

Both scheduling and viewing calendar work seamlessly with:
- **Voice Input**: Speak your request naturally
- **Voice Output**: Eva reads back the calendar or confirmation
- **Text Alternative**: Type commands if preferred

## Testing

Run the test suite:
```bash
python test_calendar_service.py
```

This tests:
- Meeting scheduling
- Calendar retrieval
- Time expression parsing
- Query detection
- Data extraction

## Future Enhancements

Potential improvements:
- Recurring meetings
- Meeting invitations/attendees
- Calendar sync with external services (Google Calendar, Outlook)
- Meeting reminders (already supported via reminder service)
- Edit existing meetings
- Weekly/monthly calendar views
- Meeting notes and attachments

## Dependencies

All required dependencies are already in `requirements.txt`:
- `python-dateutil==2.8.2` - For parsing natural language dates
- `apscheduler==3.11.2` - For scheduling (used by reminder service)

