import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import json
import sys
import socket
import requests
from requests.exceptions import RequestException
import platform
import subprocess

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from central_setup.central_setup import (
    run_single_test,
    get_github_token,
    get_github_username_and_slug,
    run_program,
    check_internet_connection,
    execute_logic,
)


class TestRunSingleTest(unittest.TestCase):
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"tests": [{"name": "test1", "points": 10}]}',
    )
    def test_run_single_test_online(self, mock_file):
        # Mock pre_test_setup function
        pre_test_setup = MagicMock()
        pre_test_setup.return_value = (
            {"test1": "output"},
            {"test1": 10},
            "feedback",
            {"test": "data"},
        )

        # Mock check_internet_connection to return True
        with patch(
            "central_setup.central_setup.check_internet_connection", return_value=True
        ):
            # Should not raise an assertion error
            run_single_test("test1", "test1", "expected feedback", pre_test_setup)

            # Verify pre_test_setup was called correctly
            pre_test_setup.assert_called_once_with(test_name="test1")

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"tests": [{"name": "test1", "points": 10}]}',
    )
    def test_run_single_test_offline(self, mock_file):
        # Mock pre_test_setup function
        pre_test_setup = MagicMock()
        pre_test_setup.return_value = ({"test1": "expected feedback"}, {}, "", {})

        # Mock check_internet_connection to return False
        with patch(
            "central_setup.central_setup.check_internet_connection", return_value=False
        ):
            # Should not raise an assertion error
            run_single_test("test1", "test1", "expected feedback", pre_test_setup)

            # Verify pre_test_setup was called correctly
            pre_test_setup.assert_called_once_with(test_name="test1")

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"tests": [{"name": "test1", "points": 10}]}',
    )
    def test_run_single_test_fail_points(self, mock_file):
        # Mock pre_test_setup function
        pre_test_setup = MagicMock()
        pre_test_setup.return_value = (
            {"test1": "output"},
            {"test1": 5},  # incorrect points
            "feedback",
            {"test": "data"},
        )

        # Mock check_internet_connection to return True
        with patch(
            "central_setup.central_setup.check_internet_connection", return_value=True
        ):
            # Should raise an assertion error
            with self.assertRaises(AssertionError):
                run_single_test("test1", "test1", "expected feedback", pre_test_setup)


class TestGetGithubToken(unittest.TestCase):
    @patch("platform.system", return_value="Linux")
    @patch("os.getenv", return_value="mock-token")
    def test_get_github_token_linux(self, mock_getenv, mock_system):
        token = get_github_token()
        self.assertEqual(token, "mock-token")
        mock_getenv.assert_called_once_with("GITHUB_TOKEN")

    @patch("platform.system", return_value="Windows")
    def test_get_github_token_windows(self, mock_system):
        # Skip this test if win32cred isn't available (like on macOS)
        try:
            import win32cred

            # Only run the test if win32cred is available
            with patch(
                "win32cred.CredRead", return_value={"CredentialBlob": b"mock-token"}
            ):
                token = get_github_token()
                self.assertEqual(token, "mock-token")
        except ImportError:
            # Skip test if we can't import win32cred
            self.skipTest("win32cred module not available on this platform")

    @patch("platform.system", return_value="Windows")
    def test_get_github_token_windows_exception(self, mock_system):
        # Mock exception in win32cred
        with patch.dict("sys.modules", {"win32cred": MagicMock()}):
            with patch("win32cred.CredRead", side_effect=Exception("Error")):
                with patch("builtins.print") as mock_print:
                    token = get_github_token()
                    self.assertIsNone(token)
                    mock_print.assert_called_once()

    @patch("platform.system", return_value="Darwin")
    @patch("subprocess.run")
    def test_get_github_token_darwin_success(self, mock_run, mock_system):
        # Create a mock response for the subprocess
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.stderr = 'password: "mock-token"'
        mock_run.return_value = process_mock

        token = get_github_token()
        self.assertEqual(token, "mock-token")

    @patch("platform.system", return_value="Darwin")
    @patch("subprocess.run", side_effect=Exception("Error"))
    def test_get_github_token_darwin_exception(self, mock_run, mock_system):
        with patch("builtins.print") as mock_print:
            token = get_github_token()
            self.assertIsNone(token)
            mock_print.assert_called_once()

    @patch("platform.system", return_value="Unknown")
    def test_get_github_token_unknown_os(self, mock_system):
        with patch("builtins.print") as mock_print:
            token = get_github_token()
            self.assertIsNone(token)
            mock_print.assert_called_once()


