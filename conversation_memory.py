conversation = []


def add_to_memory(user, assistant):
    conversation.append({"user": user, "assistant": assistant})


def build_prompt(user_input):
    history = ""
    for entry in conversation[-5:]:
        history += f"User: {entry['user']}\nAssistant: {entry['assistant']}\n"
    return history + f"User: {user_input}"
