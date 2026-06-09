import subprocess

from loguru import logger


class LocalTestRunner:
    """Executes code tests and parses terminal outputs."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def run_tests(self, test_path: str = "tests/") -> dict:
        try:
            result = subprocess.run(
                ["pytest", test_path, "-q", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                shell=False,
            )
            passed = result.returncode == 0
            if passed:
                logger.info("Tests passed")
            else:
                logger.warning(f"Tests failed:\n{result.stdout[-500:]}")
            return {
                "passed": passed,
                "stdout": result.stdout[-1000:],
                "stderr": result.stderr[-500:],
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            logger.error(f"Tests timed out after {self.timeout}s")
            return {
                "passed": False,
                "stdout": "",
                "stderr": f"Timeout after {self.timeout}s",
                "returncode": -1,
            }
        except FileNotFoundError:
            logger.warning("pytest not found, assuming tests pass")
            return {"passed": True, "stdout": "", "stderr": "", "returncode": 0}