class TestGetGithubUsernameAndSlug(unittest.TestCase):
    @patch("requests.get")
    @patch("os.path.basename", return_value="assignment-username")
    def test_get_github_username_and_slug_success(
        self, mock_basename, mock_requests_get
    ):
        # Mock successful GitHub API response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"login": "username"}
        mock_requests_get.return_value = mock_response

        username, slug = get_github_username_and_slug("mock-token")

        self.assertEqual(username, "username")
        self.assertEqual(slug, "assignment")
        mock_requests_get.assert_called_once_with(
            "https://api.github.com/user", headers={"Authorization": "token mock-token"}
        )

    @patch("requests.get")
    def test_get_github_username_and_slug_api_failure(self, mock_requests_get):
        # Mock failed GitHub API response
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.reason = "Unauthorized"
        mock_requests_get.return_value = mock_response

        with patch("builtins.print") as mock_print:
            username, slug = get_github_username_and_slug("mock-token")

            self.assertIsNone(username)
            self.assertIsNone(slug)
            mock_print.assert_called_once()

    @patch("requests.get", side_effect=RequestException("Connection error"))
    def test_get_github_username_and_slug_request_exception(self, mock_requests_get):
        with patch("builtins.print") as mock_print:
            username, slug = get_github_username_and_slug("mock-token")

            self.assertIsNone(username)
            self.assertIsNone(slug)
            mock_print.assert_called_once()

    @patch("requests.get")
    @patch("os.path.basename", return_value="assignment-username")
    def test_get_github_username_no_token(self, mock_basename, mock_requests_get):
        username, slug = get_github_username_and_slug(None)

        self.assertIsNone(username)
        self.assertIsNone(slug)
        mock_requests_get.assert_not_called()

    @patch("requests.get")
    @patch("os.path.basename", return_value="invalid-directory-name")
    def test_get_github_username_and_slug_invalid_directory(
        self, mock_basename, mock_requests_get
    ):
        # Mock successful GitHub API response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"login": "username"}
        mock_requests_get.return_value = mock_response

        # The implementation returns (None, None) when the username can't be found in the directory name
        # Let's mock the implementation to match the actual behavior
        with patch("builtins.print") as mock_print:
            # This test is checking that when the directory name doesn't contain the username,
            # the function correctly returns None, None and prints a message
            username, slug = get_github_username_and_slug("mock-token")

            # Check that username and slug are both None
            self.assertIsNone(username)
            self.assertIsNone(slug)
            # Verify that print was called to notify about the inability to detect slug
            mock_print.assert_called_once()


class TestRunProgram(unittest.TestCase):
    @patch("subprocess.run")
    def test_run_program_success(self, mock_run):
        # Mock successful process
        process_mock = MagicMock()
        process_mock.stdout = "Program output"
        mock_run.return_value = process_mock

        output = run_program(["input1", "input2"], "program.py")

        self.assertEqual(output, "Program output")
        mock_run.assert_called_once_with(
            ["python3", "program.py"],
            input="input1\ninput2\n",
            text=True,
            capture_output=True,
            check=True,
        )

    @patch(
        "subprocess.run",
        side_effect=subprocess.CalledProcessError(1, [], stderr="Error message"),
    )
    def test_run_program_subprocess_error(self, mock_run):
        output = run_program(["input"], "program.py")

        self.assertEqual(output, "Error: Error message")

    @patch("subprocess.run", side_effect=Exception("Unexpected error"))
    def test_run_program_unexpected_error(self, mock_run):
        output = run_program(["input"], "program.py")

        self.assertEqual(output, "Unexpected error: Unexpected error")


class TestCheckInternetConnection(unittest.TestCase):
    @patch("socket.create_connection")
    def test_check_internet_connection_success(self, mock_connect):
        # Mock successful connection
        mock_connect.return_value = MagicMock()

        result = check_internet_connection()

        self.assertTrue(result)
        mock_connect.assert_called_once_with(("8.8.8.8", 53), timeout=5)

    @patch("socket.create_connection", side_effect=OSError("Network error"))
    def test_check_internet_connection_failure(self, mock_connect):
        result = check_internet_connection()

        self.assertFalse(result)
        mock_connect.assert_called_once_with(("8.8.8.8", 53), timeout=5)


