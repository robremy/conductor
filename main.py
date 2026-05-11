LAYERS = [
    "Configuration",
    "Request intake",
    "Planning",
    "Code generation",
    "Test execution",
    "Review",
    "Refinement",
    "Delivery and learning feedback",
]


def get_message():
    return "Conductor is running"


def get_layers():
    return LAYERS


def get_next_improvement(tests_passed=True, review_notes=""):
    if not tests_passed:
        return "Fix failing tests before adding features."
    if review_notes.strip():
        return "Apply review notes in the next refinement."
    return "Record one small lesson for the next request."


def format_completed_request(number, feature_type, request, outcome):
    colors = {
        "Code": "green",
        "Layer": "blue",
    }
    color = colors.get(feature_type, "black")
    label = f'<span style="color: {color};">[{feature_type}]</span>'
    return f"{number}. {label} {request}: {outcome}"


if __name__ == "__main__":
    print(get_message())
