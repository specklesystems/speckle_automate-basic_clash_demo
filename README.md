[![build and deploy Speckle functions](https://github.com/specklesystems/speckle_automate-basic_clash_demo/actions/workflows/main.yml/badge.svg)](https://github.com/specklesystems/speckle_automate-basic_clash_demo/actions/workflows/main.yml)

# Speckle Automate Function: Basic Clash Analysis Demo

## Overview
This repository hosts the Basic Clash Analysis Demo for Speckle Automate, tailored for the AEC industry. It demonstrates automated clash detection using complex third-party libraries to analyze elements from both a static reference model and a dynamic model.

## ⚠️ Disclaimer: Conceptual Demonstration Only
**IMPORTANT: This function is a conceptual model and is not intended for actual use in production environments. It serves as a demonstration to illustrate automated clash detection principles in Speckle Automate and the use of third-party libraries for advanced analysis.**

## Functionality
- **Element Type Selection:** Users specify element categories for clash tests.
- **Automated Detection:** Demonstrates real-time clash detection as the dynamic model evolves.
- **Clash Reporting:** Generates reports on detected clashes.
- **Integration Example:** Illustrates potential integration with Speckle's platform and AEC software tools.
- **Notification Simulation:** Simulates automated notifications about clashes.

### How It Works
The function analyzes elements from a static reference model and a dynamic model, identifying potential geometric conflicts when the dynamic model is updated.

### Utilization of Third-Party Libraries
This demo showcases the ability to incorporate complex third-party libraries for detailed analysis, extending the functionality of Speckle Automate beyond its core features. In this case a custom build of PyMesh and its c++ library dependencies are included in the Dockerfile.

### Containerization and Deployment
- **Dockerization:** The included Dockerfile demonstrates how the project can be containerized, emphasizing the ease of deployment in Speckle Automate.
- **Automate Deployment:** Highlights the potential for easy deployment of containerized projects within the Speckle ecosystem.

## Note
This function is designed for educational purposes and is not equipped for real-world AEC projects.

---
## Potential Expansions for the Basic Clash Analysis Demo

This demo serves as a starting point and can be expanded in several ways to enhance its capabilities and usability within Speckle Automate. Below are some ideas for future development:

### Importing Rule Sets from External Sources
- **Dynamic Rule Set Integration:** Enable the function to import clash detection rules from external files or databases, allowing for greater flexibility and customization of clash criteria.
- **API-Based Rule Configuration:** Develop an API endpoint where users can update or modify rule sets dynamically, making the function adaptable to varying project requirements.

### Enhancing User Interaction with External UIs
- **Customizable User Interface:** Implement a user-friendly interface that allows users to interact with the function directly, configure settings, and view clash reports more intuitively.
- **Integration with AEC Tools:** Design interfaces or plugins for popular AEC software tools, enabling users to access and use the clash detection function directly from their preferred design environment.

### Advanced Analysis Features
- **Complex Geometric Analysis:** Expand the function to perform more sophisticated geometric analyses, potentially using advanced algorithms or machine learning models to identify complex clashes.
- **Historical Data Analysis:** Incorporate features to analyze the evolution of clashes over time, providing insights into recurring issues or patterns in the project lifecycle.

### Collaborative Feedback Loops
- **Real-Time Collaboration Tools:** Integrate real-time communication tools within the function, allowing team members to discuss and resolve clashes directly within the Speckle environment.
- **Automated Notification System:** Enhance the notification system to provide more detailed alerts, including clash severity levels and suggested resolutions.

---

**Reminder:** This repository is a conceptual demonstration for automated clash detection and the use of third-party libraries in Speckle Automate.

## Using this Speckle Function
1. **Create a New Speckle Automation**: Set up in the Speckle dashboard.
2. **Configure the Function**: Choose the "Basic Clash Analysis" function.
3. **Run and Review**: Execute the function and review the clash reports.



1. [Register](https://automate.speckle.dev/) your Function with [Speckle Automate](https://automate.speckle.dev/) and select the Python template.
1. A new repository will be created in your GitHub account.
1. Make changes to your Function in `main.py`. See below for the Developer Requirements, and instructions on how to test.
1. To create a new version of your Function, create a new [GitHub release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) in your repository.

## Developer Requirements

1. Install the following:
    - [Python 3](https://www.python.org/downloads/)
    - [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)
1. Run `poetry shell && poetry install` to install the required Python packages.

## Building and Testing

The code can be tested locally by running `poetry run pytest`.

### Building and running the Docker Container Image

Running and testing your code on your own machine is a great way to develop your Function; the following instructions are a bit more in-depth and only required if you are having issues with your Function in GitHub Actions or on Speckle Automate.

#### Building the Docker Container Image

Your code is packaged by the GitHub Action into the format required by Speckle Automate. This is done by building a Docker Image, which is then run by Speckle Automate. You can attempt to build the Docker Image yourself to test the building process locally.

To build the Docker Container Image, you will need to have [Docker](https://docs.docker.com/get-docker/) installed.

Once you have Docker running on your local machine:

1. Open a terminal
1. Navigate to the directory in which you cloned this repository
1. Run the following command:

    ```bash
    docker build -f ./Dockerfile -t speckle_automate_python_example .
    ```

#### Running the Docker Container Image

Once the image has been built by the GitHub Action, it is sent to Speckle Automate. When Speckle Automate runs your Function as part of an Automation, it will run the Docker Container Image. You can test that your Docker Container Image runs correctly by running it locally.

1. To then run the Docker Container Image, run the following command:

    ```bash
    docker run --rm speckle_automate_python_example \
    python -u main.py run \
    '{"projectId": "1234", "modelId": "1234", "branchName": "myBranch", "versionId": "1234", "speckleServerUrl": "https://speckle.xyz", "automationId": "1234", "automationRevisionId": "1234", "automationRunId": "1234", "functionId": "1234", "functionName": "my function", "functionLogo": "base64EncodedPng"}' \
    '{}' \
    yourSpeckleServerAuthenticationToken
    ```

Let's explain this in more detail:

`docker run --rm speckle_automate_python_example` tells Docker to run the Docker Container Image that we built earlier. `speckle_automate_python_example` is the name of the Docker Container Image that we built earlier. The `--rm` flag tells docker to remove the container after it has finished running, this frees up space on your machine.

The line `python -u main.py run` is the command that is run inside the Docker Container Image. The rest of the command is the arguments that are passed to the command. The arguments are:

- `'{"projectId": "1234", "modelId": "1234", "branchName": "myBranch", "versionId": "1234", "speckleServerUrl": "https://speckle.xyz", "automationId": "1234", "automationRevisionId": "1234", "automationRunId": "1234", "functionId": "1234", "functionName": "my function", "functionLogo": "base64EncodedPng"}'` - the metadata that describes the automation and the function.
- `{}` - the input parameters for the function that the Automation creator is able to set. Here they are blank, but you can add your own parameters to test your function.
- `yourSpeckleServerAuthenticationToken` - the authentication token for the Speckle Server that the Automation can connect to. This is required to be able to interact with the Speckle Server, for example to get data from the Model.

## Resources

- [Learn](https://speckle.guide/dev/python.html) more about SpecklePy, and interacting with Speckle from Python.
