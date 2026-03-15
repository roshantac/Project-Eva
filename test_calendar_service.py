"""
Test script for calendar service functionality
"""

import asyncio
from datetime import datetime, timedelta
from app.services.calendar_service import CalendarService
from app.engines.tool_engine import ToolEngine


async def test_calendar_service():
    """Test calendar service"""
    print("🧪 Testing Calendar Service\n")
    
    calendar_service = CalendarService()
    user_id = "test_user"
    
    # Test 1: Schedule a meeting
    print("Test 1: Schedule a meeting")
    start_time = datetime.now() + timedelta(hours=2)
    result = await calendar_service.schedule_meeting(
        title="Team Standup",
        start_time=start_time,
        duration_minutes=30,
        user_id=user_id,
        description="Daily team sync",
        location="Conference Room A"
    )
    print(f"✅ {result['message']}\n")
    
    # Test 2: Schedule another meeting
    print("Test 2: Schedule another meeting")
    start_time2 = datetime.now() + timedelta(hours=4)
    result2 = await calendar_service.schedule_meeting(
        title="Client Meeting",
        start_time=start_time2,
        duration_minutes=60,
        user_id=user_id,
        description="Discuss project requirements"
    )
    print(f"✅ {result2['message']}\n")
    
    # Test 3: Get today's calendar
    print("Test 3: Get today's calendar")
    calendar_result = await calendar_service.get_todays_calendar(user_id)
    print(calendar_result['message'])
    print()
    
    # Test 4: Parse time expressions
    print("Test 4: Parse time expressions")
    test_expressions = [
        "tomorrow at 3pm",
        "at 5:30pm",
        "in 2 hours",
        "next Monday at 10am"
    ]
    
    for expr in test_expressions:
        parsed = calendar_service.parse_time_expression(expr)
        if parsed:
            print(f"✅ '{expr}' -> {parsed.strftime('%Y-%m-%d %I:%M %p')}")
        else:
            print(f"❌ Could not parse: '{expr}'")
    print()


async def test_tool_engine():
    """Test tool engine calendar detection"""
    print("\n🧪 Testing Tool Engine Calendar Detection\n")
    
    tool_engine = ToolEngine()
    
    # Test calendar query detection
    test_messages = [
        "Schedule a meeting tomorrow at 3pm",
        "What's on my calendar today?",
        "Show me today's calendar",
        "Book a meeting called Project Review at 5pm",
        "Get today's calendar",
        "Schedule Team Standup tomorrow at 10am for 30 minutes",
        "List all my meetings",
        "Show all scheduled meetings",
        "What meetings do I have scheduled?"
    ]
    
    for message in test_messages:
        action = tool_engine.detect_calendar_query(message)
        if action:
            print(f"✅ '{message}'")
            print(f"   Action: {action}")
            
            data = tool_engine.extract_calendar_data(message, action)
            if data:
                print(f"   Data: {data}")
        else:
            print(f"❌ No calendar action detected: '{message}'")
        print()


async def main():
    """Run all tests"""
    try:
        await test_calendar_service()
        await test_tool_engine()
        print("\n✅ All tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
