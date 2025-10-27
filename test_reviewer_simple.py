import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from agents.reviewer_agent import ReviewerAgent

class MockDB:
    pass

async def main():
    reviewer = ReviewerAgent(db=MockDB())

    result = await reviewer.review_grant_async({
        'grant_content': {},
        'user_answers': {},
        'research_results': None,
        'citations': None,
        'tables': None,
        'selected_grant': {}
    })

    assert 'review_score' in result
    assert 'final_status' in result
    print(f"PASS: score={result['review_score']}, status={result['final_status']}")

asyncio.run(main())
