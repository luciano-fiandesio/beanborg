from typing import List, Optional

from openai import OpenAI


class GPTService:
    def __init__(self):
        self.client = OpenAI()

    def query_gpt_for_label(self, description: str, labels: List[str]) -> Optional[str]:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are 'TransactionBud' a helpful and concise utility designed to categorize bank transactions efficiently. Your primary function is to assign a category to each transaction presented to you",
                    },
                    {
                        "role": "user",
                        "content": f"Given the description '{description}', what would be the most appropriate category among the following: {', '.join(labels)}? Only output the category name without any additional text.",
                    },
                ],
                temperature=0.7,
                top_p=1,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Failed to query GPT: {str(e)}")
            return None
