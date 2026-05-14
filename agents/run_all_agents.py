from agents.log_classifier.main import main as run_log_classifier
from agents.selector_healer.main import main as run_selector_healer


if __name__ == "__main__":
    run_log_classifier()
    print("-" * 60)
    run_selector_healer()
