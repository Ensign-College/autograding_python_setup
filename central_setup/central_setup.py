import subprocess
import requests
import json
import socket
import os
import platform

def run_single_test(test_name, test_point_key, offline_feedback, pre_test_setup):
    test_outputs, test_points_awarded, test_feedback, test_response_data = pre_test_setup(test_name=test_name)
    output = test_outputs[test_name]
    
    # Load points from autograding.json
    with open('.github/classroom/autograding.json', 'r') as f:
        autograding_config = json.load(f)
    
    # Find the points for the specific test
    test_config = next((test for test in autograding_config["tests"] if test["name"] == test_point_key), None)
    expected_points = test_config["points"] if test_config else 0
    
    if check_internet_connection():
        assert test_points_awarded.get(test_point_key, 0) == expected_points, test_feedback
    else:
        assert offline_feedback in output.strip(), offline_feedback

def get_github_token():
    """Retrieve the GitHub token based on the operating system."""
    system = platform.system()
    if system == "Linux":
        return os.getenv('GITHUB_TOKEN')
    elif system == "Windows":
        try:
            import win32cred
            creds = win32cred.CredRead("git:https://github.com", win32cred.CRED_TYPE_GENERIC)
            return creds['CredentialBlob'].decode()
        except Exception as e:
            print(f"GitHub token not detected: {e}")
            return None
    elif system == "Darwin":
        try:
            cmd = ['security', 'find-internet-password', '-s', 'github.com', '-g']
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stderr.splitlines()
                for line in lines:
                    if line.startswith('password:'):
                        return line.split('"')[1]
        except Exception as e:
            print(f"GitHub token not detected: {e}")
        return None
    else:
        print(f"Unsupported operating system: {system}")
        return None


def check_repo_access(github_token, repository_name):
    """Check if the user has access to the repository."""
    try:
        response = requests.get(
            f'https://api.github.com/repos/{github_token}/{repository_name}',
            headers={
                'Authorization': f"token {github_token}",
                'Accept': 'application/vnd.github.v3+json'
            },
            timeout=10
        )
        print(f"Checking repository access for {repository_name}...")
        return response.status_code == 200, response.json() if response.ok else None
    except requests.exceptions.RequestException as e:
        print(f"Error checking repository access: {e}")
        return False, None
    except Exception as e:
        print(f"Unexpected error checking repository access: {e}")
        return False, None

def run_program(inputs,program_name):
    """Run the student's program using subprocess and return the output."""
    # Convert the inputs into a single string, each input followed by a newline
    input_data = '\n'.join(inputs) + '\n'

    try:
        # Run the student's program and capture output
        result = subprocess.run(
            ['python3', program_name],  # Adjust this command if using a different Python version or path
            input=input_data,
            text=True,
            capture_output=True,
            check=True  # If check is True and the exit code was non-zero, it raises a
                        # CalledProcessError. The CalledProcessError object will have the return code
                        # in the returncode attribute, and output & stderr attributes if those streams
                        # were captured.
        )
        return result.stdout  # Capture standard output
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"  # Return the error message from stderr
    except Exception as e:
        return f"Unexpected error: {str(e)}"  # Handle any other exceptions
    
    

def check_internet_connection():
    """Check if there is an active internet connection."""
    try:
        # Try to connect to a known server (Google's public DNS server)
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False

def execute_logic(test_name, test_outputs, student_code, pytest_code, autograding_config):
    github_token = get_github_token()
    headers = {"Authorization": f"Bearer {github_token}"} if github_token else {}

    repository_name = None
    if github_token:
        # Try to get repository name from git config if available
        try:
            result = subprocess.run(['git', 'config', '--get', 'remote.origin.url'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                remote_url = result.stdout.strip()
                # Extract repository name from git URL
                if 'github.com' in remote_url:
                    repository_name = remote_url.split('/')[-1].replace('.git', '')
        except Exception:
            pass

    if test_name:
        print(f"Running test: {test_name}")
        # Filter the autograding config to include only the relevant section
        relevant_tests = [test for test in autograding_config["tests"] if f"/{test_name}.py" in test["run"]]
        autograding_config["tests"] = relevant_tests

    # Prepare the data for the POST request
    data = {
        "studentCode": student_code,
        "pytestCode": pytest_code,
        "autogradingConfig": json.dumps(autograding_config),
        "terminalOutputs": list(test_outputs.values()),
        "repositoryName": repository_name,
    }

    # Send the POST request
    response = requests.post(
        'https://autograding-api-next.vercel.app/api/autograde', 
        json=data, 
        headers=headers
    )
    response.raise_for_status()  # Raise an exception for HTTP errors

    # Parse the response
    test_response_data = response.json()

    # Store the points awarded for each test
    test_points_awarded = {test['name']: test['pointsAwarded'] for test in test_response_data["tests"]}
    test_feedback = ""
    if check_internet_connection() and test_response_data:
        # Get feedback for the relevant test
        relevant_feedback = test_response_data["tests"]
        if relevant_feedback:
            test_feedback = (
                "\nTest Results:\n"
                + "\n".join(
                    [
                        f"Test Name: {test['name']}\nPoints Awarded: {test['pointsAwarded']}\nFeedback: {test['feedback']}\n"
                        for test in relevant_feedback
                    ]
                )
                + f"\nTotal Points Awarded: {test_response_data['totalPointsAwarded']}\n"
                + f"Total Points Possible: {test_response_data['totalPointsPossible']}\n"
                + "\nSpecific Code Feedback:\n"
                + "\n".join(
                [
                    f"{feedback['feedback']}\nRecommendation: {feedback['recommendation']}\n"
                    for feedback in test_response_data["specificCodeFeedback"]["code"]
                ]                )
                + "\nGeneral Feedback:\n"
                + test_response_data["specificCodeFeedback"]["general"]
            )

    else:
        print("No active internet connection or API response. Run the test again with an active internet connection and a working API to receive more user-friendly feedback.")


    return test_outputs, test_points_awarded, test_feedback, test_response_data