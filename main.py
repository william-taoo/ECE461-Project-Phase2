import sys
import os
import logging
from pathlib import Path
from unicodedata import category
from dotenv import load_dotenv

os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['HF_HUB_VERBOSITY'] = 'error'

def format_output(rec: dict) -> str:
    return (
        '{"name":"%s","category":"%s",'
        '"net_score":%.2f,"net_score_latency":%d,'
        '"ramp_up_time":%.2f,"ramp_up_time_latency":%d,'
        '"bus_factor":%.2f,"bus_factor_latency":%d,'
        '"performance_claims":%.2f,"performance_claims_latency":%d,'
        '"license":%.2f,"license_latency":%d,'
        '"size_score":{"raspberry_pi":%.2f,"jetson_nano":%.2f,"desktop_pc":%.2f,"aws_server":%.2f},'
        '"size_score_latency":%d,'
        '"dataset_and_code_score":%.2f,"dataset_and_code_score_latency":%d,'
        '"dataset_quality":%.2f,"dataset_quality_latency":%d,'
        '"code_quality":%.2f,"code_quality_latency":%d}'
    ) % (
        rec["name"],
        rec["category"],

        rec["net_score"],           int(rec["net_score_latency"]),
        rec["ramp_up_time"],        int(rec["ramp_up_time_latency"]),
        rec["bus_factor"],          int(rec["bus_factor_latency"]),
        rec["performance_claims"],  int(rec["performance_claims_latency"]),
        rec["license"],             int(rec["license_latency"]),

        rec["size_score"]["raspberry_pi"],
        rec["size_score"]["jetson_nano"],
        rec["size_score"]["desktop_pc"],
        rec["size_score"]["aws_server"],
        int(rec["size_score_latency"]),

        rec["dataset_and_code_score"],        int(rec["dataset_and_code_score_latency"]),
        rec["dataset_quality"],               int(rec["dataset_quality_latency"]),
        rec["code_quality"],                  int(rec["code_quality_latency"]),
    )


def setup_logging():
    """
    Configures the root logger based on environment variables.

    Reads LOG_LEVEL and LOG_FILE from the environment to set up logging.
    - LOG_LEVEL: 0 for silent (creates a blank log file), 1 for INFO, 2 for DEBUG.
    - LOG_FILE: The path to the log file.
    """
    try:
        log_level_str = os.getenv("LOG_LEVEL", "0")
        log_level = int(log_level_str)
    except (ValueError, TypeError):
        print(f"Warning: Invalid LOG_LEVEL '{log_level_str}'. Defaulting to 0 (silent).", file=sys.stderr)
        log_level = 0

    # Get the root logger and clear any handlers that may have been configured
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # If the log level is 0, create a blank log file and disable logging.
    if log_level == 0:
        logging.getLogger().propagate = False
        logging.getLogger().disabled = True
        logging.disable(logging.CRITICAL)

        log_file = os.getenv("LOG_FILE")
        if log_file and log_file.strip():
            try:
                p = Path(log_file)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("", encoding="utf-8")
            except (IOError, PermissionError) as e:
                print(f"Error: Could not create blank log file '{log_file}'. Please check permissions. Error: {e}", file=sys.stderr)
                sys.exit(1)
        return

    # Determine the actual logging level to set
    if log_level == 1:
        level_to_set = logging.INFO
    elif log_level >= 2:
        level_to_set = logging.DEBUG
    else:
        return

    # Configure the root logger
    root_logger.setLevel(level_to_set)
    log_file = os.getenv("LOG_FILE")

    if log_file and log_file.strip():
        try:
            p = Path(log_file)
            p.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

            logging.getLogger(__name__).info("program_start")
            if level_to_set == logging.DEBUG:
                logging.getLogger(__name__).debug("debug_enabled")

        except (IOError, PermissionError) as e:
            print(f"Error: Could not write to log file '{log_file}'. Please check permissions. Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Warning: LOG_LEVEL is set to '{log_level}', but no LOG_FILE was specified. Logs will not be saved.", file=sys.stderr)



load_dotenv()


setup_logging()



# Import other modules.
from URL_handler import URLHandler
from CLI_parser import read_urls

def main():
    api_key = os.getenv("API_KEY")

    if not api_key:
        print("Warning: API_KEY not set; proceeding without it.", file=sys.stderr)

    if len(sys.argv) != 2:
        print(f"Usage: ./{os.path.basename(__file__)} URL_FILE", file=sys.stderr)
        sys.exit(1)

    url_file_path = sys.argv[1]

    urls = read_urls(Path(url_file_path))

    models = URLHandler.process_urls(urls)

    # Process each model and print its scores
    for model in models:
        name = model.get_name()
        category = model.get_category()

        if category != "MODEL":
            continue

        model.compute_net_score(api_key=api_key)

        output_data = {
            "name": name,
            "category": category,
            "net_score": model.net_score,
            "net_score_latency": int(model.net_score_latency),
            "ramp_up_time": model.ramp_up_time,
            "ramp_up_time_latency": int(model.ramp_up_time_latency),
            "bus_factor": model.bus_factor,
            "bus_factor_latency": int(model.bus_factor_latency),
            "performance_claims": model.performance_claims,
            "performance_claims_latency": int(model.performance_claims_latency),
            "license": model.license_score,
            "license_latency": int(model.license_latency),
            "size_score": model.size_score if model.size_score is not None else {},
            "size_score_latency": int(model.size_score_latency),
            "dataset_and_code_score": model.dataset_and_code_score,
            "dataset_and_code_score_latency": int(model.dataset_and_code_score_latency),
            "dataset_quality": model.dataset.quality,
            "dataset_quality_latency": int(model.dataset_quality_latency),
            "code_quality": model.code.quality,
            "code_quality_latency": int(model.code_quality_latency),
        }

        # Print the final JSON object to stdout
        print(format_output(output_data))
    return 0

if __name__ == "__main__":
    main()
