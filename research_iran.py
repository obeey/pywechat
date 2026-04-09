import asyncio
import os
from browser_use import Agent
from langchain_openai import ChatOpenAI

async def main():
    # Configure the LLM to drive the browser
    llm = ChatOpenAI(
        base_url="https://vllm.codingstack.xyz:61721/v1",
        api_key="e6uIhWd+HVJSOYaN",
        model="gemma4"
    )

    # Define the task
    task = "Search for the current status of the Iran war and its history/background. Provide a comprehensive summary including key events, current situation, and the root causes. Save the final report as clear text."

    # Initialize the agent
    # Note: browser-use configuration for headed mode and profile is typically done via the BrowserConfig
    from browser_use import Browser, BrowserConfig
    
    browser = Browser(
        config=BrowserConfig(
            headless=False,  # Headed mode
            chrome_instance_path=None, # If specific profile path is needed, it would go here, but browser-use often uses a default profile or user_data_dir
        )
    )

    agent = Agent(
        task=task,
        llm=llm,
        browser=browser
    )

    print("Starting web research on Iran war...")
    history = await agent.run()
    
    # Extract the final result from the history
    # browser-use agents usually return the final result in the last step
    result = history.final_result()
    
    if result:
        with open("iran_war_report.txt", "w", encoding="utf-8") as f:
            f.write(result)
        print("Research completed and saved to iran_war_report.txt")
    else:
        print("Research failed to produce a result.")

    await browser.close()

if __name__ == "__main__":
    asyncio.run(main())