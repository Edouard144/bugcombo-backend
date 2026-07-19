import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv('GROQ_API_KEY'))
MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')

def judge_submissions(buggy_code, submission1, submission2, language):
    prompt = f"""Judge two fixes for buggy {language} code. Return ONLY valid JSON.

Bug:
```{language}
{buggy_code}
```

Fix 1:
```{language}
{submission1}
```

Fix 2:
```{language}
{submission2}
```

Score each 0.0-1.0 on: correctness, cleanliness, efficiency, security.
Overall score = average of four criteria.
Pick winner by higher overall score. "tie" if equal.

Return EXACTLY this JSON:
{{"player1":{{"correctness":0.0,"cleanliness":0.0,"efficiency":0.0,"security":0.0,"score":0.0,"feedback":"brief"}},"player2":{{"correctness":0.0,"cleanliness":0.0,"efficiency":0.0,"security":0.0,"score":0.0,"feedback":"brief"}},"winner":"player1" or "player2" or "tie"}}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=512,
    )

    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        content = content.rsplit("```", 1)[0]

    result = json.loads(content)
    return result
