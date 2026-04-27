from agent_manager import run_agent


def execute_task(prompt, ask_model):
    steps = ask_model(
        f"""
Break into steps (max 3):

{prompt}
"""
    )

    results = []

    for step in steps.split("\n")[:3]:
        if not step.strip():
            continue
        results.append(run_agent(step, ask_model))

    return "\n".join(results)
