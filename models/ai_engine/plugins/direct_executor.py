import io
import sys
import traceback

def run(raw_code):
    """Execute raw Python exactly as given and capture stdout."""
    output_buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = output_buffer

    try:
        exec_globals = {}
        exec(raw_code, exec_globals)
        sys.stdout = old_stdout
        result = output_buffer.getvalue().strip()
        return result if result else "[Direct execution completed with no printed output]"
    except Exception as e:
        sys.stdout = old_stdout
        tb = traceback.format_exc()
        return f"DIRECT EXECUTION ERROR: {e}\n\n{tb}"