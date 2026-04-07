from agents import browser_agent, coder_agent, system_agent


def choose_agent(text, ask_model):
    decision = ask_model(
        f"""
Classify this request into ONE:

- coder
- browser
- system

Text: {text}
"""
    )
    return decision.lower().strip()


def run_agent(text, ask_model):
    agent = choose_agent(text, ask_model)

    if agent == "coder":
        return coder_agent.run(text, ask_model)

    if agent == "browser":
        return browser_agent.run(text, ask_model)

    if agent == "system":
        return system_agent.run(text)

    return ask_model(text)