class TestExecuteLogic(unittest.TestCase):
    @patch("central_setup.central_setup.get_github_token", return_value="mock-token")
    @patch(
        "central_setup.central_setup.get_github_username_and_slug",
        return_value=("username", "slug"),
    )
    @patch("central_setup.central_setup.check_internet_connection", return_value=True)
    @patch("requests.post")
    def test_execute_logic_with_env_var(
        self, mock_post, mock_check_internet, mock_get_username, mock_get_token
    ):
        # Mock response for post request
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "tests": [{"name": "test1", "pointsAwarded": 10, "feedback": "Good job"}],
            "totalPointsAwarded": 10,
            "totalPointsPossible": 10,
            "specificCodeFeedback": {
                "code": [{"feedback": "Good code", "recommendation": "Keep it up"}],
                "general": "Overall good work",
            },
        }
        mock_post.return_value = mock_response

        # Set environment variable for testing
        test_url = "https://test-url.com/api"
        with patch.dict(os.environ, {"AUTOGRADING_BASE_URL": test_url}):
            test_outputs, test_points, test_feedback, response_data = execute_logic(
                "test1",
                {"test1": "output"},
                "student code",
                "pytest code",
                {"tests": [{"name": "test1", "run": "/test1.py", "points": 10}]},
            )

            # Verify URL was taken from environment variable
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(
                args[0], test_url
            )  # First positional arg should be the URL

            # Verify other function calls and results
            mock_get_token.assert_called_once()
            mock_get_username.assert_called_once_with("mock-token")

            # Check if the output data matches expectations
            self.assertEqual(test_points, {"test1": 10})
            self.assertIn("Test Name: test1", test_feedback)
            self.assertIn("Points Awarded: 10", test_feedback)

    @patch("central_setup.central_setup.get_github_token", return_value="mock-token")
    @patch(
        "central_setup.central_setup.get_github_username_and_slug",
        return_value=("username", "slug"),
    )
    @patch("central_setup.central_setup.check_internet_connection", return_value=True)
    @patch("requests.post")
    def test_execute_logic_default_url(
        self, mock_post, mock_check_internet, mock_get_username, mock_get_token
    ):
        # Mock response for post request
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "tests": [{"name": "test1", "pointsAwarded": 10, "feedback": "Good job"}],
            "totalPointsAwarded": 10,
            "totalPointsPossible": 10,
            "specificCodeFeedback": {
                "code": [{"feedback": "Good code", "recommendation": "Keep it up"}],
                "general": "Overall good work",
            },
        }
        mock_post.return_value = mock_response

        # Directly patch os.environ.get to ensure proper default value behavior
        with patch("os.environ.get") as mock_get_env:
            # Configure the mock to return the default value when called with the right args
            mock_get_env.return_value = (
                "https://autograding-api-next.vercel.app/api/autograde"
            )

            test_outputs, test_points, test_feedback, response_data = execute_logic(
                "test1",
                {"test1": "output"},
                "student code",
                "pytest code",
                {"tests": [{"name": "test1", "run": "/test1.py", "points": 10}]},
            )

            # Verify the environment variable was accessed correctly
            mock_get_env.assert_called_with(
                "AUTOGRADING_BASE_URL",
                "https://autograding-api-next.vercel.app/api/autograde",
            )

            # Verify URL used in the request
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(
                args[0], "https://autograding-api-next.vercel.app/api/autograde"
            )

    @patch("central_setup.central_setup.get_github_token", return_value="mock-token")
    @patch(
        "central_setup.central_setup.get_github_username_and_slug",
        return_value=("username", "slug"),
    )
    @patch("central_setup.central_setup.check_internet_connection", return_value=False)
    @patch("requests.post")
    def test_execute_logic_no_internet(
        self, mock_post, mock_check_internet, mock_get_username, mock_get_token
    ):
        # Mock response for post request
        mock_response = MagicMock()
        mock_response.json.return_value = {"tests": []}
        mock_post.return_value = mock_response

        # The execute_logic function prints two messages: the test name and the no internet message
        # We need to capture both and verify them
        with patch("builtins.print") as mock_print:
            test_outputs, test_points, test_feedback, response_data = execute_logic(
                "test1",
                {"test1": "output"},
                "student code",
                "pytest code",
                {"tests": [{"name": "test1", "run": "/test1.py", "points": 10}]},
            )

            # Verify feedback contains the right message for no internet
            self.assertEqual(test_feedback, "")
            # Verify the second call contains the no internet message
            mock_print.assert_any_call(
                "No active internet connection or API response. Run the test again with an active internet connection and a working API to receive more user-friendly feedback."
            )

    @patch("central_setup.central_setup.get_github_token", return_value=None)
    @patch(
        "central_setup.central_setup.get_github_username_and_slug",
        return_value=(None, None),
    )
    @patch("central_setup.central_setup.check_internet_connection", return_value=True)
    @patch("requests.post")
    def test_execute_logic_no_token(
        self, mock_post, mock_check_internet, mock_get_username, mock_get_token
    ):
        # Mock response for post request
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "tests": [{"name": "test1", "pointsAwarded": 10, "feedback": "Good job"}],
            "totalPointsAwarded": 10,
            "totalPointsPossible": 10,
            "specificCodeFeedback": {
                "code": [{"feedback": "Good code", "recommendation": "Keep it up"}],
                "general": "Overall good work",
            },
        }
        mock_post.return_value = mock_response

        test_outputs, test_points, test_feedback, response_data = execute_logic(
            "test1",
            {"test1": "output"},
            "student code",
            "pytest code",
            {"tests": [{"name": "test1", "run": "/test1.py", "points": 10}]},
        )

        # Verify headers don't contain Authorization when token is None
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"], {})

    @patch("central_setup.central_setup.get_github_token", return_value="mock-token")
    @patch(
        "central_setup.central_setup.get_github_username_and_slug",
        return_value=("username", "slug"),
    )
    @patch("central_setup.central_setup.check_internet_connection", return_value=True)
    @patch("requests.post")
    def test_execute_logic_request_exception(
        self, mock_post, mock_check_internet, mock_get_username, mock_get_token
    ):
        # Mock response for post request raising an exception
        mock_post.side_effect = requests.exceptions.RequestException(
            "Connection failed"
        )

        with self.assertRaises(requests.exceptions.RequestException):
            execute_logic(
                "test1",
                {"test1": "output"},
                "student code",
                "pytest code",
                {"tests": [{"name": "test1", "run": "/test1.py", "points": 10}]},
            )


if __name__ == "__main__":
    unittest.main()
